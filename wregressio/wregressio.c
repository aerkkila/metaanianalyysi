#include <nctietue2.h>
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#define HAVE_INLINE
#include <gsl/gsl_multifit.h>
#include <gsl/gsl_fit.h>
#include <gsl/gsl_statistics.h>
#include <math.h>
#include <stdint.h>
#include <stdarg.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>

/* Bootstrap-käyrän piirtäjä ei toimi oikein, jos osa yritetetyistä raja-arvoista on ollut toimimattomia. */

const char* wetlnimet_0[]    = {"wetland", "bog", "fen", "marsh"};
const char* wetlandnimi_0    = "wetland";
const char* wetlnimet_1[]    = {"wetland", "permafrost_bog", "tundra_wetland"};
const char* wetlandnimi_1    = "wetland_prf";
const char *wetlandnimi, **wetlnimet;
int wpit;
const char* kaudet[]         = {"whole_year", "summer", "freezing", "winter"};
enum                           {whole_year_e, summer_e, freezing_e, winter_e};
const char* menetelmät[]     = {"keskiarvo", "huippuarvo", "kaikki"};
enum			       {keskiarvo_e, huippuarvo_e, kaikki_e};
const char* pripost_sisään[] = {"flux_bio_prior", "flux_bio_posterior"};
const char* pripost_ulos[]   = {"pri", "post"};

#define ARRPIT(a) (sizeof(a)/sizeof(*(a)))
#define vapauta(fun, ptr) do { fun(ptr); ptr=NULL; } while(0)
#define korosta do { if(tty) printf("\033[1;93m"); } while(0)
#define perusväri do { if(tty) printf("\033[0m"); } while(0)
int tty;

#define SUHT2ABS_KERR 6371229.0*6371229.0 * 0.017453293 * 1 // r2 * ASTE * hila
#define ncdir "../"

#ifndef menetelmä
#define menetelmä keskiarvo_e // kaikki_e ja huipparvo_e eivät käsittele vuorajaa oikein
#endif
#define BOOTSTRAP
char aprintapu[256];
char* aprintf(const char* muoto, ...) {
    va_list args;
    va_start(args, muoto);
    vsprintf(aprintapu, muoto, args);
    va_end(args);
    return aprintapu;
}

const int nboot_vakio = 150;

typedef struct data_t data_t;

void poista_alusta(data_t*, int);
void järjestä_vuon_mukaan(data_t*, double*);

struct data_t {
    double *vuo;
    double *wdata[8]; // luku on tarkoituksella tarvittavaa suurempi
    double virtaama; // emissio / s
    int resol;
    int aikaa;
    int pit;
    double *alat;
};

int kausi=1, tallenna=0, ikir=0, töitä=1;
char *python_arg = "";
struct Sidonta { char* arg; int lue; void* var; char* muoto; } ohjelm_arg[] = {
    {"-p", 1, &python_arg,     },
    {"-s", 0, &tallenna,       },
    {"-k", 1, &kausi,      "%i"},
    {"-i", 0, &ikir,           },
    {"-j", 1, &töitä,      "%i"},
};
void argumentit(int argc, char** argv) {
    int pit = ARRPIT(ohjelm_arg);
    for(int i=1; i<argc; i++)
	for(int j=0; j<pit; j++) {
	    if(strcmp(ohjelm_arg[j].arg, argv[i])) continue;
	    if(!ohjelm_arg[j].lue)
		*((int*)ohjelm_arg[j].var) = 1;
	    else
		for(int k=0; k<ohjelm_arg[j].lue; k++) {
		    assert(i+1 < argc);
		    if(ohjelm_arg[j].muoto)
			sscanf(argv[++i], ohjelm_arg[j].muoto, ohjelm_arg[j].var+k*4); // jos on monta, koon pitää olla 4
		    else
			*((char**)ohjelm_arg[j].var) = argv[++i];
		}
	    break;
	}
    /* Globaalit asiat, jotka ovat seurausta argumenteista. */
    if(ikir) {
	wpit = ARRPIT(wetlnimet_1);
	wetlnimet = wetlnimet_1;
	wetlandnimi = wetlandnimi_1;
    }
    else {
	wpit = ARRPIT(wetlnimet_0);
	wetlnimet = wetlnimet_0;
	wetlandnimi = wetlandnimi_0;
    }
    if(tallenna) {
	stdout = freopen(aprintf("tallenteet/%s_%i.txt", kaudet[kausi], ikir), "w", stdout);
	printf("# %s\n", aprintapu);
	assert(stdout);
	tty = 0;
    }
}

double laske_virtaama_(const data_t* dt, double *kertoimet, int alku, int loppu) {
    double v = 0;
    double vuot[wpit];
    for(int i=1; i<wpit; i++)
	vuot[i] = (kertoimet[i] + kertoimet[0]) * 1e-9;
    for(int i=alku; i<loppu; i++)
	for(int w=1; w<wpit; w++)
	    v += vuot[w] * dt->wdata[w][i] * dt->alat[i] * dt->wdata[0][i];
    v *= SUHT2ABS_KERR;
    return v;
}

double laske_virtaama(const data_t* dt, double *kertoimet) {
    return laske_virtaama_(dt, kertoimet, 0, dt->pit);
}

double summa(double* dt, int n) {
    double s = 0;
    for(int i=0; i<n; i++) s += dt[i];
    return s;
}

int luo_data_kaikki(const data_t* dt, data_t* dt1, char* kausic, double wraja, double vuoraja) {
    char r_ei_kelpaa[dt->resol];
    memset(r_ei_kelpaa, 2, dt->resol);
    dt1->pit = dt1->virtaama = 0;
    for(int t=0; t<dt->aikaa; t+=3) {
	int tdt = t*dt->resol;
	for(int r=0; r<dt->resol; r++) {
	    if(!kausic[r] || dt->wdata[0][r] < wraja) continue;

	    if(r_ei_kelpaa[r] == 2) {
		double summa=0;
		for(int i=1; i<wpit; i++)
		    summa += dt->wdata[i][r] / dt->wdata[0][r];
		r_ei_kelpaa[r] = summa < 0.97;
	    }

	    if(r_ei_kelpaa[r]) continue;
	    if(kausic[tdt+r] != kausi && kausi != whole_year_e) continue;
	    double yrite = dt->vuo[tdt+r] / dt->wdata[0][r] * 1e9;
	    if(yrite > vuoraja) continue;
	    dt1->vuo[dt1->pit]  = yrite;
	    dt1->virtaama       += dt->vuo[tdt+r] * dt->alat[r];
	    dt1->alat[dt1->pit] = dt->alat[r];
	    dt1->wdata[0][dt1->pit] = dt->wdata[0][r];
	    for(int i=1; i<wpit; i++)
		dt1->wdata[i][dt1->pit] = dt->wdata[i][r] / dt->wdata[0][r];
	    dt1->wdata[0][dt1->pit] = dt->wdata[0][r];
	    dt1->pit++;
	}
    }
    dt1->virtaama *= SUHT2ABS_KERR;
    return 0;
}

int luo_data(const data_t* dt, data_t* dt1, char* kausic, double wraja, double vuoraja) {
    dt1->pit = dt1->virtaama = 0;
    if(menetelmä == kaikki_e) return luo_data_kaikki(dt, dt1, kausic, wraja, vuoraja);
    /* Tässä on nyt keskitytty saamaan keskiarvomenetelmä oikein ja huippuarvoa ei ole tarkoituksena käyttää.
       Vuorajan toteuttaminen huippuarvomenetelmässä on jätetty puolitiehen. */
    int poistettuja = 0;
    double *virtaamat = malloc(dt->resol*sizeof(double)); // kerätään ensin tähän ja lasketaan yhteen vasta lopussa,
    //                                                       koska vasta lopussa tiedetään, montako pienintä jätetään ottamatta
    for(int r=0; r<dt->resol; r++) {
	if(!kausic[r]) continue;
	if(dt->wdata[0][r] < wraja) continue;
	double summa=0;
	for(int i=1; i<wpit; i++)
	    summa += dt->wdata[i][r] / dt->wdata[0][r];
	if(summa < 0.97) continue;

	switch(menetelmä) {
	case keskiarvo_e:
	    summa = 0;
	    double ala = 0;
	    int  aikaa=0;
	    if(kausi==whole_year_e) {
		for(int t=0; t<dt->aikaa; t++) {
		    summa += dt->vuo[t*dt->resol + r] * dt->alat[r];
		    ala   += dt->alat[r];
		    aikaa++; }
	    }
	    else
		for(int t=0; t<dt->aikaa; t++)
		    if(kausic[t*dt->resol + r] == kausi) {
			summa += dt->vuo[t*dt->resol + r] * dt->alat[r];
			ala   += dt->alat[r];
			aikaa++; }

	    if(ala==0) continue;
	    double yrite = summa / ala / dt->wdata[0][r] * 1e9;
	    if(yrite >= vuoraja) { poistettuja++; continue; }
	    dt1->vuo[dt1->pit] = yrite;
	    virtaamat[dt1->pit] = summa / aikaa;
	    break;

	case huippuarvo_e: // muuttujan nimi on hämäävästi summa
	    summa = -INFINITY;
	    int argmax = -1;
	    if(kausi==whole_year_e)
		for(int t=0; t<dt->aikaa; t++) {
		    double yrite = dt->vuo[t*dt->resol+r] / dt->wdata[0][r] * 1e9;
		    if(summa < yrite && vuoraja >= yrite) {
			argmax = t*dt->resol+r;
			summa = yrite;
		    }
		}
	    else
		for(int t=0; t<dt->aikaa; t++) {
		    if(kausic[t*dt->resol+r] != kausi) continue;
		    double yrite = dt->vuo[t*dt->resol+r] / dt->wdata[0][r] * 1e9;
		    if(summa < yrite && vuoraja >= yrite) {
			argmax = t*dt->resol+r;
			summa = yrite;
		    }
		}
	    if(summa==-INFINITY) continue;
	    dt1->vuo[dt1->pit] = summa;
	    dt1->virtaama      += dt->vuo[argmax] * dt->alat[argmax % dt->resol];
	    break;

	default:
	    asm("int $3");
	}

	dt1->alat[dt1->pit] = dt->alat[r];
	for(int i=1; i<wpit; i++)
	    dt1->wdata[i][dt1->pit] = dt->wdata[i][r] / dt->wdata[0][r];
	dt1->wdata[0][dt1->pit] = dt->wdata[0][r];
	dt1->pit++;
    }
    /* Tässä lopussa vasta jätetään pois yhtä monta pienintä arvoa kuin suuria arvoja on jätetty. */
    if(dt1->pit - poistettuja < 20) return 1;
    if(poistettuja) {
	järjestä_vuon_mukaan(dt1, virtaamat);
	poista_alusta(dt1, poistettuja);
    }
    dt1->virtaama = summa(virtaamat+poistettuja, dt1->pit-poistettuja);
    dt1->virtaama *= SUHT2ABS_KERR;
    free(virtaamat);
    return 0;
}

typedef struct {
    const data_t* dt;
    double* kertoimet;
    int nboot, plus;
} Arg;
int arg_luettu = 0;

#define joo_alusta_kaikki_jutut						\
    int nmuutt = wpit;          					\
    gsl_matrix *xmatrix = gsl_matrix_alloc(dt->pit, nmuutt);		\
    gsl_vector *yvec = gsl_vector_alloc(dt->pit);			\
    gsl_vector *wvec = gsl_vector_alloc(dt->pit);			\
    gsl_vector *cvec = gsl_vector_alloc(nmuutt);			\
    gsl_multifit_linear_workspace *work = gsl_multifit_linear_alloc(dt->pit, nmuutt); \
    gsl_matrix *covm = gsl_matrix_alloc(nmuutt, nmuutt);		\
    double sum2

#define joo_vapauta_kaikki_jutut		\
    gsl_multifit_linear_free(work);		\
    gsl_matrix_free(xmatrix);			\
    gsl_vector_free(yvec);			\
    gsl_vector_free(wvec);			\
    gsl_vector_free(cvec);			\
    gsl_matrix_free(covm)

void* sovita_monta_säie(void* varg) {
    Arg* arg = varg;
    const data_t* dt=arg->dt; double* kertoimet=arg->kertoimet; int nboot=arg->nboot, plus=arg->plus;
    arg_luettu = 1;

    joo_alusta_kaikki_jutut;

    /* rand() lukitsee aina tilan, joten rinnakkaislaskenta ei nopeuta, jos rand()-funktiota käytetään.
       Lisäksi tulokset vaihtelisivat riippuen eri säikeitten nopeuksista.
       rand48_r-funktioitten pitäisi toimia hyvin. */
    static int siemen = 1;
    struct drand48_data randbuff;
    srand48_r(++siemen, &randbuff);

    for(int nb=0; nb<nboot; nb++) {
	for(size_t i=0; i<dt->pit; i++) {
	    long ind;
	    lrand48_r(&randbuff, &ind);
	    ind %= dt->pit;
	    gsl_vector_set(yvec, i, dt->vuo[ind]);
	    gsl_vector_set(wvec, i, dt->alat[ind]);
	    gsl_matrix_set(xmatrix, i, 0, 1); // vakiotermi
	    for(int j=1; j<nmuutt; j++)
		gsl_matrix_set(xmatrix, i, j, dt->wdata[j][ind]);
	}
	gsl_multifit_wlinear(xmatrix, wvec, yvec, cvec, covm, &sum2, work);
	/* Tallennetaan vain haluttu lopullinen arvo. Alussa nmuutt kpl on varattuja. */
	for(int i=0; i<nmuutt-1; i++)
	    kertoimet[i+nmuutt+(nb+plus)*(nmuutt-1)] = cvec->data[i+1] + cvec->data[0];
    }

    joo_vapauta_kaikki_jutut;

    return NULL;
}

void sovita_monta(const data_t* dt, double* kertoimet, double* r2, int nboot) {
    pthread_t säikeet[töitä-1];
    int nboot1 = nboot/töitä, plus=0;
    for(int i=0; i<töitä-1; i++) {
	Arg arg = {dt, kertoimet, nboot1, plus};
	arg_luettu = 0;
	pthread_create(säikeet+i, NULL, sovita_monta_säie, &arg);
	while(!arg_luettu) usleep(10);
	arg_luettu = 0;
	plus += nboot1;
    }
    Arg arg = {dt, kertoimet, nboot-(töitä-1)*nboot1, plus};
    sovita_monta_säie(&arg);
    for(int i=0; i<töitä-1; i++)
	pthread_join(säikeet[i], NULL);

    joo_alusta_kaikki_jutut;

    for(size_t i=0; i<dt->pit; i++) {
	gsl_vector_set(yvec, i, dt->vuo[i]);
	gsl_vector_set(wvec, i, dt->alat[i]);
	gsl_matrix_set(xmatrix, i, 0, 1); // vakiotermi
	for(int j=1; j<nmuutt; j++)
	    gsl_matrix_set(xmatrix, i, j, dt->wdata[j][i]);
    }
    gsl_multifit_wlinear(xmatrix, wvec, yvec, cvec, covm, &sum2, work);
    *r2 = 1 - (sum2 / gsl_stats_wtss(wvec->data, 1, yvec->data, 1, dt->pit));
    for(int i=0; i<nmuutt; i++)
	kertoimet[i] = cvec->data[i];

    joo_vapauta_kaikki_jutut;
}

double ristivalidoi(const data_t* dt, int määrä) {
    if(määrä >= dt->pit) return NAN;
    joo_alusta_kaikki_jutut;

    /* Olisi parempi siirtää tämä funktio ulkopuolelle ja antaa vektorit argumenttina tietueena. */
    void kopioi_vektoreihin(int b1, int b2) {
	int ind=0;
	int alku=0, loppu=b1;
	yvec->size = wvec->size = xmatrix->size1 = dt->pit - (b2-b1);
	for(int iii=0; iii<2; iii++) {
	    for(int i=alku; i<loppu; i++, ind++) {
		gsl_vector_set(yvec, ind, dt->vuo[i]);
		gsl_vector_set(wvec, ind, dt->alat[i]);
		gsl_matrix_set(xmatrix, ind, 0, 1); // vakiotermi
		for(int j=0; j<nmuutt; j++)
		    gsl_matrix_set(xmatrix, ind, j, dt->wdata[j][i]);
	    }
	    alku = b2;
	    loppu = dt->pit;
	}
	assert(ind == yvec->size);
    }

    int pit=dt->pit/määrä;
    int väli1=0, väli2 = pit;
    double virtaama = 0;
    for(int i=0; i<määrä-1; i++) {
	kopioi_vektoreihin(väli1, väli2);
	gsl_multifit_wlinear(xmatrix, wvec, yvec, cvec, covm, &sum2, work);
	virtaama += laske_virtaama_(dt, cvec->data, väli1, väli2);
	väli1 = väli2;
	väli2 += pit;
    }
    väli2 = dt->pit;
    kopioi_vektoreihin(väli1, väli2);
    gsl_multifit_wlinear(xmatrix, wvec, yvec, cvec, covm, &sum2, work);
    virtaama += laske_virtaama_(dt, cvec->data, väli1, väli2);

    joo_vapauta_kaikki_jutut;
    return virtaama;
}

void sovittaminen_kerralla(data_t* dt, double kertoimet[]) {
    double r2;
    sovita_monta(dt, kertoimet, &r2, 0);
    printf("r² = %.4lf\n", r2);
    for(int i=0; i<wpit; i++)
	printf("%-12.4lf", kertoimet[i]);
    putchar('\n');
    for(int i=1; i<wpit; i++)
	printf("%-12.4lf", kertoimet[i]+kertoimet[0]);
    putchar('\n');
}

void sovita_1(data_t* dt, int num, double* vakio, double* kulma, double* r2) {
    double sum2, cov00, cov01, cov11;
    gsl_fit_wlinear(dt->wdata[num], 1, dt->alat, 1, dt->vuo, 1, dt->pit, vakio, kulma, &cov00, &cov01, &cov11, &sum2);
    *r2 = 1 - (sum2 / gsl_stats_wtss(dt->alat, 1, dt->vuo, 1, dt->pit));
}

void sovittaminen_erikseen(data_t* dt) {
    double vakio[wpit], kulma[wpit], r2;
    for(int i=1; i<wpit; i++) {
	sovita_1(dt, i, vakio+i, kulma+i, &r2);
	printf("vakio = %7.4lf\tkulma = %8.4lf\tyksi = %.4lf\tr² = %.5lf (%s)\n",
	       vakio[i], kulma[i], vakio[i]+kulma[i], r2, wetlnimet[i]);
    }
    double alat[wpit];
    memset(alat, 0, wpit*sizeof(double));
    double summa = 0, ala = 0;
    for(int i=1; i<wpit; i++) {
	for(int r=0; r<dt->pit; r++)
	    alat[i] += dt->alat[r]*dt->wdata[i][r];
	summa += alat[i] * (vakio[i]+kulma[i]);
	ala += alat[i];
    }
    printf("keskiarvo = %.5lf\n", summa/ala);
}

int hae_alku(nct_var* v, struct tm* aika) {
    nct_anyd t = nct_mktime0(v, NULL);
    assert(t.d == nct_days);
    return (mktime(aika) - t.a.t) / 86400;
}

#define hila 1
#define ASTE 0.017453293
void luo_suhteellinen_pintaala(data_t* dt, nct_vset* vuovs) {
    dt->alat = malloc(dt->resol*sizeof(double));
    int d1 = nct_get_varlen(nct_get_var(vuovs, "lon"));
    double *lat = nct_load_var_with(nct_get_var(vuovs, "lat"), -1, nc_get_var_double, sizeof(double))->data;
    int ind=0;
    do {
	double ala = sin(((double)lat[ind/d1]+hila*0.5) * ASTE) - sin(((double)lat[ind/d1]-hila*0.5) * ASTE);
	for(int i=0; i<d1; i++)
	    dt->alat[ind++] = ala;
    } while(ind < dt->resol);
}

void alusta_dt1(data_t* dt) {
    int rt = dt->resol*(menetelmä==kaikki_e ? dt->aikaa : 1);
    dt->vuo = malloc(rt*sizeof(double));
    dt->alat = malloc(rt*sizeof(double));
    for(int i=0; i<wpit; i++)
	dt->wdata[i] = malloc(rt*sizeof(double));
}

void vapauta_dt1(data_t* dt) {
    free(dt->vuo);
    free(dt->alat);
    for(int i=0; i<wpit; free(dt->wdata[i++]));
}

#define vaihda(a,b) { apu=a; a=b; b=apu; }
void sekoita(data_t* dt) {
    double apu;
    for(int i=0; i<dt->pit; i++) {
	int ind = rand() % (dt->pit-i);
	vaihda(dt->alat[i], dt->alat[i+ind]);
	vaihda(dt->vuo[i], dt->vuo[i+ind]);
	for(int j=0; j<wpit; j++)
	    vaihda(dt->wdata[j][i], dt->wdata[j][i+ind]);
    }
}
#undef vaihda

void poista_alusta(data_t* dt, int n) { // Tämä ei pienennä varatun muistin kokoa.
    dt->pit -= n;
    memmove(dt->vuo, dt->vuo+n, dt->pit*sizeof(double));
    for(int i=0; i<wpit; i++)
	memmove(dt->wdata[i], dt->wdata[i]+n, dt->pit*sizeof(double));
    memmove(dt->alat, dt->alat+n, dt->pit*sizeof(double));
}

/* Nojoo. Tämä on nyt tämmönen. En pitänyt tarpeellisena käyttää aikaa lomituslajittelun optimointiin. */
void _lomlaj2(double* d, double* d_apu, int* integ, int* integ_apu, unsigned pit) {
    if(pit <= 1) return;
    unsigned jako = pit/2;
    _lomlaj2(d, d_apu, integ, integ_apu, jako);
    _lomlaj2(d+jako, d_apu+jako, integ+jako, integ_apu+jako, pit-jako);
    double *d1=d, *d2=d+jako;
    int *i1=integ, *i2=integ+jako;
    int pit1 = jako, pit2 = pit-jako, ind=0;
    while(pit1 && pit2) {
	if(*d1<*d2) {
	    d_apu[ind] = *d1++;
	    integ_apu[ind] = *i1++;
	    pit1--;
	}
	else {
	    d_apu[ind] = *d2++;
	    integ_apu[ind] = *i2++;
	    pit2--;
	}
	ind++;
    }
    if(pit1) {
	memcpy(d_apu+ind, d1, pit1*sizeof(double));
	memcpy(integ_apu+ind, i1, pit1*sizeof(int));
    }
    else {
	memcpy(d_apu+ind, d2, pit2*sizeof(double));
	memcpy(integ_apu+ind, i2, pit2*sizeof(int));
    }
    memcpy(d, d_apu, pit*sizeof(double));
    memcpy(integ, integ_apu, pit*sizeof(int));
}

void lomituslajittele2(double* a, int* b, int pit) {
    double *apu = malloc(pit*sizeof(double));
    int *iapu = malloc(pit*sizeof(int));
    _lomlaj2(a, apu, b, iapu, pit);
    free(iapu);
    free(apu);
}

void järjestä_d(double *d, int *j, int pit) {
    double *apu = malloc(pit*sizeof(double));
    memcpy(apu, d, pit*sizeof(double));
    for(int i=0; i<pit; i++)
	d[i] = apu[j[i]];
    free(apu);
}

void järjestä_vuon_mukaan(data_t* dt, double* d2) {
    int *järj = malloc(dt->pit*sizeof(int));
    for(int i=0; i<dt->pit; i++) järj[i] = i;
    lomituslajittele2(dt->vuo, järj, dt->pit);
    for(int i=0; i<wpit; i++)
	järjestä_d(dt->wdata[i], järj, dt->pit);
    järjestä_d(dt->alat, järj, dt->pit);
    järjestä_d(d2, järj, dt->pit);
    free(järj);
}

double maksimi(const data_t* dt) {
    double max = -INFINITY;
    for(int i=0; i<dt->pit; i++)
	if(dt->vuo[i] > max)
	    max = dt->vuo[i];
    return max;
}

int vertaa_double(const void* a, const void* b) {
    double d = *(double*)a - *(double*)b;
    return d<0? -1: d==0? 0: 1;
}

int main(int argc, char** argv) {
    nct_vset wetlset = {0};
    nct_var *var = NULL;
    int ppnum = 1;
    data_t dt;
    tty = isatty(STDOUT_FILENO);
    argumentit(argc, argv);

    struct tm tm0 = {.tm_year=2012-1900, .tm_mon=8-1, .tm_mday=15};
    struct tm tm1 = tm0;
    tm1.tm_year = 2020-1900;
    dt.aikaa = (mktime(&tm1) - mktime(&tm0)) / 86400;

    nct_read_ncfile_gd(&wetlset, ncdir "BAWLD1x1.nc");
    for(int i=0; i<wpit; i++) {
	assert((var = nct_get_var(&wetlset, wetlnimet[i])));
	dt.wdata[i] = var->data;
    }

    dt.resol = nct_get_varlen(var);

    nct_vset *vuovs = nct_read_ncfile_info(ncdir "flux1x1.nc");
    int alku = hae_alku(nct_get_var(vuovs, "time"), &tm0);
    dt.vuo = nct_load_var_with(nct_get_var(vuovs, pripost_sisään[ppnum]), -1, nc_get_var_double, sizeof(double))->data;
    assert((intptr_t)dt.vuo >= 0x800);
    dt.vuo += alku*dt.resol;

    luo_suhteellinen_pintaala(&dt, vuovs);

    nct_vset* vvv = nct_read_ncfile_info(ncdir "kaudet2.nc");
    var = nct_load_var(nct_next_truevar(vvv->vars[0], 0), -1);
    alku = hae_alku(nct_get_var(vvv, "time"), &tm0);
    char* kausic = var->data + alku*dt.resol;

    FILE* f = NULL;
    int pit = wpit;

// #ifndef BOOTSTRAP
    data_t dt1 = dt;
    alusta_dt1(&dt1);
    const double vuorajat[] = {NAN, 100, 90, 80, 70, 60, 50, 40, 30, 20, 11};
    int rajapit = ARRPIT(vuorajat);
    double paras_d = INFINITY;
    int paras_i = -1;
    /* Haetaan ristivalidoinnilla suurin piirtein paras vuoraja käyttäen ennalta määritettyjä yritteitä */
    for(int i=0; i<rajapit; i++) {
	if(luo_data(&dt, &dt1, kausic, 0.05, vuorajat[i]))
	    break;
	sekoita(&dt1);
	double v = ristivalidoi(&dt1, 30);
	if(v!=v) break; // syöte oli liian lyhyt
	double yrite = v / dt1.virtaama;
	yrite = yrite<1? 1-yrite: yrite-1;
	if(yrite < paras_d) {
	    paras_i = i;
	    paras_d = yrite;
	    korosta;
	}
	if(tallenna) continue;
	printf("%.0lf\t%.0lf\t%.0lf\t%.2lf\n", vuorajat[i], v, dt1.virtaama, yrite);
	perusväri;
    }
    if(!tallenna) putchar('\n');

    /* Tarkennetaan vuorajaa tarkemmalla ristivalidoinnilla. */
    paras_d = INFINITY;
    double paras_raja = NAN;
    double __attribute__((unused)) alaraja = NAN;
    for(double d=-8; d<=8; d+=1) {
	double raja = vuorajat[paras_i]+d;
	if(luo_data(&dt, &dt1, kausic, 0.05, raja))
	    continue;
	double _alaraja = dt1.vuo[0];
	sekoita(&dt1);
	double v = ristivalidoi(&dt1, 250); // Tarkempi ristivalidointi kuin edellä
	if(v!=v) continue;
	double yrite = (v-dt1.virtaama)/dt1.virtaama;
	if(yrite < 0) yrite=-yrite;
	if(yrite < paras_d) {
	    paras_raja = raja;
	    alaraja = _alaraja;
	    paras_d = yrite;
	    korosta;
	}
	if(tallenna) continue;
	printf("%.0lf\t%.0lf\t%.0lf\t%.3lf\n", raja, v, dt1.virtaama, yrite);
	perusväri;
	if(raja - paras_raja > 3) break;
    }

#ifndef BOOTSTRAP // piirretään tulokset
    double vuorajat1[] = {NAN, paras_raja};
    for(int i=0; i<2; i++) {
	if(luo_data(&dt, &dt1, kausic, 0.05, vuorajat1[i]))
	    continue;
	if(!f)
	    assert((f = popen(aprintf("./piirrä.py %s", python_arg), "w")));
	assert(fwrite(&dt1.pit, 4, 1, f) == 1);
	assert(fwrite(dt1.wdata[0], 8, dt1.pit, f) == dt1.pit);
	assert(fwrite(dt1.vuo,      8, dt1.pit, f) == dt1.pit);
	if(i==0) {
	    fprintf(f, "%s\n%s\n", wetlandnimi, kaudet[kausi]);
	    assert(fwrite(dt1.wdata[0], 8, dt1.pit, f) == dt1.pit);
	    assert(fwrite(&paras_raja, 8, 1, f) == 1);
	    assert(fwrite(&alaraja, 8, 1, f) == 1);
	}
	else
	    for(int i=1; i<pit; i++) {
		fprintf(f, "%s\n%s\n", wetlnimet[i], kaudet[kausi]);
		assert(fwrite(dt1.wdata[i], 8, dt1.pit, f) == dt1.pit);
		assert(fwrite(vuorajat1, 8, 1, f) == 1); // NAN
		assert(fwrite(vuorajat1, 8, 1, f) == 1); // NAN
	    }
	vapauta(pclose, f);
    }

#else // #ifdef BOOTSTRAP
    /* Kertoimet-muuttujassa on alussa vakiotermi ja kertoimet.
       Sitten jokaisesta bootstrap-sovituksesta tulos eli vakio+kerroin[i]. */
    double kertoimet[pit*(nboot_vakio+2)]; // tässä on tarkoituksella vähän ylimääräistä
    double r2;

    // #include "poistettu_piirrä_bootstrap.h" // Käytöstä poistettu koodin pätkä on tuolla.

    assert(!luo_data(&dt, &dt1, kausic, 0.05, paras_raja));
    sovita_monta(&dt1, kertoimet, &r2, nboot_vakio);
    printf("raja: %.3lf\n", paras_raja);
    printf("sovite:");
    for(int i=0; i<pit; i++)
	printf(" %-9.3lf", kertoimet[i]);
    putchar('\n');
    assert((f = popen(aprintf("./piirrä.py sovitteet %s", python_arg), "w")));
    assert(fwrite(&dt1.pit, 4, 1, f) == 1);
    assert(fwrite(dt1.wdata[0], 8, dt1.pit, f) == dt1.pit);
    assert(fwrite(dt1.vuo,      8, dt1.pit, f) == dt1.pit);
    fwrite(kertoimet+0, 8, 1, f);
    for(int i=1; i<pit; i++) {
	qsort(kertoimet+pit+i-1, nboot_vakio, 8*(pit-1), vertaa_double); // pit-1 eri kerrointa on aina peräkkäin
	double matala = gsl_stats_quantile_from_sorted_data(kertoimet+pit+i-1, pit-1, nboot_vakio, 0.05);
	double korkea = gsl_stats_quantile_from_sorted_data(kertoimet+pit+i-1, pit-1, nboot_vakio, 0.95);
	fprintf(f, "%s\n%s\n", wetlnimet[i], kaudet[kausi]);
	assert(fwrite(dt1.wdata[i], 8, dt1.pit, f) == dt1.pit);
	fwrite(kertoimet+i, 8, 1, f);
	printf("%-15s %-8.3lf %-8.3lf %.3lf\n", wetlnimet[i], kertoimet[i]+kertoimet[0], matala, korkea);
    }
    vapauta(pclose, f);

#endif
    if(f)
	vapauta(pclose, f);

    vapauta_dt1(&dt1);
    nct_free_vset(vvv);
    nct_free_vset(&wetlset);
    nct_free_vset(vuovs);
    free(dt.alat);
    fclose(stdout); // voi olla vaihdettu tiedostoksi
}

#if 0
'''#';
#endif
/* Tämä tiedosto on pätevää lähdekoodia sekä C:lle, että pythonille.
   Alussa on datan tuottava C-koodi, joka pythonin tapauksessa on kommentoitu ulos.
   Lopussa on datan piirtävä python-koodi, jota kutsutaan tästä C-ohjelmasta, ja joka C:n tapauksessa on kommentoitu ulos.
*/

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

#ifdef IKIROUTA
const char* wetlnimet[]     = {"wetland", "permafrost_bog", "tundra_wetland"};
#else
const char* wetlnimet[]      = {"wetland", "bog", "fen", "marsh"};
#endif
const char* kaudet[]         = {"whole_year", "summer", "freezing", "winter"};
enum                           {whole_year_e, summer_e, freezing_e, winter_e};
const char* menetelmät[]     = {"keskiarvo", "huippuarvo", "kaikki"};
enum			       {keskiarvo_e, huippuarvo_e, kaikki_e};
const char* pripost_sisään[] = {"flux_bio_prior", "flux_bio_posterior"};
const char* pripost_ulos[]   = {"pri", "post"};
#define ARRPIT(a) (sizeof(a)/sizeof(*(a)))

#define SUHT2ABS_KERR 6371229.0*6371229.0 * 0.017453293 * 1 // r2 * ASTE * hila

#ifndef menetelmä
#define menetelmä keskiarvo_e
#endif
#ifndef kausi
#define kausi 1
#endif
//#define BOOTSTRAP
//#define RISTIVALIDOI
const int nboot_vakio = 150;

typedef struct data_t data_t;

void poista_alusta(data_t*, int);
void järjestä_vuon_mukaan(data_t*, double*);

struct data_t {
    double *vuo;
    double *wdata[ARRPIT(wetlnimet)];
    double virtaama; // emissio / m²
    int resol;
    int aikaa;
    int pit;
    double *alat;
};

char aprintapu[256];
char* aprintf(const char* muoto, ...) {
    va_list args;
    va_start(args, muoto);
    vsprintf(aprintapu, muoto, args);
    va_end(args);
    return aprintapu;
}

double laske_virtaama_(const data_t* dt, double *kertoimet, int alku, int loppu) {
    double v = 0;
    double vuot[ARRPIT(wetlnimet)];
    for(int i=1; i<ARRPIT(wetlnimet); i++)
	vuot[i] = (kertoimet[i] + kertoimet[0]) * 1e-9;
    for(int i=alku; i<loppu; i++)
	for(int w=1; w<ARRPIT(wetlnimet); w++)
	    v += vuot[w] * dt->wdata[w][i] * dt->alat[i] * dt->wdata[0][i];
    v *= SUHT2ABS_KERR;
    return v;
}

double laske_virtaama(const data_t* dt, double *kertoimet) {
    return laske_virtaama_(dt, kertoimet, 0, dt->pit);
}

/*
int puolitushaku(const double* a, double f, int alempi, int ylempi) {
alku:
    int keski = (alempi+ylempi)/2;
    if(ylempi-alempi <= 1) return f<alempi? alempi: f<ylempi? ylempi: ylempi+1;
    if(f<a[keski])         ylempi = keski-1;
    else if(f>a[keski])    alempi = keski+1;
    else                   return keski;
    goto alku;
}
*/

double summa(double* dt, int n) {
    double s = 0;
    for(int i=0; i<n; i++) s += dt[i];
    return s;
}

void luo_data_kaikki(const data_t* dt, data_t* dt1, char* kausic, double wraja, double vuoraja) {
    char r_ei_kelpaa[dt->resol];
    memset(r_ei_kelpaa, 2, dt->resol);
    dt1->pit = dt1->virtaama = 0;
    for(int t=0; t<dt->aikaa; t+=3) {
	int tdt = t*dt->resol;
	for(int r=0; r<dt->resol; r++) {
	    if(!kausic[r] || dt->wdata[0][r] < wraja) continue;

	    if(r_ei_kelpaa[r] == 2) {
		double summa=0;
		for(int i=1; i<ARRPIT(wetlnimet); i++)
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
	    for(int i=1; i<ARRPIT(wetlnimet); i++)
		dt1->wdata[i][dt1->pit] = dt->wdata[i][r] / dt->wdata[0][r];
	    dt1->wdata[0][dt1->pit] = dt->wdata[0][r];
	    dt1->pit++;
	}
    }
    dt1->virtaama *= SUHT2ABS_KERR;
}

void luo_data(const data_t* dt, data_t* dt1, char* kausic, double wraja, double vuoraja) {
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
	for(int i=1; i<ARRPIT(wetlnimet); i++)
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
	for(int i=1; i<ARRPIT(wetlnimet); i++)
	    dt1->wdata[i][dt1->pit] = dt->wdata[i][r] / dt->wdata[0][r];
	dt1->wdata[0][dt1->pit] = dt->wdata[0][r];
	dt1->pit++;
    }
    /* Tässä lopussa vasta jätetään pois yhtä monta pienintä arvoa kuin suuria arvoja on jätetty. */
    if(poistettuja) {
	järjestä_vuon_mukaan(dt1, virtaamat);
	poista_alusta(dt1, poistettuja);
    }
    dt1->virtaama = summa(virtaamat+poistettuja, dt1->pit-poistettuja);
    dt1->virtaama *= SUHT2ABS_KERR;
    free(virtaamat);
}

typedef struct {
    const data_t* dt;
    double* kertoimet;
    int nboot, plus;
} Arg;
int arg_luettu = 0;

#define joo_alusta_koko_touhu						\
    int nmuutt = ARRPIT(wetlnimet);					\
    gsl_matrix *xmatrix = gsl_matrix_alloc(dt->pit, nmuutt);		\
    gsl_vector *yvec = gsl_vector_alloc(dt->pit);			\
    gsl_vector *wvec = gsl_vector_alloc(dt->pit);			\
    gsl_vector *cvec = gsl_vector_alloc(nmuutt);			\
    gsl_multifit_linear_workspace *work = gsl_multifit_linear_alloc(dt->pit, nmuutt); \
    gsl_matrix *covm = gsl_matrix_alloc(nmuutt, nmuutt);		\
    double sum2

#define joo_vapauta_koko_touhu			\
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
    int nmuutt = ARRPIT(wetlnimet);
    gsl_matrix *xmatrix = gsl_matrix_alloc(dt->pit, nmuutt);
    gsl_vector *yvec = gsl_vector_alloc(dt->pit);
    gsl_vector *wvec = gsl_vector_alloc(dt->pit);
    gsl_vector *cvec = gsl_vector_alloc(nmuutt);
    gsl_multifit_linear_workspace *work = gsl_multifit_linear_alloc(dt->pit, nmuutt);
    gsl_matrix *covm = gsl_matrix_alloc(nmuutt, nmuutt);
    double sum2;
    /* rand() lukitsee aina tilan, joten rinnakkaislaskenta ei nopeuta, jos rand()-funktiota käytetään.
       rand48_r-funktioitten pitäisi toimia hyvin. */
    struct drand48_data randbuff;
    srand48_r(plus, &randbuff);

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
	/* Tallennetaan vain haluttu lopullinen arvo. Alussa nmuutt+1 kpl on varattuja. */
	for(int i=0; i<nmuutt-1; i++)
	    kertoimet[i+nmuutt+1+(nb+plus)*(nmuutt-1)] = cvec->data[i+1] + cvec->data[0];
    }
    gsl_multifit_linear_free(work);
    gsl_matrix_free(xmatrix);
    gsl_vector_free(yvec);
    gsl_vector_free(wvec);
    gsl_vector_free(cvec);
    gsl_matrix_free(covm);
    return NULL;
}

#define töitä 4
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

    int nmuutt = ARRPIT(wetlnimet);
    gsl_matrix *xmatrix = gsl_matrix_alloc(dt->pit, nmuutt);
    gsl_vector *yvec = gsl_vector_alloc(dt->pit);
    gsl_vector *wvec = gsl_vector_alloc(dt->pit);
    gsl_vector *cvec = gsl_vector_alloc(nmuutt);
    gsl_multifit_linear_workspace *work = gsl_multifit_linear_alloc(dt->pit, nmuutt);
    gsl_matrix *covm = gsl_matrix_alloc(nmuutt, nmuutt);
    double sum2;

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

    gsl_multifit_linear_free(work);
    gsl_matrix_free(xmatrix);
    gsl_vector_free(yvec);
    gsl_vector_free(wvec);
    gsl_vector_free(cvec);
    gsl_matrix_free(covm);
}

double ristivalidoi(const data_t* dt, int määrä) {
    joo_alusta_koko_touhu;

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

    joo_vapauta_koko_touhu;
    return virtaama;
}

void sovittaminen_kerralla(data_t* dt, double kertoimet[]) {
    sovita_monta(dt, kertoimet, kertoimet+ARRPIT(wetlnimet), 0);
    printf("r² = %.4lf\n", kertoimet[ARRPIT(wetlnimet)]);
    for(int i=0; i<ARRPIT(wetlnimet); i++)
	printf("%-12.4lf", kertoimet[i]);
    putchar('\n');
    for(int i=1; i<ARRPIT(wetlnimet); i++)
	printf("%-12.4lf", kertoimet[i]+kertoimet[0]);
    putchar('\n');
}

void sovita_1(data_t* dt, int num, double* vakio, double* kulma, double* r2) {
    double sum2, cov00, cov01, cov11;
    gsl_fit_wlinear(dt->wdata[num], 1, dt->alat, 1, dt->vuo, 1, dt->pit, vakio, kulma, &cov00, &cov01, &cov11, &sum2);
    *r2 = 1 - (sum2 / gsl_stats_wtss(dt->alat, 1, dt->vuo, 1, dt->pit));
}

void sovittaminen_erikseen(data_t* dt) {
    double vakio[ARRPIT(wetlnimet)], kulma[ARRPIT(wetlnimet)], r2;
    for(int i=1; i<ARRPIT(wetlnimet); i++) {
	sovita_1(dt, i, vakio+i, kulma+i, &r2);
	printf("vakio = %7.4lf\tkulma = %8.4lf\tyksi = %.4lf\tr² = %.5lf (%s)\n",
	       vakio[i], kulma[i], vakio[i]+kulma[i], r2, wetlnimet[i]);
    }
    double alat[ARRPIT(wetlnimet)] = {0};
    double summa = 0, ala = 0;
    for(int i=1; i<ARRPIT(wetlnimet); i++) {
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
    for(int i=0; i<ARRPIT(wetlnimet); i++)
	dt->wdata[i] = malloc(rt*sizeof(double));
}

void vapauta_dt1(data_t* dt) {
    free(dt->vuo);
    free(dt->alat);
    for(int i=0; i<ARRPIT(wetlnimet); free(dt->wdata[i++]));
}

#define vaihda(a,b) { apu=a; a=b; b=apu; }
void sekoita(data_t* dt) {
    double apu;
    for(int i=0; i<dt->pit; i++) {
	int ind = rand() % (dt->pit-i);
	vaihda(dt->alat[i], dt->alat[i+ind]);
	vaihda(dt->vuo[i], dt->vuo[i+ind]);
	for(int j=0; j<ARRPIT(wetlnimet); j++)
	    vaihda(dt->wdata[j][i], dt->wdata[j][i+ind]);
    }
}
#undef vaihda

void poista_alusta(data_t* dt, int n) { // Tämä ei pienennä varatun muistin kokoa.
    dt->pit -= n;
    memmove(dt->vuo, dt->vuo+n, dt->pit*sizeof(double));
    for(int i=0; i<ARRPIT(wetlnimet); i++)
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
    for(int i=0; i<ARRPIT(wetlnimet); i++)
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

int main(int argc, char** argv) {
    nct_vset wetlset = {0};
    nct_var *var;
    int ppnum = 1;
    data_t dt;

    struct tm tm0 = {.tm_year=2012-1900, .tm_mon=8-1, .tm_mday=15};
    struct tm tm1 = tm0;
    tm1.tm_year = 2020-1900;
    dt.aikaa = (mktime(&tm1) - mktime(&tm0)) / 86400;

    nct_read_ncfile_gd(&wetlset, "BAWLD1x1.nc");
    for(int i=0; i<ARRPIT(wetlnimet); i++) {
	assert((var = nct_get_var(&wetlset, wetlnimet[i])));
	dt.wdata[i] = var->data;
    }

    dt.resol = nct_get_varlen(var);

    nct_vset *vuovs = nct_read_ncfile_info("flux1x1.nc");
    int alku = hae_alku(nct_get_var(vuovs, "time"), &tm0);
    dt.vuo = nct_load_var_with(nct_get_var(vuovs, pripost_sisään[ppnum]), -1, nc_get_var_double, sizeof(double))->data;
    assert((intptr_t)dt.vuo >= 0x800);
    dt.vuo += alku*dt.resol;

    luo_suhteellinen_pintaala(&dt, vuovs);

    nct_vset* vvv = nct_read_ncfile_info("kaudet2.nc");
    var = nct_load_var(nct_next_truevar(vvv->vars[0], 0), -1);
    alku = hae_alku(nct_get_var(vvv, "time"), &tm0);
    char* kausic = var->data + alku*dt.resol;

    FILE* f = NULL;
    int pit __attribute__((unused)) = ARRPIT(wetlnimet);
#ifdef BOOTSTRAP
    f = popen(aprintf("python ./wetlregressio_jatkuva.c %s", argc>1? argv[1]: ""), "w");
    assert(f);
    assert(fwrite(&pit, 4, 1, f) == 1);
    assert(fwrite(&nboot_vakio, 4, 1, f) == 1);
    fprintf(f, "%s\n%s\n", kaudet[kausi], menetelmät[menetelmä]);
    double kertoimet[pit*(nboot_vakio+1) + 1];
    double kirj[pit + 1];
#endif

    data_t dt1 = dt;
    alusta_dt1(&dt1);
    //const double vuorajat[] = {NAN, 150, 120, 100, 90, 80, 75, 70, 65, 63, 60, 57, 55, 52, 50, 48, 45, 43, 40, 35, 30, 25};
#ifdef IKIROUTA
    const double vuorajat[] = {NAN, 35};
#else
    const double vuorajat[] = {NAN, 50};
#endif
    int rajapit = ARRPIT(vuorajat);
    for(int a=0; a<rajapit; a++) {
	luo_data(&dt, &dt1, kausic, 0.05, vuorajat[a]);

#ifdef BOOTSTRAP
	sovita_monta(&dt1, kertoimet, kertoimet+pit, nboot_vakio);
	for(int i=1; i<pit; i++) {
	    kirj[i-1] = kertoimet[i]+kertoimet[0];
	    printf("%.4lf\t", kirj[i-1]);
	}
	printf("%.0lf, %i\n", vuorajat[a], dt1.pit);
	kirj[pit-1] = (double)dt1.pit;
	kirj[pit] = vuorajat[a];
	assert(fwrite(kirj, sizeof(double), pit+1, f) == pit+1);
	assert(fwrite(kertoimet+pit+1, sizeof(double), (pit-1)*nboot_vakio, f) == (pit-1)*nboot_vakio);
#elif defined RISTIVALIDOI
	sekoita(&dt1);
	double v = ristivalidoi(&dt1, 200);
	printf("%.0lf\t%.0lf\t%.0lf\n", vuorajat[a], v, dt1.virtaama);
#else
	if(!f)
	    assert((f = popen("./wetlregr_piirrä.py", "w")));
	assert(fwrite(&dt1.pit, 4, 1, f) == 1);
	assert(fwrite(dt1.wdata[0], 8, dt1.pit, f) == dt1.pit);
	assert(fwrite(dt1.vuo,      8, dt1.pit, f) == dt1.pit);
	for(int i=1; i<pit; i++) {
	    fprintf(f, "%s\n%s\n", wetlnimet[i], kaudet[kausi]);
	    assert(fwrite(dt1.wdata[i], 8, dt1.pit, f) == dt1.pit);
	}
	pclose(f); f=NULL;
	if(a==1) break;
#endif
    }
    if(f)
	pclose(f);
    f = NULL;

    vapauta_dt1(&dt1);
    nct_free_vset(vvv);
    nct_free_vset(&wetlset);
    nct_free_vset(vuovs);
    free(dt.alat);
}

#if 0
'''#'
from matplotlib.pyplot import *
import numpy as np
import sys, struct

# sys.stdin.readline() ei toimi, koska myöhemmin tulee binääridataa, mistä Python ei ole iloinen.
def lue_rivi():
    lista = bytearray(b'')
    while True:
        a = sys.stdin.buffer.read(1)
        if len(a) == 0 or struct.unpack("b", a)[0] == 10:
            break
        lista.append(a[0])
    return lista.decode('UTF-8')

def main():
    global tehtiin, datastot, rajastot, nimet
    rcParams.update({'figure.figsize':(12,10), 'font.size':13})
    raaka = sys.stdin.buffer.read(8)
    pit,nboot = struct.unpack("ii", raaka)
    if nboot == 0:
        return
    kausi = lue_rivi()
    menetelmä = lue_rivi()
    ax = axes()
    data = np.empty([pit+1, 0], np.float64)
    alue = np.empty([0, 2, pit-1], np.float64)
    while(True):
        raaka = sys.stdin.buffer.read((pit+1)*8)
        if(len(raaka)==0):
            break
        dt = np.ndarray([pit+1,1], dtype=np.float64, buffer=raaka)
        data = np.concatenate([data, dt], axis=1)

        raaka = sys.stdin.buffer.read((pit-1)*nboot*8)
        dt = np.ndarray([nboot, pit-1], dtype=np.float64, buffer=raaka)
        dt = np.percentile(dt, [5,95], axis=0).reshape([1,2,pit-1])
        alue = np.concatenate([alue, dt], axis=0)
        #alue = np.concatenate([alue, np.concatenate([np.min(dt, axis=1).reshape([1,pit-1,1]),
        #                                             np.max(dt, axis=1).reshape([1,pit-1,1])], axis=2)], axis=0)

    värit = ['#ff0000', '#00ff00', '#0000ff']
    (nimet,tunniste) = (['bog', 'fen', 'marsh'],'bfm') if pit == 4 else (['permafrost_bog', 'tundra_wetland'],'pt')
    for i in range(pit-1):
        ax.plot(data[-1,:], data[i,:], c=värit[i], linewidth=2.5, label=nimet[i])
        ax.plot(data[-1,:], alue[:,0,i], c=värit[i], linestyle='--')
        ax.plot(data[-1,:], alue[:,1,i], c=värit[i], linestyle='--')
    #for i in range(pit-2):
    #    ax.fill_between(data[-1,:], alue[:,i,0], alue[:,i,1], color=värit[i], alpha=0.2)
    #ax.fill_between(data[:,-1], alue[:,0,0], alue[:,0,1], color='#ff000058')
    #ax.fill_between(data[:,-1], alue[:,1,0], alue[:,1,1], color='#00ff0058')
    #ax.fill_between(data[:,-1], alue[:,2,0], alue[:,2,1], color='#0000ff58')
    xlabel('upper flux limit')
    ylabel('flux')
    title(kausi)
    legend(loc='upper right')
    ax.twinx()
    plot(data[-1,:], data[-2,:], color='k')
    if '-s' in sys.argv:
        savefig('kuvia/erottelu_%s_%s_%s.png' %(tunniste,kausi,menetelmä))
    show()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

#endif

#include <nctietue2.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdarg.h>
#include <unistd.h>
#include <gsl/gsl_sort.h>
#include <gsl/gsl_statistics.h>
#include <assert.h>
#include <time.h>

// kääntäjä tarvitsee argumentit `pkg-config --libs nctietue2 gsl` -lm
// nctietue2-kirjasto on osoitteessa https://github.com/aerkkila/nctietue2.git

#define ARRPIT(a) (sizeof(a)/sizeof(*(a)))
#define MIN(a,b) (a)<(b)? (a): (b)
#define ASTE 0.017453293
const double r2 = 6371229.0*6371229.0;
#define SUHT_ALA(lat, hila) (sin(((lat)+(hila)*0.5) * ASTE) - sin(((lat)-(hila)*0.5) * ASTE))
#define SUHT2ABS_KERR(hila) (r2 * ASTE * (hila))

const int resol = 19800;
#define LATPIT 55
#define Printf(...) do { if(verbose) printf(__VA_ARGS__); } while(0)

const char* ikirnimet[]      = {"non_permafrost", "sporadic", "discontinuous", "continuous"};
const char* koppnimet[]      = {"D.b", "D.c", "D.d", "ET"};
const char* wetlnimet[]      = {"wetland", "bog", "fen", "marsh", "tundra_wetland", "permafrost_bog"};
const char* kaudet[]         = {"whole_year", "summer", "freezing", "winter"};
enum                           {whole_year_e, summer_e, freezing_e, winter_e};
const char* pripost_sisaan[] = {"flux_bio_prior", "flux_bio_posterior"};
const char* pripost_ulos[]   = {"pri", "post"};
enum                           {kopp_e, ikir_e, wetl_e} luokenum;
const char*** luoknimet;

int vuosi1=2021, vuosi0=2012;
size_t   *kauden_kapasit;
float    alat[LATPIT] = {0};
nct_vset *luok_vs;
int       ppnum, kausia, aikapit, lajinum;
float *restrict vuoptr;
char  *restrict kausiptr, *restrict luok_c;
float *restrict kpitptr;
int ikirvuosi0, ikirvuosia, vuosia, k_alku, v_alku, lajeja;
int verbose;
struct tm tm0 = {.tm_mon=8-1, .tm_mday=15};
struct tm tm1 = {.tm_mon=1-1, .tm_mday=15};

char aprintapu[256];
char* aprintf(const char* muoto, ...) {
    va_list args;
    va_start(args, muoto);
    vsprintf(aprintapu, muoto, args);
    va_end(args);
    return aprintapu;
}

int binsearch(const float* a, float f, int lower, int upper) {
    while(1) {
	int mid = (lower+upper)/2;
	if(upper-lower <= 1)
	    return f<lower? lower: f<upper? upper: upper+1;
	if(f<a[mid])
	    upper = mid-1;
	else if(f>a[mid])
	    lower = mid+1;
	else
	    return mid;
    }
}

int argumentit(int argc, char** argv) {
    if(argc < 3) {
	printf("Käyttö: %s luokitus:köpp/ikir/wetl pri/post [-v]\n", argv[0]);
	return 1;
    }
    if(!strcmp(argv[1], "köpp"))
	luokenum = kopp_e;
    else if (!strcmp(argv[1], "ikir"))
	luokenum = ikir_e;
    else if (!strcmp(argv[1], "wetl"))
	luokenum = wetl_e;
    else {
	printf("Ei luettu luokitusargumenttia\n");
	return 1;
    }
    if(!strcmp(argv[2], "pri"))
	ppnum = 0;
    else if(!strcmp(argv[2], "post"))
	ppnum = 1;
    else {
	printf("Ei luettu pri/post-argumenttia\n");
	return 1;
    }
    for(int i=3; i<argc; i++)
	if(!strcmp(argv[i], "-v"))
	    verbose = 1;
    return 0;
}

static void* lue_kopp() {
    char* luok = malloc(resol);
    int pit;
    FILE* f = fopen("./köppenmaski.txt", "r");
    if(!f) return NULL;
    if((pit=fread(luok, 1, resol, f))!=resol)
	printf("Luettiin %i eikä %i\n", pit, resol);
    for(int i=0; i<resol; i++)
	luok[i] -= '0'+1; // '1' -> 0 jne.
    return (luok_c = luok);
}
static void* lue_ikir() {
    nct_vset *vset = nct_read_ncfile("./ikirdata.nc");
    int varid = nct_get_varid(vset, "luokka");
    char* ret = vset->vars[varid]->data;
    vset->vars[varid]->nonfreeable_data = 1;
    nct_var* var = &NCTVAR(*vset, "vuosi");
    assert(var->xtype == NC_INT);
    ikirvuosi0 = ((int*)var->data)[0];
    ikirvuosia = nct_get_varlen(var);
    nct_free_vset(vset);
    return (luok_c = ret);
}
static void* lue_wetl() {
    return (luok_vs = nct_read_ncfile("./BAWLD1x1.nc"));
}
void* lue_luokitus() {
    static void* (*funktio[])(void) = { [kopp_e]=lue_kopp, [ikir_e]=lue_ikir, [wetl_e]=lue_wetl, };
    return funktio[luokenum]();
}

void tee_data(int luokitusnum, float** vuoulos, float** cdf, double* summa, int ftnum) {
    float *osdet[kausia];
    int kauden_pit[kausia];
    int vuosi = tm0.tm_year+1+1900;
    if(luokenum == wetl_e)
	for(int i=0; i<kausia; i++)
	    osdet[i] = malloc(kauden_kapasit[i]*4);

    memset(kauden_pit, 0, sizeof(int)*kausia);
    for(int i=0; i<kausia; i++)
	summa[i] = 0;

    if (luokitusnum == wetl_e) {
	double *restrict osuus0ptr = NCTVAR(*luok_vs, "wetland").data;
	double *restrict osuus1ptr = NCTVAR(*luok_vs, wetlnimet[lajinum]).data;
	for(int r=0; r<resol; r++) {
	    if(osuus0ptr[r] < 0.05) continue;
	    int t;
	    for(t=0; t<aikapit; t++) {
		int ind_t = t*resol + r;
		if(kausiptr[ind_t] == freezing_e) break;
	    }
	    int kuluva_kausi = freezing_e;
	    for(; t<aikapit; t++) {
		int ind_t = t*resol + r;
		int kausi = kausiptr[ind_t];
		if(kausi != kuluva_kausi) {
		    if(!kausi) continue; // Ehkä tarpeeton tarkistus.
		    if(kuluva_kausi == summer_e)
			break;
		    kuluva_kausi = kausi;
		}
		osdet  [kausi][kauden_pit[kausi]  ] = osuus1ptr[r]; // /osuus0ptr[r]; Olisi väärin jakaa jo tässä.
		osdet  [0    ][kauden_pit[0    ]  ] = osuus1ptr[r]; // /osuus0ptr[r];
		vuoulos[kausi][kauden_pit[kausi]  ] = vuoptr[ind_t] * osuus1ptr[r]/osuus0ptr[r];
		vuoulos[0    ][kauden_pit[0    ]  ] = vuoptr[ind_t] * osuus1ptr[r]/osuus0ptr[r];
		summa  [kausi]                      += (double)vuoulos[kausi][kauden_pit[kausi]] * alat[r/360];
		summa  [0    ]                      += (double)vuoulos[0    ][kauden_pit[0    ]] * alat[r/360];
		cdf    [kausi][kauden_pit[kausi]++] = alat[r/360];
		cdf    [0    ][kauden_pit[0    ]++] = alat[r/360];
	    }
	}
    }
    else if (luokitusnum == kopp_e) {
	for(int r=0; r<resol; r++) {
	    if(luok_c[r] != lajinum) continue;
	    int t;
	    for(t=0; t<aikapit; t++) {
		int ind_t = t*resol + r;
		if(kausiptr[ind_t] == freezing_e) break;
	    }
	    int kuluva_kausi = freezing_e;
	    for(; t<aikapit; t++) {
		int ind_t = t*resol + r;
		int kausi = kausiptr[ind_t];
		if(kausi != kuluva_kausi) {
		    if(!kausi) continue; // Ehkä tarpeeton tarkistus.
		    if(kuluva_kausi == summer_e)
			break;
		    kuluva_kausi = kausi;
		}
		vuoulos[kausi][kauden_pit[kausi]  ] = vuoptr[ind_t];
		vuoulos[0    ][kauden_pit[0    ]  ] = vuoptr[ind_t];
		summa  [kausi]                      += (double)vuoulos[kausi][kauden_pit[kausi]] * alat[r/360];
		summa  [0    ]                      += (double)vuoulos[0    ][kauden_pit[0    ]] * alat[r/360];
		cdf    [kausi][kauden_pit[kausi]++] = alat[r/360];
		cdf    [0    ][kauden_pit[0    ]++] = alat[r/360];
	    }
	}
	Printf("%e\t%i\t%s\t%i\n",
	       gsl_stats_float_mean(vuoulos[1], 1, kauden_pit[1]),
	       vuosi, luoknimet[luokenum][lajinum], kauden_pit[1]);
    }
    else if (luokitusnum == ikir_e)
	for(int r=0; r<resol; r++) {
	    int t;
	    for(t=0; t<aikapit; t++) {
		int ind_t = t*resol + r;
		if(kausiptr[ind_t] == freezing_e) break;
	    }
	    int kuluva_kausi = freezing_e;
	    struct tm tma = tm0;
	    for(; t<aikapit; t++) {
		int v = tma.tm_year+1+1900-ikirvuosi0;
		if(v >= ikirvuosia)
		    v = ikirvuosia-1; // käytetään viimeistä vuotta, kun ikiroutadata loppuu kesken
		int ind_v = v*resol + r;
		int ind_t = t*resol + r;
		if(luok_c[ind_v] != lajinum) continue;
		int kausi = kausiptr[ind_t];
		if(kausi != kuluva_kausi) {
		    if(!kausi) continue; // Ehkä tarpeeton tarkistus.
		    if(kuluva_kausi == summer_e)
			break;
		    kuluva_kausi = kausi;
		}
		vuoulos[kausi][kauden_pit[kausi]  ] = vuoptr[ind_t];
		vuoulos[0    ][kauden_pit[0    ]  ] = vuoptr[ind_t];
		summa  [kausi]                      += (double)vuoulos[kausi][kauden_pit[kausi]] * alat[r/360];
		summa  [0    ]                      += (double)vuoulos[0    ][kauden_pit[0    ]] * alat[r/360];
		cdf    [kausi][kauden_pit[kausi]++] = alat[r/360];
		cdf    [0    ][kauden_pit[0    ]++] = alat[r/360];
		tma.tm_mday++;
		mktime(&tma);
	    }
	}
    else
	printf("Tuntematon luokitusnum: %i\n", luokitusnum);

    if(access("./vuojakaumadata", F_OK))
	if(system("mkdir vuojakaumadata")) {
	    register int eax asm("eax");
	    printf("system(mkdir)-komento palautti arvon %i", eax);
	}

    for(int kausi=0; kausi<kausia; kausi++) {
	float* data   = vuoulos   [kausi];
	float* cdfptr = cdf       [kausi]; // tässä vaiheessa sisältää vain dataa vastaavat pinta-alat
	int    pit    = kauden_pit[kausi];

	Printf("len(%s) = %i\n", kaudet[kausi], pit);
	if(luokitusnum==wetl_e) {
	    float avg = gsl_stats_float_wmean(cdfptr, 1, osdet[kausi], 1, kauden_pit[kausi]);
	    free(osdet[kausi]);
	    for(int j=0; j<kauden_pit[kausi]; j++)
		data[j] /= avg;
	}

	gsl_sort2_float(data, 1, cdfptr, 1, pit);

	for(int i=1; i<kauden_pit[kausi]; i++)
	    cdfptr[i] += cdfptr[i-1];
	for(int i=0; i<kauden_pit[kausi]; i++)
	    cdfptr[i] /= cdfptr[kauden_pit[kausi]-1]; // tämä on harhautunut jakauma, mutta virhe on sangen pieni

	FILE *f = fopen(aprintf("./vuojakaumadata_vuosittain/ft%i_%s_%s_%s_%i.bin",
				ftnum, luoknimet[luokenum][lajinum], kaudet[kausi], pripost_ulos[ppnum], vuosi), "w");
	if(!f) puts("Kohdekansio puuttunee.");

	static int kirjpit = 1000;
	float kirj[kirjpit];
	fwrite(&kirjpit, 4, 1, f);
	fwrite(kauden_pit+kausi, 4, 1, f);
	int ind = 0;
	for(int i=0; i<kirjpit; i++) {
	    ind = binsearch(cdfptr, (float)i/kirjpit, ind, kauden_pit[kausi]);
	    kirj[i] = data[ind]*1e9;
	}
	fwrite(kirj, 4, kirjpit, f);
	fclose(f);
    }
}

/* Paljonko pitää siirtyä eteenpäin, jotta päästään t0:n kohdalle. */
int hae_alku(nct_vset* vset, time_t t0) {
    struct tm tm1;
    nct_anyd tn1 = nct_mktime0(&NCTVAR(*vset, "time"), &tm1);
    if(tn1.d < 0) {
	puts("Ei löytynyt ajan yksikköä");
	return -1;
    }
    tm1 = *nct_localtime((long)nct_get_value_integer(&NCTVAR(*vset, "time"), 0), tn1);
    time_t t1 = mktime(&tm1);
    return (t0-t1) / 86400;
}

void kirjoita_summat(double summat[][vuosi1-vuosi0][kausia], int ftnum) {
    for(int lajinum=0; lajinum<lajeja; lajinum++) {
	FILE* f = fopen(aprintf("./vuojakaumadata_vuosittain/summat_ft%i_%s_%s.csv",
				ftnum, luoknimet[luokenum][lajinum], pripost_ulos[ppnum]), "w");
	fprintf(f, "#ft%i %s %s\n", ftnum, luoknimet[luokenum][lajinum], pripost_ulos[ppnum]);
	for(int kausi=0; kausi<kausia; kausi++) {
	    fprintf(f, "%s", kaudet[kausi]);
	    for(int v=0; v<vuosi1-vuosi0; v++)
		fprintf(f, ",%.4lf", summat[lajinum][v][kausi] * SUHT2ABS_KERR(1) * 86400 * 16.0416 * 1e-12);
	    fputc('\n', f);
	}
	fclose(f);
    }
}

int main(int argc, char** argv) {
    if(argumentit(argc, argv))
	return 1;
    nct_vset vuo;
    kausia = ARRPIT(kaudet);
    const char** _luoknimet[]    = { [kopp_e]=koppnimet, [ikir_e]=ikirnimet, [wetl_e]=wetlnimet, };
    luoknimet = _luoknimet;
    lajeja = ( luokenum==kopp_e? ARRPIT(koppnimet):
	       luokenum==ikir_e? ARRPIT(ikirnimet):
	       luokenum==wetl_e? ARRPIT(wetlnimet):
	       -1 );

    nct_read_ncfile_gd0(&vuo, "./flux1x1.nc");
    nct_var* vuovar = &NCTVAR(vuo, pripost_sisaan[ppnum]);
    if(vuovar->xtype != NC_FLOAT) {
	printf("Vuodatan tyyppi ei täsmää koodissa ja datassa.\n");
	return 1;
    }

    if(!lue_luokitus()) {
	printf("Luokitusta ei luettu\n");
	return 1;
    }

    for(int i=0; i<LATPIT; i++)
	alat[i] = SUHT_ALA(29.5+i, 1);

    putchar('\n');
    int ftnum0=1, ftnum1=3;
    for(int ftnum=ftnum0; ftnum<ftnum1; ftnum++) {
	nct_vset *kausivset = nct_read_ncfile(aprintf("./kaudet%i.nc", ftnum));
	nct_var* kausivar = &NCTVAR(*kausivset, "kausi");
	if(kausivar->xtype != NC_BYTE && kausivar->xtype != NC_UBYTE) {
	    printf("Kausidatan tyyppi ei täsmää koodissa ja datassa.\n");
	    continue;
	}
	double summat[lajeja][vuosi1-vuosi0][kausia];
	for(int vuosi=vuosi0; vuosi<vuosi1; vuosi++) {
	    printf("\033[A\rvuosi %i/%i, ft %i/%i\n",
		   vuosi-vuosi0+1, vuosi1-vuosi0, ftnum-ftnum0+1, ftnum1-ftnum0);
	    /* Laitetaan alku- ja loppuhetket. */
	    tm0.tm_year = vuosi-1-1900;
	    tm1.tm_year = vuosi+1-1900;
	    time_t t0 = mktime(&tm0); // haluttu alkuhetki
	    time_t t1 = mktime(&tm1); // haluttu loppuhetki
	    v_alku = hae_alku(&vuo, t0);
	    vuoptr = (float*)vuovar->data + v_alku*resol;
	    if(0) {
		printf("%i\n", vuosi);
		void* tmp = vuovar->data;
		vuovar->data = vuoptr;
		nct_plot_var(vuovar);
		vuovar->data = tmp;
	    }
	    k_alku = hae_alku(kausivset, t0);
	    kausiptr = kausivar->data + k_alku*resol;
	    if(k_alku < 0) {
		printf("k_alku = %i vuonna %i\n", k_alku, vuosi);
		continue;
	    }
	    if(v_alku < 0) {
		printf("v_alku = %i vuonna %i\n", v_alku, vuosi);
		continue;
	    }
	    aikapit = (t1 - t0) / 86400;
	    int l1  = NCTDIM(*kausivset, "time").len - k_alku;
	    int l2  = NCTDIM(vuo, "time").len - v_alku;
	    int testi = MIN(l1, l2);
	    if(testi < aikapit)
		aikapit = testi; // viimeinen kesä voi loppua kesken
	    Printf("%i: v_alku = %i, k_alku = %i, aikapit = %i\n", vuosi, v_alku, k_alku, aikapit);

	    size_t kauden_kapasit_arr[kausia];
	    kauden_kapasit = kauden_kapasit_arr;
	    kauden_kapasit[whole_year_e] = (size_t)(aikapit*1.0 * resol*0.9);
	    kauden_kapasit[summer_e]     = (size_t)(aikapit*0.7 * resol*0.9);
	    kauden_kapasit[winter_e]     = (size_t)(aikapit*0.5 * resol*0.9);
	    kauden_kapasit[freezing_e]   = (size_t)(aikapit*0.1 * resol*0.9);

	    float* vuojako[kausia];
	    for(int i=0; i<kausia; i++)
		if(!(vuojako[i]=malloc(kauden_kapasit[i] * 4))) {
		    fprintf(stderr, "malloc #%i epäonnistui\n", i);
		    return 1;
		}
	    float* cdf[kausia];
	    for(int i=0; i<kausia; i++)
		if(!(cdf[i]=malloc(kauden_kapasit[i] * 4))) {
		    fprintf(stderr, "malloc #%i epäonnistui (cdf)\n", i);
		    return 1;
		}

	    for(lajinum=0; lajinum<lajeja; lajinum++)
		tee_data(luokenum, vuojako, cdf, summat[lajinum][vuosi-vuosi0], ftnum);

	    for(int i=0; i<kausia; i++) {
		free(vuojako[i]);
		vuojako[i] = NULL;
		free(cdf[i]);
		cdf[i] = NULL;
	    }
	    kauden_kapasit = NULL;
	}
	kirjoita_summat(summat, ftnum);
	nct_free_vset(kausivset);
	kausivset = NULL;
    }
    free(luok_c);
    nct_free_vset(luok_vs);
    nct_free_vset(&vuo);
    return 0;
}

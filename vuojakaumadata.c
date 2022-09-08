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

// kääntäjä tarvitsee argumentit `pkg-config --libs nctietue2 gsl`
// nctietue2-kirjasto on osoitteessa https://github.com/aerkkila/nctietue2.git

#define ARRPIT(a) (sizeof(a)/sizeof(*(a)))
#define MIN(a,b) (a)<(b)? (a): (b)
#define ASTE 0.017453293
#define SUHT_ALA(lat, hila) (sin(((lat)+(hila)*0.5) * ASTE) - sin(((lat)-(hila)*0.5) * ASTE))

const int resol = 19800;
#define LATPIT 55

const char* ikirnimet[]      = {"non_permafrost", "sporadic", "discontinuous", "continuous"};
const char* koppnimet[]      = {"D.b", "D.c", "D.d", "ET"};
const char* wetlnimet[]      = {"wetland", "bog", "fen", "marsh", "tundra_wetland", "permafrost_bog"};
const char* kaudet[]         = {"whole_year", "summer", "freezing", "winter"};
enum                           {whole_year_e, summer_e, freezing_e, winter_e};
const char* pripost_sisaan[] = {"flux_bio_prior", "flux_bio_posterior"};
const char* pripost_ulos[]   = {"pri", "post"};
enum                           {kopp_e, ikir_e, wetl_e} luokenum;
const char*** luoknimet;

size_t   *kauden_kapasit;
float     alat[LATPIT] = {0};
nct_vset *luok_vs;
int       ppnum, kausia, aikapit, lajinum;
float *restrict vuoptr;
char  *restrict kausiptr, *restrict luok_c;
float *restrict kpitptr;
int ikirvuosi0, ikirvuosia, vuosia, k_alku, v_alku;
struct tm tm0 = {.tm_year=2011-1900, .tm_mon=8-1, .tm_mday=15};
const int vuosi1 = 2020;

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
	printf("Käyttö: %s luokitus:köpp/ikir/wetl pri/post [-Bv]\n", argv[0]);
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

double* jaa(double* a, double* b, int pit) {
    double *c = malloc(8*pit);
    for(int i=0; i<pit; i++)
	c[i] = a[i]/b[i];
    return c;
}

void tee_data(int luokitusnum, float** vuoulos, float** cdf) {
    int kauden_pit[kausia];

    memset(kauden_pit, 0, sizeof(int)*kausia);

    if (luokitusnum == wetl_e) {
	double *restrict osuus0ptr = NCTVAR(*luok_vs, "wetland").data;
	double *restrict osuus1ptr = NCTVAR(*luok_vs, wetlnimet[lajinum]).data;
	double* tmp = jaa(osuus1ptr,osuus0ptr,resol);
	gsl_sort(tmp, 1, resol);
	//double keskiosuus = gsl_stats_quantile_from_sorted_data(tmp, 1, resol, 0.25);
	free(tmp);
	for(int r=0; r<resol; r++) {
	    if(osuus0ptr[r] < 0.05) continue;
	    //if(osuus1ptr[r]/osuus0ptr[r] < keskiosuus) continue;
	    for(int t=0; t<aikapit; t++) {
		int ind_t = t*resol + r;
		int kausi = kausiptr[ind_t];
		if(!kausi)          continue;
		float ala = alat[r/360];
		vuoulos[kausi][kauden_pit[kausi]  ] = vuoptr[ind_t] / osuus0ptr[r];
		vuoulos[0    ][kauden_pit[0    ]  ] = vuoptr[ind_t] / osuus0ptr[r];
		cdf    [kausi][kauden_pit[kausi]++] = osuus1ptr[r] * ala;
		cdf    [0    ][kauden_pit[0    ]++] = osuus1ptr[r] * ala;
	    }
	}
    }
    else if (luokitusnum == kopp_e)
	for(int r=0; r<resol; r++) {
	    if(luok_c[r] != lajinum) continue;
	    for(int t=0; t<aikapit; t++) {
		int ind_t = t*resol + r;
		int kausi = kausiptr[ind_t];
		if(!kausi)           continue;
		vuoulos[kausi][kauden_pit[kausi]  ] = vuoptr[ind_t];
		vuoulos[0    ][kauden_pit[0    ]  ] = vuoptr[ind_t];
		cdf    [kausi][kauden_pit[kausi]++] = alat[r/360];
		cdf    [0    ][kauden_pit[0    ]++] = alat[r/360];
	    }
	}
    else if (luokitusnum == ikir_e) {
	struct tm tma = tm0;
	for(int t=0; t<aikapit; t++) {
	    mktime(&tma);
	    int v = tma.tm_year+1900-ikirvuosi0;
	    if(v >= ikirvuosia)
		v = ikirvuosia-1; // käytetään viimeistä vuotta, kun ikiroutadata loppuu kesken
	    for(int r=0; r<resol; r++) {
		int ind_v = v*resol + r;
		int ind_t = t*resol + r;
		int kausi = kausiptr[ind_t];
		if(!kausi)                   continue;
		if(luok_c[ind_v] != lajinum) continue;
		vuoulos[kausi][kauden_pit[kausi]  ] = vuoptr[ind_t];
		vuoulos[0    ][kauden_pit[0    ]  ] = vuoptr[ind_t];
		cdf    [kausi][kauden_pit[kausi]++] = alat[r/360];
		cdf    [0    ][kauden_pit[0    ]++] = alat[r/360];
	    }
	    tma.tm_mday++;
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
	float* cdfptr = cdf       [kausi]; // alussa sisältää pinta-alat
	int    pit    = kauden_pit[kausi];
	
	gsl_sort2_float(data, 1, cdfptr, 1, pit);

	for(int i=1; i<kauden_pit[kausi]; i++)
	    cdfptr[i] += cdfptr[i-1];
	{
	    float tmp0 = cdfptr[0];
	    float tmp1 = cdfptr[kauden_pit[kausi]-1] - tmp0;
	    for(int i=0; i<kauden_pit[kausi]; i++)
		cdfptr[i] = (cdfptr[i]-tmp0) / tmp1;
	}

	FILE *f = fopen(aprintf("./vuojakaumadata/%s_%s_%s.bin",
				luoknimet[luokenum][lajinum], kaudet[kausi], pripost_ulos[ppnum]), "w");
	if(!f)
	    puts("Tallennuskansio puuttunee");

	int kirjpit = 1000;
	if(kauden_pit[kausi] < kirjpit)
	    puts("liian vähän dataa");
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

/* Paljonko pitää siirtyä eteenpäin, jotta päästään t0:n kohdalle */
int hae_alku(nct_vset* vset, time_t t0) {
    struct tm tm1;
    nct_anyd tn1 = nct_mktime(&NCTVAR(*vset, "time"), &tm1, 0);
    if(tn1.d < 0) {
	puts("Ei löytynyt ajan yksikköä");
	return -1;
    }
    return (t0-tn1.a.t) / 86400;
}

int main(int argc, char** argv) {
    if(argumentit(argc, argv))
	return 1;
    nct_vset vuo;
    nct_var* apuvar;
    kausia = ARRPIT(kaudet);
    const char** _luoknimet[]    = { [kopp_e]=koppnimet, [ikir_e]=ikirnimet, [wetl_e]=wetlnimet, };
    luoknimet = _luoknimet;
    int lajeja = ( luokenum==kopp_e? ARRPIT(koppnimet):
		   luokenum==ikir_e? ARRPIT(ikirnimet):
		   luokenum==wetl_e? ARRPIT(wetlnimet):
		   -1 );

    time_t t0 = mktime(&tm0); // haluttu alkuhetki

    nct_read_ncfile_gd0(&vuo, "./flux1x1.nc");
    apuvar = &NCTVAR(vuo, pripost_sisaan[ppnum]);
    if(apuvar->xtype != NC_FLOAT) {
	printf("Vuodatan tyyppi ei täsmää koodissa ja datassa.\n");
	return 1;
    }
    v_alku = hae_alku(&vuo, t0);
    vuoptr = (float*)apuvar->data + v_alku*resol;

    if(!lue_luokitus()) {
	printf("Luokitusta ei luettu\n");
	return 1;
    }

    for(int i=0; i<LATPIT; i++)
	alat[i] = SUHT_ALA(29.5+i, 1);

    for(int ftnum=2; ftnum<3; ftnum++) {
	nct_vset *kausivset = nct_read_ncfile(aprintf("./kaudet%i.nc", ftnum));

	apuvar = &NCTVAR(*kausivset, "kausi");
	if(apuvar->xtype != NC_BYTE && apuvar->xtype != NC_UBYTE) {
	    printf("Kausidatan tyyppi ei täsmää koodissa ja datassa.\n");
	    return 1;
	}
	k_alku = hae_alku(kausivset, t0);
	if(k_alku < 0) {
	    printf("k_alku = %i\n", k_alku);
	    return 1;
	}
	kausiptr = (char*)apuvar->data + k_alku*resol;
	
	int l1  = NCTDIM(*kausivset, "time").len - k_alku;
	int l2  = NCTDIM(vuo, "time").len - v_alku;
	int maxpit = MIN(l1, l2);
	struct tm tm1 = tm0;
	tm1.tm_year = vuosi1-1900;
	aikapit = (mktime(&tm1)-t0) / 86400;
	if(maxpit < aikapit) {
	    puts("liikaa aikaa");
	    aikapit = maxpit;
	}

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
	    tee_data(luokenum, vuojako, cdf);

	nct_free_vset(kausivset);
	kausivset = NULL;
	for(int i=0; i<kausia; i++) {
	    free(vuojako[i]);
	    vuojako[i] = NULL;
	    free(cdf[i]);
	    cdf[i] = NULL;
	}
	kauden_kapasit = NULL;
    }
    free(luok_c);
    nct_free_vset(luok_vs);
    nct_free_vset(&vuo);
    return 0;
}

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
#include <errno.h>

// kääntäjä tarvitsee argumentit `pkg-config --libs nctietue2 gsl`
// lisäksi tarvittaessa -DVUODET_ERIKSEEN=1
// nctietue2-kirjasto on osoitteessa https://github.com/aerkkila/nctietue2.git

#define ARRPIT(a) (sizeof(a)/sizeof(*(a)))
#define MIN(a,b) (a)<(b)? (a): (b)
#define ASTE 0.017453293
const double r2 = 6371229.0*6371229.0;
#define SUHT_ALA(lat, hila) (sin((((double)lat)+(hila)*0.5) * ASTE) - sin((((double)lat)-(hila)*0.5) * ASTE))
#define SUHT2ABS_KERR(hila) (r2 * ASTE * (hila))

#ifndef VUODET_ERIKSEEN
#define VUODET_ERIKSEEN 0
#endif

const int resol = 19800;

const char* ikirnimet[]      = {"non_permafrost", "sporadic", "discontinuous", "continuous"};
const char* koppnimet[]      = {"D.b", "D.c", "D.d", "ET"};
const char* wetlnimet[]      = {"wetland", "bog", "fen", "marsh", "tundra_wetland", "permafrost_bog"};
const char* kaudet[]         = {"whole_year", "summer", "freezing", "winter"};
enum                           {whole_year_e, summer_e, freezing_e, winter_e};
const char* pripost_sisaan[] = {"flux_bio_prior", "flux_bio_posterior"};
const char* pripost_ulos[]   = {"pri", "post"};
enum                           {kopp_e, ikir_e, wetl_e} luokenum;
const char*** luoknimet;
const char* kansio =
#if VUODET_ERIKSEEN
    "./vuojakaumadata/vuosittain"
#else
    "./vuojakaumadata"
#endif
    ;
#define kausia 4
#define wraja 0.05

static nct_vset *luok_vs;
static int       ppnum, aikapit;
static char  *restrict luok_c;
static double *restrict alat;
static int ikirvuosi0, ikirvuosia, vuosia;
static struct tm tm0 = {.tm_mon=8-1, .tm_mday=15};
static struct tm tm1 = {.tm_mon=8-1, .tm_mday=1};
#define vuosi0 2012
#if VUODET_ERIKSEEN
#define vuosi1 2021
static const int vuosi0_var = vuosi0;
#else
#define vuosi1 2020
#endif

typedef struct {
    time_t t;
    struct tm tm;
} tmt;

struct laskenta {
    char* kausiptr;
    float* vuoptr;
    int kuluva_kausi, kuluneita_kausia[kausia], sijainti1[kausia], sijainti[kausia], lajinum, lukitse, vuosi;
    const char* lajinimi;
    float *vuoulos[kausia], *cdf[kausia];
    tmt kesän_alku;
    /* vuodet erikseen */
    double emissio1[kausia], emissio[vuosi1-vuosi0][kausia];
};

tmt* tee_päivä(tmt *aika, int ind_t);

char aprintapu[256];
char* aprintf(const char* muoto, ...) {
    va_list args;
    va_start(args, muoto);
    vsprintf(aprintapu, muoto, args);
    va_end(args);
    return aprintapu;
}

int binsearch(const float* a, float f, int lower, int upper) {
alku:
    int mid = (lower+upper)/2;
    if(upper-lower <= 1) return f<lower? lower: f<upper? upper: upper+1;
    if(f<a[mid])         upper = mid-1;
    else if(f>a[mid])    lower = mid+1;
    else                 return mid;
    goto alku;
}

int argumentit(int argc, char** argv) {
    if(argc < 3) {
	printf("Käyttö: %s luokitus:köpp/ikir/wetl pri/post\n", argv[0]);
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
	luok[i] -= '1';
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

void alusta_lajin_laskenta(struct laskenta* args) {
    for(int i=0; i<kausia; i++) {
	args->kuluneita_kausia[i]          =
	    args->sijainti1[i]             =
	    args->sijainti[i]              =
	    args->emissio[args->vuosi][i]  =
	    args->emissio1[i]              = 0;
    }
    args->lukitse = 0;
}

void alusta_hilaruutu(struct laskenta* args, int t, int kausi) {
    args->kuluva_kausi = kausi;
    args->kuluneita_kausia[0] = t/365;
    memset(args->kuluneita_kausia+1, 0, (kausia-1)*sizeof(int));
}

tmt* tee_päivä(tmt *aika, int ind_t) {
    aika->tm = tm0;
    aika->tm.tm_mday += ind_t / resol;
    aika->t = mktime(&aika->tm);
    return aika;
}

void hyväksy_kausi(struct laskenta* args, int k) {
    /* Jos tähän lisätään jokin esim. maksimiarvon ottaminen kaudelta,
       täytyy käsitellä erikseen monivuotiset kesät. */
    args->sijainti[k] = args->sijainti1[k];
    args->sijainti[0] = args->sijainti1[0];
    if(!VUODET_ERIKSEEN) return;
    args->emissio[args->vuosi][k] += args->emissio1[k];
    args->emissio[args->vuosi][0] += args->emissio1[0];
    args->emissio1[k] = args->emissio1[0] = 0;
}

int tarkista_kausi(struct laskenta* args, int ind_t) {
    if(args->kausiptr[ind_t] == args->kuluva_kausi) return 1; // samaa kautta
    assert(args->kausiptr[ind_t]);
    int lisäys = 1;
    if(args->kuluva_kausi == summer_e) { // kesässä voi olla monta vuotta kerralla
#if !VUODET_ERIKSEEN
	tmt aputmt;
	tee_päivä(&aputmt, ind_t);
	if(args->kesän_alku.tm.tm_year != aputmt.tm.tm_year) {
	    struct tm apu = {.tm_year = args->kesän_alku.tm.tm_year, .tm_mon=8-1, .tm_mday=15};
	    time_t p15_8 = mktime(&apu);
	    lisäys = 0;
	    lisäys += args->kesän_alku.t < p15_8; // onko 15.8. ensimmäisenä vuonna
	    apu = (struct tm){.tm_year=aputmt.tm.tm_year, .tm_mon=8-1, .tm_mday=15};
	    p15_8 = mktime(&apu);
	    lisäys += p15_8 < aputmt.t;           // onko 15.8. viimeisenä vuonna
	    int keskivuosia = aputmt.tm.tm_year - args->kesän_alku.tm.tm_year - 2;
	    lisäys += keskivuosia>0? keskivuosia: 0; // keskivuosissa on aina 15.8.
	}
#endif
	args->kuluneita_kausia[0] += lisäys; // kuluneet kokovuodet lasketaan kesistä
    }
    if(!args->lukitse)
	args->kuluneita_kausia[args->kuluva_kausi] += lisäys;
    if((args->kuluva_kausi = args->kausiptr[ind_t]) == summer_e)
#if VUODET_ERIKSEEN
	aikapit = MIN(ind_t+365, aikapit);
#else
	tee_päivä(&args->kesän_alku, ind_t);
#endif
    if(args->kuluneita_kausia[0] == vuosia)
	return 0; // vuosien määrä täyttyi
    return 2; // kausi vaihtui
}

#define ALKUUN(t,ala)					\
    int t;						\
    args->kuluva_kausi = 0;				\
    for(t=0; t<aikapit; t++)				\
	if(kausiptr[t*resol+r] == 0)			\
	    goto seuraava;				\
    for(t=0; t<aikapit; t++)				\
	if(kausiptr[t*resol + r] == freezing_e		\
	   || kausiptr[t*resol + r] == winter_e) break;	\
    alusta_hilaruutu(args, t, kausiptr[t*resol+r]);	\
    if(args->kuluneita_kausia[0] >= vuosia) continue;   \
    double ala = alat[r/360]

void täytä_kosteikkodata(struct laskenta* args) {
    char* kausiptr = args->kausiptr;
    float* vuoptr = args->vuoptr;
    double *restrict osuus0ptr = NCTVAR(*luok_vs, "wetland").data;
    double *restrict osuus1ptr = NCTVAR(*luok_vs, wetlnimet[args->lajinum]).data;
    /*double* tmp = jaa(osuus1ptr,osuus0ptr,resol);
      gsl_sort(tmp, 1, resol);
      double rajaosuus = gsl_stats_quantile_from_sorted_data(tmp, 1, resol, 0.25);
      free(tmp);*/
    for(int r=0; r<resol; r++) {
	if(osuus0ptr[r] < wraja) continue;
	//if(osuus1ptr[r]/osuus0ptr[r] < rajaosuus) continue;
	ALKUUN(t,ala);
	int kausi = args->kuluva_kausi;

	for(; t<aikapit; t++) {
	    int ind_t = t*resol + r;
	    switch(tarkista_kausi(args, ind_t)) {
	    case 0: hyväksy_kausi(args,kausi); goto seuraava;
	    case 2: hyväksy_kausi(args,kausi); break;
	    }
	    kausi = args->kuluva_kausi;
	    args->vuoulos[kausi][args->sijainti1[kausi]]   = vuoptr[ind_t] / osuus0ptr[r];
	    args->vuoulos[0    ][args->sijainti1[0    ]]   = vuoptr[ind_t] / osuus0ptr[r];
	    args->cdf    [kausi][args->sijainti1[kausi]++] = osuus1ptr[r] * ala;
	    args->cdf    [0    ][args->sijainti1[0    ]++] = osuus1ptr[r] * ala;
#if VUODET_ERIKSEEN
	    args->emissio1[kausi] += vuoptr[ind_t] * osuus1ptr[r]/osuus0ptr[r] * ala;
	    args->emissio1[0    ] += vuoptr[ind_t] * osuus1ptr[r]/osuus0ptr[r] * ala;
#endif
	}
	if(VUODET_ERIKSEEN && args->kuluva_kausi) hyväksy_kausi(args, kausi);
    seuraava:;
    }
}

void täytä_köppendata(struct laskenta* args) {
    char* kausiptr = args->kausiptr;
    float* vuoptr = args->vuoptr;
    for(int r=0; r<resol; r++) {
	if(luok_c[r] != args->lajinum) continue;
	ALKUUN(t,ala);
	int kausi=args->kuluva_kausi;

	for(; t<aikapit; t++) {
	    int ind_t = t*resol + r;
	    switch(tarkista_kausi(args, ind_t)) {
	    case 0: hyväksy_kausi(args,kausi); goto seuraava;
	    case 2: hyväksy_kausi(args,kausi); break;
	    }
	    kausi = args->kuluva_kausi;
	    args->vuoulos[kausi][args->sijainti1[kausi]]   = vuoptr[ind_t];
	    args->vuoulos[0    ][args->sijainti1[0    ]]   = vuoptr[ind_t];
	    args->cdf    [kausi][args->sijainti1[kausi]++] = ala;
	    args->cdf    [0    ][args->sijainti1[0    ]++] = ala;
#if VUODET_ERIKSEEN
	    args->emissio1[kausi] += vuoptr[ind_t] * ala;
	    args->emissio1[0    ] += vuoptr[ind_t] * ala;
#endif
	}
	if(VUODET_ERIKSEEN && args->kuluva_kausi) hyväksy_kausi(args, kausi);
    seuraava:;
    }
}

/* Jos ikiroutaluokka vaihtuu, aloitettu kausi käydään kuitenkin loppuun samana ikiroutaluokkana. */
void täytä_ikirdata(struct laskenta* args) {
    char* kausiptr = args->kausiptr;
    float* vuoptr = args->vuoptr;
    for(int r=0; r<resol; r++) {
	/* Optimoinnin vuoksi tarkistetaan, onko tämä piste milloinkaan oikeaa ikiroutaluokkaa. */
	for(int v=0; v<ikirvuosia; v++)
	    if(luok_c[v*resol+r] == args->lajinum)
		goto piste_kelpaa;
	continue;
    piste_kelpaa:

	ALKUUN(t,ala);
	int kausi=args->kuluva_kausi;
	struct tm tma = tm0; // Tällä tarkistetaan, minkä vuoden ikiroutadataa käytetään.
	tma.tm_mday += t;
	int lukitse_ikirvuosi = 0;
	for(; t<aikapit; t++, tma.tm_mday++) {
	    int ind_v, ind_t = t*resol + r;
	    switch(tarkista_kausi(args, ind_t)) {
	    case 0: hyväksy_kausi(args,kausi); goto seuraava;
	    case 2: hyväksy_kausi(args,kausi); lukitse_ikirvuosi=0; break;
	    }
	    kausi=args->kuluva_kausi;

	    if(!lukitse_ikirvuosi) { // ikiroutaluokitus saa muuttua ajassa vain kauden vaihtuessa
		mktime(&tma);
		int v = tma.tm_year+1900 - ikirvuosi0 + args->vuosi;
		if(v >= ikirvuosia)
		    v = ikirvuosia-1; // Käytetään viimeistä vuotta, kun ikiroutadata loppuu kesken.
		ind_v = v*resol + r;
		lukitse_ikirvuosi = 1;
	    }
	    if(luok_c[ind_v] != args->lajinum) {
		args->lukitse = 1; // tällöin määrää ei kasvateta kauden vaihtuessa
		continue;
	    }
	    args->lukitse = 0;
	    int kausi = kausiptr[ind_t];
	    args->vuoulos[kausi][args->sijainti1[kausi]]   = vuoptr[ind_t];
	    args->vuoulos[0    ][args->sijainti1[0    ]]   = vuoptr[ind_t];
	    args->cdf    [kausi][args->sijainti1[kausi]++] = ala;
	    args->cdf    [0    ][args->sijainti1[0    ]++] = ala;
#if VUODET_ERIKSEEN
	    args->emissio1[kausi] += vuoptr[ind_t] * ala;
	    args->emissio1[0    ] += vuoptr[ind_t] * ala;
#endif
	}
	if(VUODET_ERIKSEEN && args->kuluva_kausi) hyväksy_kausi(args,kausi);
    seuraava:;
    }
}

float* pintaaloista_kertymäfunktio(float* data, float* cdfptr, int pit) {
    gsl_sort2_float(data, 1, cdfptr, 1, pit);
    for(int i=1; i<pit; i++)
	cdfptr[i] += cdfptr[i-1];
    float tmp0 = cdfptr[0];
    float tmp1 = cdfptr[pit-1] - tmp0;
    for(int i=0; i<pit; i++)
	cdfptr[i] = (cdfptr[i]-tmp0) / tmp1;
    return cdfptr;
}

void tallenna(struct laskenta* args, void* data, int kirjpit, int kausi) {
    if(access(kansio, F_OK))
	if(system(aprintf("mkdir %s", kansio))) {
	    register int eax asm("eax");
	    printf("system(mkdir)-komento palautti arvon %i", eax);
	}
    FILE *f = fopen(aprintf("./%s/%s_%s_%s.bin", kansio, args->lajinimi, kaudet[kausi], pripost_ulos[ppnum]), "w");
    assert(f);
    fwrite(&kirjpit, 4, 1, f);
    //fwrite(&args->sijainti[kausi], 4, 1, f);
#if VUODET_ERIKSEEN
    fwrite(&vuosi0_var, 4, 1, f);
#endif
    fwrite(data, 4, kirjpit * (VUODET_ERIKSEEN? vuosi1-vuosi0 : 1), f);
    fclose(f);
}

float* laita_data(struct laskenta* args, float *kohde, int kirjpit, int kausi, int vuosi) {
    float* data = args->vuoulos [kausi];
    int    pit  = args->sijainti[kausi];
    float* cdf  = pintaaloista_kertymäfunktio(data, args->cdf[kausi], pit);
    if(pit < kirjpit)
	printf("liian vähän dataa %i %s, %s, %i\n", pit, args->lajinimi, kaudet[kausi], vuosi);
    int ind = 0;
    for(int i=0; i<kirjpit; i++) {
	ind = binsearch(cdf, (float)i/kirjpit, ind, pit);
	kohde[i] = data[ind]*1e9;
    }
    return kohde;
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

void tee_aikapit(int l1, int l2, int v) {
    tm0.tm_year = vuosi0-1+v-1900;
    tm1.tm_year = VUODET_ERIKSEEN? vuosi0+1+v-1900 : vuosi1-1900;
    time_t t0 = mktime(&tm0);
    aikapit = (mktime(&tm1)-t0) / 86400;
    int maxpit = MIN(l1, l2);
    if(aikapit > maxpit) {
	printf("liikaa aikaa vuonna %i: maxpit=%i\n", vuosi0+v, maxpit);
	aikapit = maxpit;
    }
}

void laita_ja_nollaa_emissio(struct laskenta* args) {
    FILE* f = fopen(aprintf("%s/emissio_%s_%s.csv", kansio, args->lajinimi, pripost_ulos[ppnum]), "w");
    fprintf(f, "#%s %s\n", args->lajinimi, pripost_ulos[ppnum]);
    for(int v=vuosi0; v<vuosi1; v++)
	fprintf(f, ",%i", v);
    fputc('\n', f);
    for(int kausi=0; kausi<kausia; kausi++) {
	fprintf(f, "%s", kaudet[kausi]);
	for(int v=0; v<vuosi1-vuosi0; v++) {
	    fprintf(f, ",%.4lf", args->emissio[v][kausi] * SUHT2ABS_KERR(1) * 86400 * 16.0416 * 1e-12);
	    args->emissio[v][kausi] = 0;
	}
	fputc('\n', f);
    }
    fclose(f);
}

int main(int argc, char** argv) {
    if(argumentit(argc, argv))
	return 1;
    nct_vset vuo;
    nct_var* apuvar;
    tm0.tm_year = vuosi0-1-1900;
    const char** _luoknimet[] = { [kopp_e]=koppnimet, [ikir_e]=ikirnimet, [wetl_e]=wetlnimet, };
    luoknimet = _luoknimet;
    int lajeja = ( luokenum==kopp_e? ARRPIT(koppnimet):
		   luokenum==ikir_e? ARRPIT(ikirnimet):
		   luokenum==wetl_e? ARRPIT(wetlnimet):
		   -1 );
    time_t t0 = mktime(&tm0); // haluttu alkuhetki

    nct_read_ncfile_gd0(&vuo, "./flux1x1.nc");
    int v_alku = hae_alku(&vuo, t0);
    assert(v_alku >= 0);
    apuvar = &NCTVAR(vuo, pripost_sisaan[ppnum]);
    assert(apuvar->xtype == NC_FLOAT);
    float* vuoptr = (float*)apuvar->data + v_alku*resol;

    assert(lue_luokitus());

    int lonpit = NCTVARDIM(*apuvar,2).len;
    int latpit = NCTVARDIM(*apuvar,1).len;
    assert(lonpit*latpit == resol);
    assert((apuvar=&NCTVAR(vuo, "lat"))->xtype == NC_FLOAT);
    float* lat = apuvar->data;
    double _alat[latpit];
    alat = _alat;
    for(int i=0; i<latpit; i++)
	alat[i] = SUHT_ALA(lat[i], 1);

    nct_vset *kausivset = nct_read_ncfile("kaudet2.nc");

    apuvar = &NCTVAR(*kausivset, "kausi");
    assert(apuvar->xtype == NC_BYTE || apuvar->xtype == NC_UBYTE);

    int k_alku = hae_alku(kausivset, t0);
    if(k_alku < 0) {
	printf("k_alku = %i\n", k_alku);
	return 1;
    }
    char* kausiptr = (char*)apuvar->data + k_alku*resol;
	
    int l1  = NCTDIM(*kausivset, "time").len - k_alku;
    int l2  = NCTDIM(vuo, "time").len - v_alku;
    tee_aikapit(l1, l2, 0);
    int L1=l1, L2=l2;
    int vuosia_yht = vuosi1-vuosi0;
    size_t kauden_kapasit[kausia];
    kauden_kapasit[whole_year_e] = (size_t)(aikapit*1.0 * resol*0.9);
    kauden_kapasit[summer_e]     = (size_t)(aikapit*0.7 * resol*0.9);
    kauden_kapasit[winter_e]     = (size_t)(aikapit*0.5 * resol*0.9);
    kauden_kapasit[freezing_e]   = (size_t)(aikapit*0.1 * resol*0.9);

    struct laskenta l_args = {.kausiptr=kausiptr, .vuoptr=vuoptr};

    for(int i=0; i<kausia; i++) {
	assert((l_args.vuoulos[i] = malloc(kauden_kapasit[i] * sizeof(float))));
	assert((l_args.cdf[i]     = malloc(kauden_kapasit[i] * sizeof(float))));
    }

    const int kirjpit = 1000;
    float* apu = malloc(kirjpit*vuosia_yht*kausia*sizeof(float));
    for(int lajinum=0; lajinum<lajeja; lajinum++) {
	for(int v=0; v<vuosia_yht; v++) {
	    tee_aikapit(l1, l2, v);
	    vuosia = aikapit / 365;
	    if(VUODET_ERIKSEEN) assert(vuosia == 1);
	    else assert(vuosia_yht == vuosia);

	    l_args.lajinimi = luoknimet[luokenum][lajinum];
	    l_args.lajinum = lajinum;
	    l_args.vuosi = v;
	    alusta_lajin_laskenta(&l_args);
	    switch(luokenum) {
	    case wetl_e: täytä_kosteikkodata(&l_args); break;
	    case kopp_e: täytä_köppendata(&l_args);    break;
	    case ikir_e: täytä_ikirdata(&l_args);      break;
	    }
	    if(!VUODET_ERIKSEEN) {
		for(int k=0; k<kausia; k++) {
		    laita_data(&l_args, apu, kirjpit, k, -1);
		    tallenna  (&l_args, apu, kirjpit, k);
		}
		goto seuraava_laji;
	    }
	    for(int k=0; k<kausia; k++)
		laita_data(&l_args, apu+k*vuosia_yht*kirjpit+v*kirjpit, kirjpit, k, vuosi0+v);
	    int vuoden_päivät = 365 + (!((vuosi0+v)%4) && ((vuosi0+v)%100 || !(vuosi0+v)%400));

	    l_args.kausiptr += vuoden_päivät*resol;
	    l_args.vuoptr   += vuoden_päivät*resol;
	    l1 -= vuoden_päivät;
	    l2 -= vuoden_päivät;
	}
	laita_ja_nollaa_emissio(&l_args);
	for(int k=0; k<kausia; k++)
	    tallenna(&l_args, apu+k*vuosia_yht*kirjpit, kirjpit, k);
	l_args.kausiptr = kausiptr;
	l_args.vuoptr   = vuoptr;
	l1=L1; l2=L2;
    seuraava_laji:;
    }
    free(apu);

    nct_free_vset(kausivset);
    kausivset = NULL;
    for(int i=0; i<kausia; i++) {
	free(l_args.vuoulos[i]);
	free(l_args.cdf[i]);
    }
    free(luok_c);
    nct_free_vset(luok_vs);
    nct_free_vset(&vuo);
    return 0;
}

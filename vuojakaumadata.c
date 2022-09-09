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

const char* ikirnimet[]      = {"non_permafrost", "sporadic", "discontinuous", "continuous"};
const char* koppnimet[]      = {"D.b", "D.c", "D.d", "ET"};
const char* wetlnimet[]      = {"wetland", "bog", "fen", "marsh", "tundra_wetland", "permafrost_bog"};
const char* kaudet[]         = {"whole_year", "summer", "freezing", "winter"};
enum                           {whole_year_e, summer_e, freezing_e, winter_e};
const char* pripost_sisaan[] = {"flux_bio_prior", "flux_bio_posterior"};
const char* pripost_ulos[]   = {"pri", "post"};
enum                           {kopp_e, ikir_e, wetl_e} luokenum;
const char*** luoknimet;
#define kausia 4
#define wraja 0.05

static size_t   *kauden_kapasit;
static nct_vset *luok_vs;
static int       ppnum, aikapit, lajinum;
static float *restrict vuoptr, *restrict lat;
static char  *restrict kausiptr, *restrict luok_c;
static double *restrict alat;
static int latpit, ikirvuosi0, ikirvuosia, vuosia, k_alku, v_alku;
static struct tm tm0 = {.tm_year=2011-1900, .tm_mon=8-1, .tm_mday=15};
static const int vuosi1 = 2020;

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

typedef struct {
    time_t t;
    struct tm tm;
} tmt;

/* Kuluneita_kausia on tässä turha lukuunottamatta kuluneita kokovuosia. */
struct laskenta {
    char* kausiptr;
    int kuluva_kausi, kuluneita_kausia[kausia], sijainti1[kausia], sijainti[kausia], lajinum, lukitse;
    const char* lajinimi;
    tmt alkuhetki, kesän_alku;
    float *vuoulos[kausia], *cdf[kausia];
};

void alusta_lajin_laskenta(struct laskenta* args) {
    memset(args->kuluneita_kausia, 0,  kausia*sizeof(int));
    memset(args->sijainti1, 0, kausia*sizeof(int));
    memset(args->sijainti,  0, kausia*sizeof(int));
    args->lukitse=0;
}

void alusta_hilaruutu(struct laskenta* args) {
    args->kuluva_kausi = freezing_e;
    memset(args->kuluneita_kausia, 0,  kausia*sizeof(int));
}

tmt tee_päivä(struct laskenta* args, int ind_t) {
    tmt aika = {.tm=args->alkuhetki.tm};
    aika.tm.tm_mday += ind_t / resol;
    aika.t = mktime(&aika.tm);
    return aika;
}

void hyväksy_kausi(struct laskenta* args) {
    /* Jos tähän lisätään jokin esim. maksimiarvon ottaminen kaudelta,
       täytyy käsitellä erikseen monivuotiset kesät. */
    for(int i=0; i<kausia; i++)
	args->sijainti[i] = args->sijainti1[i];
}

int tarkista_kausi(struct laskenta* args, int ind_t) {
    if(args->kausiptr[ind_t] == args->kuluva_kausi) return 1; // samaa kautta
    assert(args->kausiptr[ind_t] != 0);
    int lisäys = 1;
    if(args->kuluva_kausi == summer_e) { // kesässä voi olla monta vuotta kerralla
	tmt kesän_loppu = tee_päivä(args, ind_t);
	if(args->kesän_alku.tm.tm_year != kesän_loppu.tm.tm_year) {
	    struct tm apu = {.tm_year = args->kesän_alku.tm.tm_year, .tm_mon=8-1, .tm_mday=15};
	    time_t p15_8 = mktime(&apu);
	    lisäys = 0;
	    lisäys += args->kesän_alku.t < p15_8; // onko 15.8. ensimmäisenä vuonna
	    apu = (struct tm){.tm_year = kesän_loppu.tm.tm_year, .tm_mon=8-1, .tm_mday=15};
	    p15_8 = mktime(&apu);
	    lisäys += p15_8 < kesän_loppu.t;      // onko 15.8. viimeisenä vuonna
	    int keskivuosia = kesän_loppu.tm.tm_year - args->kesän_alku.tm.tm_year - 2;
	    lisäys += keskivuosia>0? keskivuosia: 0; // keskivuosina on aina 15.8.
	}
	args->kuluneita_kausia[0] += lisäys; // kuluneet kokovuodet lasketaan kesistä
    }
    if(!args->lukitse)
	args->kuluneita_kausia[args->kuluva_kausi] += lisäys;
    if((args->kuluva_kausi = args->kausiptr[ind_t]) == summer_e)
	args->kesän_alku = tee_päivä(args, ind_t);
    if(args->kuluneita_kausia[0] == vuosia)
	return 0; // vuosien määrä täyttyi
    return 2; // kausi vaihtui
}

#define ALKUUN(t,ala)					\
    int t;						\
    for(t=0; t<aikapit; t++)				\
	if(kausiptr[t*resol+r] == 0)			\
	    goto seuraava;				\
    for(t=0; t<aikapit; t++)				\
	if(kausiptr[t*resol + r] == freezing_e) break;	\
    alusta_hilaruutu(args);				\
    double ala = alat[r/360]

void täytä_kosteikkodata(struct laskenta* args) {
    char* kausiptr = args->kausiptr;
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

	for(; t<aikapit; t++) {
	    int ind_t = t*resol + r;
	    switch(tarkista_kausi(args, ind_t)) {
	    case 0: hyväksy_kausi(args); goto seuraava;
	    case 2: hyväksy_kausi(args); break;
	    }
	    int kausi = kausiptr[ind_t];
	    args->vuoulos[kausi][args->sijainti1[kausi]]   = vuoptr[ind_t] / osuus0ptr[r];
	    args->vuoulos[0    ][args->sijainti1[0    ]]   = vuoptr[ind_t] / osuus0ptr[r];
	    args->cdf    [kausi][args->sijainti1[kausi]++] = osuus1ptr[r] * ala;
	    args->cdf    [0    ][args->sijainti1[0    ]++] = osuus1ptr[r] * ala;
	}
    seuraava:;
    }
}

void täytä_köppendata(struct laskenta* args) {
    char* kausiptr = args->kausiptr;
    for(int r=0; r<resol; r++) {
	if(luok_c[r] != lajinum) continue;
	ALKUUN(t,ala);

	for(; t<aikapit; t++) {
	    int ind_t = t*resol + r;
	    switch(tarkista_kausi(args, ind_t)) {
	    case 0: hyväksy_kausi(args); goto seuraava;
	    case 2: hyväksy_kausi(args); break;
	    }
	    int kausi = kausiptr[ind_t];
	    args->vuoulos[kausi][args->sijainti1[kausi]]   = vuoptr[ind_t];
	    args->vuoulos[0    ][args->sijainti1[0    ]]   = vuoptr[ind_t];
	    args->cdf    [kausi][args->sijainti1[kausi]++] = ala;
	    args->cdf    [0    ][args->sijainti1[0    ]++] = ala;
	}
    seuraava:;
    }
}

/* Jos ikiroutaluokka vaihtuu, aloitettu kausi käydään kuitenkin loppuun samana ikiroutaluokkana. */
void täytä_ikirdata(struct laskenta* args) {
    char* kausiptr = args->kausiptr;
    for(int r=0; r<resol; r++) {
	/* Optimoinnin vuoksi tarkistetaan, onko tämä piste milloinkaan oikeaa ikiroutaluokkaa. */
	for(int v=0; v<ikirvuosia; v++)
	    if(luok_c[v*resol+r] == args->lajinum)
		goto piste_kelpaa;
	continue;
    piste_kelpaa:

	ALKUUN(t,ala);
	struct tm tma = tm0; // Tällä tarkistetaan, minkä vuoden ikiroutadataa käytetään.
	tma.tm_mday += t;
	int lukitse_ikirvuosi = 0;
	for(; t<aikapit; t++, tma.tm_mday++) {
	    int ind_v, ind_t = t*resol + r;
	    switch(tarkista_kausi(args, ind_t)) {
	    case 0: hyväksy_kausi(args); goto seuraava;
	    case 2: hyväksy_kausi(args); lukitse_ikirvuosi=0; break;
	    }

	    if(!lukitse_ikirvuosi) { // ikiroutaluokitus saa muuttua ajassa vain kauden vaihtuessa
		mktime(&tma);
		int v = tma.tm_year+1900-ikirvuosi0;
		if(v == ikirvuosia)
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
	}
    seuraava:;
    }
}

void kirjoita_data(struct laskenta* args) {
    if(access("./vuojakaumadata", F_OK))
	if(system("mkdir vuojakaumadata")) {
	    register int eax asm("eax");
	    printf("system(mkdir)-komento palautti arvon %i", eax);
	}

    for(int kausi=0; kausi<kausia; kausi++) {
	float* data   = args->vuoulos [kausi];
	float* cdfptr = args->cdf     [kausi]; // alussa sisältää pinta-alat
	int    pit    = args->sijainti[kausi];
	
	gsl_sort2_float(data, 1, cdfptr, 1, pit);

	for(int i=1; i<pit; i++)
	    cdfptr[i] += cdfptr[i-1];
	{
	    float tmp0 = cdfptr[0];
	    float tmp1 = cdfptr[pit-1] - tmp0;
	    for(int i=0; i<pit; i++)
		cdfptr[i] = (cdfptr[i]-tmp0) / tmp1;
	}

	FILE *f = fopen(aprintf("./vuojakaumadata/%s_%s_%s.bin",
				args->lajinimi, kaudet[kausi], pripost_ulos[ppnum]), "w");
	assert(f);

	int kirjpit = 1000;
	if(pit < kirjpit)
	    printf("liian vähän dataa %i %s\n", pit, args->lajinimi);
	float kirj[kirjpit];
	fwrite(&kirjpit, 4, 1, f);
	fwrite(&pit, 4, 1, f);
	int ind = 0;
	for(int i=0; i<kirjpit; i++) {
	    ind = binsearch(cdfptr, (float)i/kirjpit, ind, pit);
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
    const char** _luoknimet[]    = { [kopp_e]=koppnimet, [ikir_e]=ikirnimet, [wetl_e]=wetlnimet, };
    //const char* luokitus_ulos[] = { [kopp_e]="köppen",  [ikir_e]="ikir",    [wetl_e]="wetland", };
    luoknimet = _luoknimet;
    int lajeja = ( luokenum==kopp_e? ARRPIT(koppnimet):
		   luokenum==ikir_e? ARRPIT(ikirnimet):
		   luokenum==wetl_e? ARRPIT(wetlnimet):
		   -1 );
    time_t t0 = mktime(&tm0); // haluttu alkuhetki

    nct_read_ncfile_gd0(&vuo, "./flux1x1.nc");
    v_alku = hae_alku(&vuo, t0);
    assert(v_alku >= 0);
    apuvar = &NCTVAR(vuo, pripost_sisaan[ppnum]);
    assert(apuvar->xtype == NC_FLOAT);
    vuoptr = (float*)apuvar->data + v_alku*resol;

    assert(lue_luokitus());

    int lonpit = NCTVARDIM(*apuvar,2).len;
    latpit = NCTVARDIM(*apuvar,1).len;
    assert(lonpit*latpit == resol);
    assert((apuvar=&NCTVAR(vuo, "lat"))->xtype == NC_FLOAT);
    lat = apuvar->data;
    double _alat[latpit];
    alat = _alat;
    for(int i=0; i<latpit; i++)
	alat[i] = SUHT_ALA(lat[i], 1);

    for(int ftnum=2; ftnum<3; ftnum++) {
	nct_vset *kausivset = nct_read_ncfile(aprintf("./kaudet%i.nc", ftnum));

	apuvar = &NCTVAR(*kausivset, "kausi");
	assert(apuvar->xtype == NC_BYTE || apuvar->xtype == NC_UBYTE);

	k_alku = hae_alku(kausivset, t0);
	if(k_alku < 0) {
	    printf("k_alku = %i\n", k_alku);
	    return 1;
	}
	kausiptr = (char*)apuvar->data + k_alku*resol;
	if(0){
	    void *tmp = apuvar->data;
	    apuvar->data = kausiptr;
	    NCTDIM(*(apuvar->super), "time").len-=k_alku;
	    apuvar->len=0;
	    nct_plot_var(apuvar);
	    apuvar->data = tmp;
	    return 0;
	}
	
	int l1  = NCTDIM(*kausivset, "time").len - k_alku;
	int l2  = NCTDIM(vuo, "time").len - v_alku;
	int maxpit = MIN(l1, l2);
	struct tm tm1 = {.tm_year=vuosi1-1900, .tm_mon=4-1, .tm_mday=15};
	aikapit = (mktime(&tm1)-t0) / 86400;
	if(aikapit > maxpit) {
	    puts("liikaa aikaa");
	    aikapit = maxpit;
	}
	vuosia = aikapit / 365;

	size_t kauden_kapasit_arr[kausia];
	kauden_kapasit = kauden_kapasit_arr;
	kauden_kapasit[whole_year_e] = (size_t)(aikapit*1.0 * resol*0.9);
	kauden_kapasit[summer_e]     = (size_t)(aikapit*0.7 * resol*0.9);
	kauden_kapasit[winter_e]     = (size_t)(aikapit*0.5 * resol*0.9);
	kauden_kapasit[freezing_e]   = (size_t)(aikapit*0.1 * resol*0.9);

	struct laskenta l_args = {.kausiptr=kausiptr};

	for(int i=0; i<kausia; i++) {
	    assert((l_args.vuoulos[i] = malloc(kauden_kapasit[i] * sizeof(float))));
	    assert((l_args.cdf[i]     = malloc(kauden_kapasit[i] * sizeof(float))));
	}

	for(lajinum=0; lajinum<lajeja; lajinum++) {
	    alusta_lajin_laskenta(&l_args);
	    l_args.lajinimi = luoknimet[luokenum][lajinum];
	    l_args.lajinum = lajinum;
	    switch(luokenum) {
	    case wetl_e: täytä_kosteikkodata(&l_args); break;
	    case kopp_e: täytä_köppendata(&l_args);    break;
	    case ikir_e: täytä_ikirdata(&l_args);      break;
	    }
	    kirjoita_data(&l_args);
	}

	nct_free_vset(kausivset);
	kausivset = NULL;
	for(int i=0; i<kausia; i++) {
	    free(l_args.vuoulos[i]);
	    free(l_args.cdf[i]);
	}
	kauden_kapasit = NULL;
    }
    free(luok_c);
    nct_free_vset(luok_vs);
    nct_free_vset(&vuo);
    return 0;
}

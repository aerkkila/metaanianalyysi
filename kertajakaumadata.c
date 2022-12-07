#include <nctietue2.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdarg.h>
#include <unistd.h>
#include <sys/stat.h> // mkdir
#include <gsl/gsl_sort.h>
#include <gsl/gsl_statistics.h>
#include <assert.h>
#include <time.h>
#include <err.h>

// kääntäjä tarvitsee argumentit `pkg-config --libs nctietue2 gsl`
// lisäksi tarvittaessa -DVUODET_ERIKSEEN=1
// nctietue2-kirjasto on osoitteessa https://github.com/aerkkila/nctietue2.git

#define ARRPIT(a) (sizeof(a)/sizeof(*(a)))
#define MIN(a,b) (a)<(b)? (a): (b)
#define ASTE 0.017453293
const double r2 = 6362132.0*6362132.0;
#define SUHT_ALA(lat, hila) (sin((((double)lat)+(hila)*0.5) * ASTE) - sin((((double)lat)-(hila)*0.5) * ASTE))

#ifndef VUODET_ERIKSEEN
#define VUODET_ERIKSEEN 0
#endif

const int resol = 19800;

const char* ikirnimet[] = {"non_permafrost", "sporadic", "discontinuous", "continuous"};
const char* koppnimet[] = {"D.b", "D.c", "D.d", "ET"};
const char* wetlnimet[] = {"wetland", "bog", "fen", "marsh", "tundra_wetland", "permafrost_bog"};
const char* kaudet[]    = {"whole_year", "summer", "freezing", "winter"};
enum                      {whole_year_e, summer_e, freezing_e, winter_e};
enum                      {kopp_e, ikir_e, wetl_e} luokenum;
const char*** luoknimet;
const char* kansio = "kausijakaumadata";
#define kausia 4
#define wraja 0.05

static size_t   *kauden_kapasit;
static nct_vset *luok_vs;
static int       aikapit;
static char  *restrict luok_c;
static double *restrict alat;
static int ikirvuosi0, ikirvuosia, vuosia, l1;
static struct tm tm0 = {.tm_mon=8-1, .tm_mday=15}; // vain vuotta muutetaan ohjelman aikana
static struct tm tm1 = {.tm_mon=5-1, .tm_mday=1}; // vain vuotta muutetaan ohjelman aikana
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
    const char* lajinimi;
    char* kausiptr;
    int kuluva_kausi, kuluneita_kausia[kausia], lajinum, lukitse, vuosi;
    float *cdf[kausia];
    float* päivät[kausia];
    tmt kesän_alku;
    /* vuodet erikseen */
    long double päiv0sum[vuosi1-vuosi0][kausia], n_päiv0[vuosi1-vuosi0][kausia]; // painotettuina pinta-alalla
    int pisteitä[vuosi1-vuosi0][kausia];
};

tmt* tee_päivä(tmt *aika, int ind_t);
void tee_aikapit(int vuosi_ind);
void tee_aikapit_talvi(int vuosi_ind);

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
    if(argc < 2) {
	printf("Käyttö: %s luokitus:köpp/ikir/wetl\n", argv[0]);
	return 1;
    }
    luokenum =
	!strcmp(argv[1], "köpp")? kopp_e:
	!strcmp(argv[1], "ikir")? ikir_e:
	!strcmp(argv[1], "wetl")? wetl_e:
	-1;
    if(luokenum<0) {
	printf("Ei luettu luokitusargumenttia\n");
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
	    args->pisteitä[args->vuosi][i] =
	    args->päiv0sum[args->vuosi][i] =
	    args->n_päiv0[args->vuosi][i]  = 0;
	if(!args->päivät[i])
	    assert((args->päivät[i] = malloc(resol*vuosia)));
	if(!args->cdf[i])
	    assert((args->cdf[i] = malloc(resol*vuosia)));
    }
    args->lukitse = 0;
}

void päivä_keskiarvoon(struct laskenta* args, double ala, int kausi, int ind_t) {
    tmt aputmt;
    tee_päivä(&aputmt, ind_t);
    if(!(aputmt.tm.tm_year+1900 <= vuosi0+args->vuosi))
	asm("int $3");
    args->päiv0sum[args->vuosi][kausi] += aputmt.t * ala;
    args->n_päiv0[args->vuosi][kausi] += ala;

    struct tm testi = {.tm_year=vuosi0+args->vuosi-1900, .tm_mday=1};
    int toinen = (aputmt.t-mktime(&testi))/86400;
    if(toinen >= 0 && aputmt.tm.tm_yday != toinen)
	asm("int $3");
    
    int *pisteitä = args->pisteitä[args->vuosi]+kausi;
    args->päivät[kausi][*pisteitä] = toinen;
    args->cdf[kausi][*pisteitä] = ala;
    ++*pisteitä;
}

void päivä_keskiarvoon_w(struct laskenta* args, double ala, int kausi, int ind_t, double paino) {
    tmt aputmt;
    tee_päivä(&aputmt, ind_t);
    if(!(aputmt.tm.tm_year+1900 <= vuosi0+args->vuosi))
	asm("int $3");
    args->päiv0sum[args->vuosi][kausi] += aputmt.t * ala * paino;
    args->n_päiv0[args->vuosi][kausi] += ala * paino;

    struct tm testi = {.tm_year=vuosi0+args->vuosi-1900, .tm_mday=1};
    int toinen = (aputmt.t-mktime(&testi))/86400;

    int *pisteitä = args->pisteitä[args->vuosi]+kausi;
    args->päivät[kausi][*pisteitä] = toinen;
    args->cdf[kausi][*pisteitä] = ala*paino;
    ++*pisteitä;
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

int tarkista_kausi(struct laskenta* args, int ind_t) {
    if(args->kausiptr[ind_t] == args->kuluva_kausi) return 1; // samaa kautta
    assert(args->kausiptr[ind_t]);
    assert(args->kuluva_kausi);
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
    if((args->kuluva_kausi = args->kausiptr[ind_t]) == summer_e) {
	if(VUODET_ERIKSEEN)
	    /* Päätepisteenä oli aikapit_talvi.
	       Siirretään siihen, mikä kesälle on sopivaa (struct tm1). */
	    tee_aikapit(args->vuosi);
	else
	    tee_päivä(&args->kesän_alku, ind_t);
    }
    if(args->kuluneita_kausia[0] > 1 && VUODET_ERIKSEEN)
	asm("int $3");
    if(args->kuluneita_kausia[0] >= vuosia) return 0; // vuosien määrä täyttyi
    if(VUODET_ERIKSEEN && luokenum!=wetl_e)
	päivä_keskiarvoon(args, alat[ind_t%resol/360], args->kuluva_kausi, ind_t);
    return 2; // kausi vaihtui
}

#define ALKUUN(t,ala)							\
    int t;								\
    args->kuluva_kausi = 0;						\
    tee_aikapit_talvi(args->vuosi);					\
    for(t=0; t<aikapit; t++)						\
	if(kausiptr[t*resol+r] == 0)					\
	    goto seuraava;						\
    for(t=0; t<aikapit; t++)						\
	if(kausiptr[t*resol + r] == freezing_e				\
	   || kausiptr[t*resol + r] == winter_e) break;			\
    alusta_hilaruutu(args, t, kausiptr[t*resol+r]);			\
    double ala = alat[r/360];						\
    if(args->kuluneita_kausia[0] >= vuosia) continue; /* törkiän tärkiä */ \
    if(VUODET_ERIKSEEN && luokenum!=wetl_e) päivä_keskiarvoon(args, ala, kausiptr[t*resol+r], t*resol+r)

void täytä_kosteikkodata(struct laskenta* args) {
    char* kausiptr = args->kausiptr;
    double *restrict osuus0ptr = NCTVAR(*luok_vs, "wetland").data;
    double *restrict osuus1ptr = NCTVAR(*luok_vs, wetlnimet[args->lajinum]).data;
    for(int r=0; r<resol; r++) {
	if(osuus0ptr[r] < wraja) continue;
	ALKUUN(t,ala);
	päivä_keskiarvoon_w(args, ala, kausiptr[t*resol+r], t*resol+r, osuus1ptr[r]);

	for(; t<aikapit; t++) {
	    int ind_t = t*resol + r;
	    switch(tarkista_kausi(args, ind_t)) {
	    case 0: goto seuraava;
	    case 2: päivä_keskiarvoon_w(args, ala, args->kuluva_kausi, t*resol+r, osuus1ptr[r]); break;
	    }
	}
    seuraava:;
    }
}

void täytä_köppendata(struct laskenta* args) {
    char* kausiptr = args->kausiptr;
    for(int r=0; r<resol; r++) {
	if(luok_c[r] != args->lajinum) continue;
	ALKUUN(t,ala);

	for(; t<aikapit; t++)
	    if(!tarkista_kausi(args, t*resol + r)) goto seuraava;
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
	    case 0: goto seuraava;
	    case 2: lukitse_ikirvuosi=0; break;
	    }

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
	}
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
    if(mkdir(kansio, 0755) < 0 && errno != EEXIST)
	err(1, "mkdir %s epäonnistui, rivi %i", kansio, __LINE__);
    FILE *f = fopen(aprintf("./%s/%s_%s.bin", kansio, args->lajinimi, kaudet[kausi]), "w");
    assert(f);
    fwrite(&kirjpit, 4, 1, f);
#if VUODET_ERIKSEEN
    fwrite(&vuosi0_var, 4, 1, f);
#endif
    fwrite(data, 4, kirjpit * (VUODET_ERIKSEEN? vuosi1-vuosi0 : 1), f);
    fclose(f);
}

float* laita_data(struct laskenta* args, float *kohde, int kirjpit, int kausi, int vuosi) {
    float* data = args->päivät  [kausi];
    int    pit  = args->pisteitä[args->vuosi][kausi];
    float* cdf  = pintaaloista_kertymäfunktio(data, args->cdf[kausi], pit);
    if(pit < kirjpit)
	printf("liian vähän dataa %i %s, %s, %i\n", pit, args->lajinimi, kaudet[kausi], vuosi);
    int ind = 0;
    for(int i=0; i<kirjpit; i++) {
	ind = binsearch(cdf, (float)i/kirjpit, ind, pit);
	kohde[i] = data[ind];
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

/* Asettaa globaalin muuttujan aikapit, johon kesä viimeistään päätetään. */
void tee_aikapit(int v) {
    tm0.tm_year = vuosi0-1+v-1900;
    tm1.tm_year = VUODET_ERIKSEEN? vuosi0+1+v-1900 : vuosi1-1900;
    time_t t0 = mktime(&tm0);
    aikapit = (mktime(&tm1)-t0) / 86400;
    if(aikapit > l1) {
	printf("liikaa aikaa (%i) vuonna %i: maxpit=%i\n", aikapit, vuosi0+v, l1);
	aikapit = l1;
    }
}

/* Asettaan globaalin muuttujan aikapit, johon talvi viimeistään päätetään.
   Jos t0-päivämääränä kesä ei ole alkanut,
   talvi keskeytetään ja sitä jatketaan seuraavaan vuoteen kuuluvana.
   Lähes aina sitä ennen kesä on alkanut ja on kutsuttu tee_aikapit,
   joka on pidentänyt aikarajaa sellaiseksi, mikä kesälle katsotaan sopivaksi. */
void tee_aikapit_talvi(int v) {
    int vuosi = vuosi0+v;
    aikapit = 365 + !(vuosi%4 || (vuosi%100 && !(vuosi%400)));
    if(aikapit > l1) {
	printf("liikaa aikaa (%i) vuonna %i: maxpit=%i\n", aikapit, vuosi0+v, l1);
	aikapit = l1;
    }
}

void laita_alkupäivä(struct laskenta* args) {
    FILE* f = fopen(aprintf("%s/alkupäivät_%s.csv", kansio, args->lajinimi), "w");
    fprintf(f, "#%s\n", args->lajinimi);
    for(int v=vuosi0; v<vuosi1; v++)
	fprintf(f, ",%i", v);
    fputc('\n', f);
    struct tm ttt = {.tm_mon=1-1, .tm_mday=1};
    for(int kausi=1; kausi<kausia; kausi++) {
	fprintf(f, "%s", kaudet[kausi]);
	for(int v=0; v<vuosi1-vuosi0; v++) {
	    ttt.tm_year = v+vuosi0-1900;
	    time_t tavg = args->päiv0sum[v][kausi] / args->n_päiv0[v][kausi];
	    double päivä = (tavg - mktime(&ttt)) / 86400;
	    fprintf(f, ",%i", (int)päivä);
	}
	fputc('\n', f);
    }
    fclose(f);
}

int main(int argc, char** argv) {
    if(argumentit(argc, argv))
	return 1;
    nct_vset apuvset = {0};
    nct_var* apuvar;
    tm0.tm_year = vuosi0-1-1900;
    const char** _luoknimet[] = { [kopp_e]=koppnimet, [ikir_e]=ikirnimet, [wetl_e]=wetlnimet, };
    luoknimet = _luoknimet;
    int lajeja = ( luokenum==kopp_e? ARRPIT(koppnimet):
		   luokenum==ikir_e? ARRPIT(ikirnimet):
		   luokenum==wetl_e? ARRPIT(wetlnimet):
		   -1 );
    time_t t0 = mktime(&tm0); // haluttu alkuhetki

    assert(lue_luokitus());

    nct_read_ncfile_info_gd(&apuvset, "ikirdata.nc");
    int lonpit = nct_get_varlen(&NCTVAR(apuvset, "lon"));
    int latpit = nct_get_varlen(&NCTVAR(apuvset, "lat"));
    double *lat = nct_load_data_with(&apuvset, "lat", nc_get_var_double, sizeof(double));
    assert(lonpit*latpit == resol);
    double _alat[latpit];
    alat = _alat;
    for(int i=0; i<latpit; i++)
	alat[i] = SUHT_ALA(lat[i], 1);
    nct_free_vset(&apuvset);
    free(lat);

    nct_vset *kausivset = nct_read_ncfile("kaudet.nc");

    apuvar = &NCTVAR(*kausivset, "kausi");
    assert(apuvar->xtype == NC_BYTE || apuvar->xtype == NC_UBYTE);

    int k_alku = hae_alku(kausivset, t0);
    if(k_alku < 0) {
	printf("k_alku = %i\n", k_alku);
	return 1;
    }
    char* kausiptr = (char*)apuvar->data + k_alku*resol;
	
    l1 = NCTDIM(*kausivset, "time").len - k_alku;
    tee_aikapit(0);
    int L1=l1;
    int vuosia_yht = vuosi1-vuosi0;

    struct laskenta l_args = {.kausiptr=kausiptr};

    const int kirjpit = 240;
    float* apu = malloc(kirjpit*vuosia_yht*kausia*sizeof(float));
    for(int lajinum=0; lajinum<lajeja; lajinum++) {
	for(int v=0; v<vuosia_yht; v++) {
	    tee_aikapit(v);
	    vuosia = aikapit / 365;
	    if(VUODET_ERIKSEEN)
		assert(vuosia == 1);
	    else
		assert(vuosia_yht == vuosia);

	    l_args.lajinimi = luoknimet[luokenum][lajinum];
	    l_args.lajinum  = lajinum;
	    l_args.vuosi    = v;
	    alusta_lajin_laskenta(&l_args);
	    switch(luokenum) {
	    case wetl_e: täytä_kosteikkodata(&l_args); break;
	    case kopp_e: täytä_köppendata(&l_args);    break;
	    case ikir_e: täytä_ikirdata(&l_args);      break;
	    }
	    if(!VUODET_ERIKSEEN) {
		for(int k=1; k<kausia; k++) {
		    laita_data(&l_args, apu, kirjpit, k, -1);
		    tallenna  (&l_args, apu, kirjpit, k);
		}
		goto seuraava_laji;
	    }
	    for(int k=1; k<kausia; k++)
		laita_data(&l_args, apu+k*vuosia_yht*kirjpit+v*kirjpit, kirjpit, k, vuosi0+v);
	    int vuoden_päivät = 365 + (!((vuosi0+v)%4) && ((vuosi0+v)%100 || !(vuosi0+v)%400));

	    l_args.kausiptr += vuoden_päivät*resol;
	    l1 -= vuoden_päivät;
	}
	laita_alkupäivä(&l_args);
	for(int k=0; k<kausia; k++)
	    tallenna(&l_args, apu+k*vuosia_yht*kirjpit, kirjpit, k);
	l_args.kausiptr = kausiptr;
	l1=L1;
    seuraava_laji:;
    }
    free(apu);

    nct_free_vset(kausivset);
    kausivset = NULL;
    for(int i=0; i<kausia; i++) {
	free(l_args.päivät[i]);
	free(l_args.cdf[i]);
    }
    kauden_kapasit = NULL;
    free(luok_c);
    nct_free_vset(luok_vs);
    return 0;
}

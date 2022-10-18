#include <nctietue2.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdarg.h>
#include <time.h>
#include <assert.h>
#include <unistd.h>
#include <sys/stat.h>

/* Kääntäjä tarvitsee argumentit `pkg-config --libs nctietue2` -lm
   nctietue2-kirjasto on osoitteessa https://github.com/aerkkila/nctietue2.git */

#define ARRPIT(a) sizeof(a)/sizeof(*(a))
#define MIN(a,b) (a)<(b)? (a): (b)
const double r2 = 6371229.0*6371229.0;
#define PINTAALA(lat, hila) ((hila) * r2 * (sin((lat)+0.5*(hila)) - sin((lat)-0.5*(hila))))
#define ASTE 0.017453293

const int resol = 19800;

const char* ikirnimet[]      = {"non_permafrost", "sporadic", "discontinuous", "continuous"};
const char* köppnimet[]      = {"D.b", "D.c", "D.d", "ET"};
const char* wetlnimet[]      = {"wetland", "bog", "fen", "marsh", "permafrost_bog", "tundra_wetland"};
const char* kaudet[]         = {"whole_year", "summer", "freezing", "winter"};
enum                           {whole_year_e, summer_e, freezing_e, winter_e};
const char* pripost_sisaan[] = {"flux_bio_prior", "flux_bio_posterior"};
const char* pripost_ulos[]   = {"pri", "post"};
#define kausia 4
#define wraja 0.05
#ifndef KOSTEIKKO
#define KOSTEIKKO 0 // jaetaanko kuivat luokat kosteikon määrällä
#endif
#ifndef kosteikko_kahtia
#define kosteikko_kahtia 0
#endif

#if kosteikko_kahtia == 0
#define kansio_m "vuotaulukot"
#elif kosteikko_kahtia == 1
#define kansio_m "vuotaulukot/kahtia"
#elif kosteikko_kahtia == 2
#define kansio_m "vuotaulukot/kahtia_keskiosa"
#endif

const char* kansio = kansio_m;
enum luokitus_e {kopp_e, ikir_e, wetl_e} luokenum;
int ppnum;

static float *restrict vuoptr, *restrict lat, *restrict yleiskosteikko;
static char *restrict luok_c;
static double *restrict alat;
static nct_vset *luok_vs;
static int latpit, lonpit, ikirvuosi0, ikirvuosia, aikapit, vuosia, luokkia;
static struct tm tm0 = {.tm_year=2011-1900, .tm_mon=8-1, .tm_mday=15};

void lue_yleiskosteikko();

char aprintapu[256];
char* aprintf(const char* muoto, ...) {
    va_list args;
    va_start(args, muoto);
    vsprintf(aprintapu, muoto, args);
    va_end(args);
    return aprintapu;
}

int argumentit(int argc, char** argv) {
    if(argc < 3) {
	printf("Käyttö: %s köpp/ikir/wetl pri/post\n", argv[0]);
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

void lue_yleiskosteikko() {
#define lue(nimi,var) (yleiskosteikko=nct_read_from_ncfile(nimi, var, nc_get_var_float, sizeof(float)))
    switch(KOSTEIKKO) {
    case 1:   lue("BAWLD1x1.nc", "wetland"); break;
    case 'H': lue("BAWLD1x1_H.nc", "wetland"); break;
    case 'L': lue("BAWLD1x1_L.nc", "wetland"); break;
    case 2:   lue("yleiskosteikko.nc", "data"); break;
    case 3:   lue("../lpx_data/LPX_area_peat.nc", "data"); break;
    }
#undef lue
}

void* lue_kopp() {
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
void* lue_ikir() {
    nct_vset *vset = nct_read_ncfile("./ikirdata.nc");
    int varid = nct_get_varid(vset, "luokka");
    char* ret = vset->vars[varid]->data;
    vset->vars[varid]->nonfreeable_data = 1;
    nct_var* var = &NCTVAR(*vset, "vuosi");
    ikirvuosi0 = ((short*)var->data)[0]; // nouseva tavujärjestys, joten short toimii myös int-datalle
    ikirvuosia = nct_get_varlen(var);
    nct_free_vset(vset);
    return (luok_c = ret);
}
void* lue_wetl() {
    return (luok_vs = nct_read_ncfile("./BAWLD1x1.nc"));
}
void* lue_luokitus() {
    static void* (*funktio[])(void) = { [kopp_e]=lue_kopp, [ikir_e]=lue_ikir, [wetl_e]=lue_wetl, };
    return funktio[luokenum]();
}

typedef struct {
    time_t t;
    struct tm tm;
} tmt;

/*
  var[0][kausi] on se, johon yhden pisteen aikasarja kaudelta ensin summataan,
  var[1][kausi] on se, johon yhden kauden summat yhdestä pisteestä siirretään välitilaan.
  *  Sitä tarvitaan siihen, että summa voidaan jakaa kyseisessä pisteessä olleitten kausien määrällä
  *  ennen kuin lisätään yhteen muitten pisteitten summan kanssa.
  var[2][kausi]  on se, johon lopuksi lisätään var[1] / kausien_määrä_tässä_pisteessä.
  *  Vain tähän muuttujaan kerrytetään tiedot useammasta kuin yhdestä pisteestä.
  */

typedef struct{ double _[3][kausia]; } taikuus;

struct laskenta {
    char* kausiptr;
    taikuus ainemäärä, ala_ja_aika, leveyspiiri;
    int kuluva_kausi, kuluneita_kausia[kausia], lajinum, lukitse;
    const char* lajinimi;
    tmt alkuhetki, kesän_alku;
};
#define olkoon(args,i,j,a) (args)->ainemäärä._[i][j] = (args)->ala_ja_aika._[i][j] = (args)->leveyspiiri._[i][j] = a

void alusta_lasku(struct laskenta* args) {
    args->kuluva_kausi = freezing_e;
    memset(args->kuluneita_kausia, 0,  kausia*sizeof(int));
    for(int i=0; i<kausia; i++) {
	olkoon(args, 0, i, 0);
	olkoon(args, 1, i, 0);
    }
}

void hyväksy_data_välitilasta(struct laskenta* args) {
    for(int k=1; k<kausia; k++)
	if(args->kuluneita_kausia[k] != 0) {
	    double kerroin = 1.0 / args->kuluneita_kausia[k];
	    args->ainemäärä  ._[2][k] += args->ainemäärä  ._[1][k] * kerroin;
	    args->ala_ja_aika._[2][k] += args->ala_ja_aika._[1][k] * kerroin;
	    args->leveyspiiri._[2][k] += args->leveyspiiri._[1][k] * kerroin;
	} // nollaaminen tehdään aina tämän jälkeen alusta_lasku-funktiossa
}

void data_välitilaan(struct laskenta* args) {
    for(int k=1; k<kausia; k++) {
	args->ainemäärä  ._[1][k] += args->ainemäärä  ._[0][k];
	args->ala_ja_aika._[1][k] += args->ala_ja_aika._[0][k];
	args->leveyspiiri._[1][k] += args->leveyspiiri._[0][k];
	olkoon(args, 0, k, 0);
	if(args->ala_ja_aika._[1][k] > 200000*1e3*1e6)
	    asm("int $3");
    }
}

tmt tee_päivä(struct laskenta* args, int ind_t) {
    tmt aika = {.tm=args->alkuhetki.tm};
    aika.tm.tm_mday += ind_t / resol;
    aika.t = mktime(&aika.tm);
    return aika;
}

int tarkista_kausi(struct laskenta* args, int ind_t) {
    if(args->kausiptr[ind_t] == args->kuluva_kausi)
	return 1; // samaa kautta
    if(args->kausiptr[ind_t] == 0) {
	puts("Varoitus: määrittelemätön kausi");
	return 1;
    }
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

#define ALKUUN(t,ala,ala_kost,latnyt)			\
    int t;						\
    for(t=0; t<aikapit; t++)				\
	if(kausiptr[t*resol+r] == 0)			\
	    goto seuraava;				\
    for(t=0; t<aikapit; t++)				\
	if(kausiptr[t*resol + r] == freezing_e) break;	\
    alusta_lasku(args);					\
    double ala = alat[r/360];				\
    double ala_kost = ala;				\
    double latnyt = lat[r/lonpit];			\
    if(yleiskosteikko) {				\
	if(yleiskosteikko[r] < 0.05				\
	   || yleiskosteikko[r] != yleiskosteikko[r]) continue; \
	ala_kost *= yleiskosteikko[r];			\
    }

void laske_köpp(struct laskenta* args) {
    char* kausiptr = args->kausiptr;
    for(int r=0; r<resol; r++) {
	if(luok_c[r] != args->lajinum) continue;

	ALKUUN(t,ala,ala_kost,latnyt);

	for(; t<aikapit; t++) {
	    int ind_t = t*resol + r;
	    switch(tarkista_kausi(args, ind_t)) {
	    case 0: data_välitilaan(args); goto pois_aikasilmukasta;
	    case 2: data_välitilaan(args); break;
	    }
	    double virtaama = vuoptr[ind_t] * ala;
	    args->ainemäärä  ._[0][(int)kausiptr[ind_t]] += virtaama; // *86400 kerrotaan lopussa: mol/s * s -> mol
	    args->ala_ja_aika._[0][(int)kausiptr[ind_t]] += ala_kost; // *86400 kerrotaan lopussa: m²*d -> m²*s
	    args->leveyspiiri._[0][(int)kausiptr[ind_t]] += latnyt*ala_kost;
	}
    pois_aikasilmukasta:
	hyväksy_data_välitilasta(args);
    seuraava:;
    }
}

void laske_kuiva(struct laskenta* args) {
    double* osuusptr = NCTVAR(*luok_vs, "wetland").data;
    char* kausiptr = args->kausiptr;
    for(int r=0; r<resol; r++) {
	if(osuusptr[r] >= wraja) continue;

	ALKUUN(t,ala,ala_kost,latnyt);

	for(; t<aikapit; t++) {
	    int ind_t = t*resol + r;
	    switch(tarkista_kausi(args, ind_t)) {
	    case 0: data_välitilaan(args); goto pois_aikasilmukasta;
	    case 2: data_välitilaan(args); break;
	    }
	    double virtaama = vuoptr[ind_t] * ala;
	    args->ainemäärä  ._[0][(int)kausiptr[ind_t]] += virtaama; // *86400 kerrotaan lopussa: mol/s * s -> mol
	    args->ala_ja_aika._[0][(int)kausiptr[ind_t]] += ala_kost; // *86400 kerrotaan lopussa: m²*d -> m²*s
	    args->leveyspiiri._[0][(int)kausiptr[ind_t]] += latnyt*ala_kost; // tässä funktiossa ala_kost aina == ala
	}
    pois_aikasilmukasta:
	hyväksy_data_välitilasta(args);
    seuraava:;
    }
}

void laske_kosteikko(struct laskenta* args) {
    char* kausiptr = args->kausiptr;
    free(yleiskosteikko); yleiskosteikko=NULL; // varmuuden vuoksi
    double *restrict osuus0ptr = NCTVAR(*luok_vs, "wetland").data;
    double *restrict osuus1ptr = NCTVAR(*luok_vs, wetlnimet[args->lajinum]).data;
#if kosteikko_kahtia
    double *restrict pb = nct_get_var(luok_vs, "permafrost_bog")->data;
    double *restrict tw = nct_get_var(luok_vs, "tundra_wetland")->data;
#endif
    for(int r=0; r<resol; r++) {
	if(osuus0ptr[r] < wraja) continue;
#if kosteikko_kahtia == 1
	double osuus = (pb[r] + tw[r]) / osuus0ptr[r];
	if(0.03 < osuus && osuus < 0.97) continue;
#elif kosteikko_kahtia == 2
	double osuus = (pb[r] + tw[r]) / osuus0ptr[r];
	if(!(0.03 < osuus && osuus < 0.97)) continue;
#endif
	ALKUUN(t,ala,osuusala,latnyt);
	ala *= osuus1ptr[r];         // vain kyseisen luokan pinta-ala
	osuusala = ala/osuus0ptr[r]; // koko ruudun pinta-ala jaettuna osuuden mukaan eri luokille

	for(; t<aikapit; t++) {
	    int ind_t = t*resol + r;
	    switch(tarkista_kausi(args, ind_t)) {
	    case 0: data_välitilaan(args); goto pois_aikasilmukasta;
	    case 2: data_välitilaan(args); break;
	    }
	    args->ainemäärä  ._[0][(int)kausiptr[ind_t]] += vuoptr[ind_t] * osuusala; // *86400 lopussa: mol/s * s -> mol
	    args->ala_ja_aika._[0][(int)kausiptr[ind_t]] += ala;                      // *86400 lopussa: m²*d -> m²*s
	    args->leveyspiiri._[0][(int)kausiptr[ind_t]] += latnyt*ala;               // ala on jo kerrottu luokan osuudella
	}
    pois_aikasilmukasta:
	hyväksy_data_välitilasta(args);
    seuraava:;
    }
}

/* Jos ikiroutaluokka vaihtuu, aloitettu kausi käydään kuitenkin loppuun samana ikiroutaluokkana. */
void laske_ikir(struct laskenta* args) {
    char* kausiptr = args->kausiptr;
    for(int r=0; r<resol; r++) {
	/* Optimoinnin vuoksi tarkistetaan, onko tämä piste milloinkaan oikeaa ikiroutaluokkaa. */
	for(int v=0; v<ikirvuosia; v++)
	    if(luok_c[v*resol+r] == args->lajinum)
		goto piste_kelpaa2;
	continue;
    piste_kelpaa2:

	ALKUUN(t,ala,ala_kost,latnyt);

	struct tm tma = tm0; // Tällä tarkistetaan, minkä vuoden ikiroutadataa käytetään.
	tma.tm_mday += t;
	int lukitse_ikirvuosi = 0;
	for(; t<aikapit; t++, tma.tm_mday++) {
	    int ind_v, ind_t = t*resol + r;
	    switch(tarkista_kausi(args, ind_t)) {
	    case 0: data_välitilaan(args); goto pois_aikasilmukasta;
	    case 2: data_välitilaan(args); lukitse_ikirvuosi=0;
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

	    double virtaama = vuoptr[ind_t] * ala;
	    args->ainemäärä  ._[0][(int)kausiptr[ind_t]] += virtaama; // *86400 lopussa: mol/s * s -> mol
	    args->ala_ja_aika._[0][(int)kausiptr[ind_t]] += ala_kost; // *86400 lopussa: m²*d -> m²*s
	    args->leveyspiiri._[0][(int)kausiptr[ind_t]] += latnyt*ala_kost;
	}
    pois_aikasilmukasta:
	hyväksy_data_välitilasta(args);
    seuraava:;
    }
}

void kirjoita_csv(struct laskenta* args, double tallenn[kausia][luokkia], FILE** ulos) {
    olkoon(args, 2, 0, 0);
    for(int i=1; i<kausia; i++) {
	args->ainemäärä  ._[2][0] += args->ainemäärä  ._[2][i];
	args->ala_ja_aika._[2][0] += args->ala_ja_aika._[2][i];
	args->leveyspiiri._[2][0] += args->leveyspiiri._[2][i];
    }
    for(int i=0; i<kausia; i++) {
	double leveyspiiri = args->leveyspiiri._[2][i] / args->ala_ja_aika._[2][i];
	args->ainemäärä._[2][i]   *= 86400;
	args->ala_ja_aika._[2][i] *= 86400;
	fprintf(ulos[i], "%s,%.4lf,%.5lf,%.4lf,%.4lf\n", args->lajinimi,
		args->ainemäärä  ._[2][i] * 16.0416 * 1e-12,               // Tg
		args->ainemäärä  ._[2][i] / args->ala_ja_aika._[2][i]*1e9, // nmol/s/m²
		args->ala_ja_aika._[2][i] / args->ala_ja_aika._[2][0],     // 1
		leveyspiiri                                                // °
	    );
	tallenn[i][args->lajinum] = args->ainemäärä._[2][i] / args->ala_ja_aika._[2][i]*1e9;
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

/* tekee saman kuin system(mkdir -p kansio) */
void mkdir_p(const char *restrict nimi, int mode) {
    char *restrict k1 = strdup(nimi);
    char *restrict k2 = malloc(strlen(k1));
    *k2 = 0;
    char* str = strtok(k1, "/");
    do {
	sprintf(k2+strlen(k2), "%s/", str);
	assert(!mkdir(k2, mode) || errno == EEXIST);
    } while((str=strtok(NULL, "/")));
    free(k2);
    free(k1);
}

int main(int argc, char** argv) {
    if(argumentit(argc, argv))
	return 1;
    lue_yleiskosteikko();
    nct_vset vuo;
    nct_var* apuvar;
    FILE* ulos[kausia];
    const char** luoknimet[]   = { [kopp_e]=köppnimet, [ikir_e]=ikirnimet, [wetl_e]=wetlnimet, };
    const char* luokitus_ulos[] = { [kopp_e]="köppen",  [ikir_e]="ikir",    [wetl_e]="wetland", };
    luokkia = ( luokenum==kopp_e? ARRPIT(köppnimet):
		luokenum==ikir_e? ARRPIT(ikirnimet):
		luokenum==wetl_e? ARRPIT(wetlnimet):
		-1 );
    time_t t0 = mktime(&tm0); // haluttu alkuhetki

    nct_read_ncfile_gd0(&vuo, "./flux1x1.nc");
    int v_alku = hae_alku(&vuo, t0);
    assert(v_alku >= 0);
    apuvar = &NCTVAR(vuo, pripost_sisaan[ppnum]);
    assert(apuvar->xtype == NC_FLOAT);
    vuoptr = (float*)apuvar->data + v_alku*resol;

    assert(lue_luokitus());

    lonpit = NCTVARDIM(*apuvar,2).len;
    latpit = NCTVARDIM(*apuvar,1).len;
    assert(lonpit*latpit == resol);
    assert((apuvar=&NCTVAR(vuo, "lat"))->xtype == NC_FLOAT);
    lat = apuvar->data;
    double _alat[latpit];
    alat = _alat;
    for(int i=0; i<latpit; i++)
	alat[i] = PINTAALA(ASTE*lat[i], ASTE);

    nct_vset kausivset;
    nct_read_ncfile_gd0(&kausivset, "./kaudet2.nc");

    apuvar = &NCTVAR(kausivset, "kausi");
    assert(apuvar->xtype == NC_BYTE || apuvar->xtype == NC_UBYTE);
	
    int k_alku = hae_alku(&kausivset, t0);
    if(k_alku < 0) {
	printf("k_alku = %i\n", k_alku);
	return 1;
    }
    char* kausiptr = (char*)apuvar->data + k_alku*resol;
	
    int l1        = NCTDIM(kausivset, "time").len - k_alku;
    int l2        = NCTDIM(vuo, "time").len - v_alku;
    int maxpit    = MIN(l1, l2);
    struct tm tm1 = (struct tm){.tm_year=2020-1900, .tm_mon=4-1, .tm_mday=15};
    aikapit       = (mktime(&tm1) - t0) / 86400;
    if(aikapit > maxpit) {
	puts("Liikaa aikaa");
	aikapit = maxpit;
    }
    vuosia = aikapit / 365;

    mkdir_p(kansio, 0755);
    for(int i=0; i<kausia; i++) {
	if(!(ulos[i] =
	     fopen(aprintf(kansio_m "/%svuo_%s_%s_k%i.csv",
			   luokitus_ulos[luokenum], pripost_ulos[ppnum], kaudet[i], KOSTEIKKO*(luokenum!=wetl_e)), "w"))) {
	    printf("Ei luotu ulostiedostoa\n");
	    return 1;
	}
	fprintf(ulos[i], "#%s kosteikko%i\n,Tg,nmol/s/m²,season_length,lat\n", kaudet[i], KOSTEIKKO*(luokenum!=wetl_e));
    }

    double tallenn[kausia][luokkia+1];
    for(int lajinum=0; lajinum<luokkia; lajinum++) {
	struct laskenta l_args = {
	    .lajinum      = lajinum,
	    .kausiptr     = kausiptr,
	    .alkuhetki    = (tmt){.t=t0, .tm=tm0},
	    .lajinimi     = luoknimet[luokenum][lajinum],
	};

	switch(luokenum) {
	case wetl_e: laske_kosteikko(&l_args); break;
	case ikir_e: laske_ikir     (&l_args); break;
	case kopp_e: laske_köpp     (&l_args); break;
	}

	kirjoita_csv(&l_args, tallenn, ulos);
    }

    if(luokenum == wetl_e) {
	struct laskenta l_args = {
	    .kausiptr     = kausiptr,
	    .alkuhetki    = (tmt){.t=t0, .tm=tm0},
	    .lajinum      = luokkia,
	    .lajinimi     = "non-wetland",
	};
	laske_kuiva(&l_args);
	kirjoita_csv(&l_args, tallenn, ulos);

	FILE *f = fopen(aprintf("vuokertoimet_%s.csv", pripost_ulos[ppnum]), "w");
	for(int i=0; i<kausia; i++)
	    fprintf(f, ",%s", kaudet[i]);
	fputc('\n', f);
	for(int i=0; i<luokkia; i++) {
	    fprintf(f, "%s", luoknimet[luokenum][i]);
	    for(int k=0; k<kausia; k++)
		fprintf(f, ",%.6lf", tallenn[k][i]/tallenn[k][0]);
	    fputc('\n', f);
	}
	fclose(f);
    }

    for(int i=0; i<kausia; i++)
	fclose(ulos[i]);
    nct_free_vset(&kausivset);
    kausivset = (nct_vset){0};
    
    free(luok_c);
    free(yleiskosteikko); yleiskosteikko=NULL;
    nct_free_vset(luok_vs);
    nct_free_vset(&vuo);
    return 0;
}

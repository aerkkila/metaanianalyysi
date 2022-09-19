#include <nctietue2.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdarg.h>
#include <time.h>
#include <assert.h>

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
#define KOSTEIKKO 0
#endif
enum luokitus_e {kopp_e, ikir_e, wetl_e, kart_e} luokenum;
int ppnum;

static float *restrict vuoptr, *restrict lat, *restrict yleiskosteikko;
static char *restrict luok_c;
static double *restrict alat;
static nct_vset *luok_vs;
static int latpit, ikirvuosi0, ikirvuosia, aikapit, vuosia, luokkia;
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
	if(argc == 2 && !strcmp(argv[1], "kartta")) {
	    luokenum = kart_e;
	    return 0;
	}
	printf("Käyttö: %s (kartta) TAI (köpp/ikir/wetl pri/post)\n", argv[0]);
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
    if(luokenum == kart_e) return (void*)1;
    static void* (*funktio[])(void) = { [kopp_e]=lue_kopp, [ikir_e]=lue_ikir, [wetl_e]=lue_wetl, };
    return funktio[luokenum]();
}

typedef struct {
    time_t t;
    struct tm tm;
} tmt;

struct laskenta {
    char* kausiptr;
    double *ainemäärä, *ainemäärä1, *ala_ja_aika, *ala_ja_aika1, *ainemäärä2, *ala_ja_aika2, pintaala;
    int kuluva_kausi, kuluneita_kausia[kausia], lajinum, lukitse;
    const char* lajinimi;
    tmt alkuhetki, kesän_alku;
};

void alusta_lasku(struct laskenta* args) {
    args->kuluva_kausi = freezing_e;
    memset(args->kuluneita_kausia, 0,  kausia*sizeof(int));
    memset(args->ainemäärä1, 0, kausia*8);
    memset(args->ala_ja_aika1, 0, kausia*8);
    memset(args->ainemäärä2, 0, kausia*8);
    memset(args->ala_ja_aika2, 0, kausia*8);
}

void hyväksy_data_välitilasta(struct laskenta* args) {
    for(int k=1; k<kausia; k++)
	if(args->kuluneita_kausia[k] != 0) {
	    double kerroin = 1.0 / args->kuluneita_kausia[k];
	    args->ainemäärä   [k] += args->ainemäärä2[k] * kerroin;
	    args->ala_ja_aika [k] += args->ala_ja_aika2[k] * kerroin;
	}
}

void data_välitilaan(struct laskenta* args) {
    for(int k=1; k<kausia; k++) {
	args->ainemäärä2   [k] += args->ainemäärä1[k];
	args->ala_ja_aika2 [k] += args->ala_ja_aika1[k];
	args->ainemäärä1[k]=args->ala_ja_aika1[k] = 0;
	if(args->ala_ja_aika2[k] > 200000*1e3*1e6)
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

void vanha_tee_kartta(struct laskenta* args) {
    static int tehty = 0;
    if(tehty)
	puts("Varoitus, uusi kutsu tee_kartta-funktioon päällekirjoittaa vanhan kartan");
    tehty = 1;
    char* kausiptr = args->kausiptr;
    char kartta[resol];
    for(int r=0; r<resol; r++) {
	if(!kausiptr[r]) {
	    kartta[r]=0; continue; }
	kartta[r] = 1;
	int t;
	for(t=0; t<aikapit; t++)
	    if(kausiptr[t*resol+r] == freezing_e) break;
	alusta_lasku(args);
	for(; t<aikapit; t++) {
	    int ind_t = t*resol+r;
	    if(!tarkista_kausi(args, ind_t)) {
		kartta[r] = 2;
		break;
	    }
	}
    }
    nct_vset v = {0};
    size_t dimlens[] = {latpit, resol/latpit};
    nct_add_var_(&v, kartta, NC_BYTE, "data", 2, NULL, dimlens, NULL)->nonfreeable_data = 1;
    nct_write_ncfile(&v, "vanha_käytetty_alue.nc");
    nct_free_vset(&v);
}

void tee_kartta(struct laskenta* args) {
    static int tehty = 0;
    char* kausiptr = args->kausiptr;
    char kartta[resol];
    for(int r=0; r<resol; r++) {
	char ens = !!kausiptr[r];
	for(int t=0; t<aikapit; t++)
	    if(!!kausiptr[t*resol+r] != ens) {
		kartta[r]=1; goto seuraava; }
	kartta[r]=ens*2;
    seuraava:;
    }
    nct_vset v = {0};
    size_t dimlens[] = {latpit, resol/latpit};
    nct_add_var_(&v, kartta, NC_BYTE, "data", 2, NULL, dimlens, NULL)->nonfreeable_data = 1;
    nct_write_ncfile(&v, aprintf("käytetty_alue%i.nc", ++tehty));
    nct_free_vset(&v);
}

#define ALKUUN(t,ala,ala_kost)				\
    int t;						\
    for(t=0; t<aikapit; t++)				\
	if(kausiptr[t*resol+r] == 0)			\
	    goto seuraava;				\
    for(t=0; t<aikapit; t++)				\
	if(kausiptr[t*resol + r] == freezing_e) break;	\
    alusta_lasku(args);					\
    double ala = alat[r/360];				\
    double ala_kost = ala;				\
    if(yleiskosteikko) {				\
	if(yleiskosteikko[r] < 0.05				\
	   || yleiskosteikko[r] != yleiskosteikko[r]) continue; \
	ala_kost *= yleiskosteikko[r];			\
    }

void laske_köpp(struct laskenta* args) {
    char* kausiptr = args->kausiptr;
    for(int r=0; r<resol; r++) {
	if(luok_c[r] != args->lajinum) continue;

	ALKUUN(t,ala,ala_kost);

	for(; t<aikapit; t++) {
	    int ind_t = t*resol + r;
	    switch(tarkista_kausi(args, ind_t)) {
	    case 0: data_välitilaan(args); goto pois_aikasilmukasta;
	    case 2: data_välitilaan(args); break;
	    }
	    double virtaama = vuoptr[ind_t] * ala;
	    args->ainemäärä1  [(int)kausiptr[ind_t]] += virtaama; // *86400 kerrotaan lopussa: mol/s * s -> mol
	    args->ala_ja_aika1[(int)kausiptr[ind_t]] += ala_kost; // *86400 kerrotaan lopussa: m²*d -> m²*s
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

	ALKUUN(t,ala,ala_kost);

	for(; t<aikapit; t++) {
	    int ind_t = t*resol + r;
	    switch(tarkista_kausi(args, ind_t)) {
	    case 0: data_välitilaan(args); goto pois_aikasilmukasta;
	    case 2: data_välitilaan(args); break;
	    }
	    double virtaama = vuoptr[ind_t] * ala;
	    args->ainemäärä1  [(int)kausiptr[ind_t]] += virtaama; // *86400 kerrotaan lopussa: mol/s * s -> mol
	    args->ala_ja_aika1[(int)kausiptr[ind_t]] += ala_kost;  // *86400 kerrotaan lopussa: m²*d -> m²*s
	}
    pois_aikasilmukasta:
	hyväksy_data_välitilasta(args);
    seuraava:;
    }
}

void laske_kosteikko(struct laskenta* args) {
    char* kausiptr = args->kausiptr;
    free(yleiskosteikko); yleiskosteikko=NULL; // varmuuden vuoksi
    double* osuus0ptr = NCTVAR(*luok_vs, "wetland").data;
    double* osuus1ptr = NCTVAR(*luok_vs, wetlnimet[args->lajinum]).data;
    args->pintaala = 0;
    for(int r=0; r<resol; r++) {
	if(osuus0ptr[r] < wraja) continue;

	ALKUUN(t,ala,osuusala);
	ala *= osuus1ptr[r];         // vain kyseisen luokan pinta-ala
	osuusala = ala/osuus0ptr[r]; // koko ruudun pinta-ala jaettuna osuuden mukaan eri luokille

	args->pintaala += ala;
	for(; t<aikapit; t++) {
	    int ind_t = t*resol + r;
	    switch(tarkista_kausi(args, ind_t)) {
	    case 0: data_välitilaan(args); goto pois_aikasilmukasta;
	    case 2: data_välitilaan(args); break;
	    }
	    args->ainemäärä1  [(int)kausiptr[ind_t]] += vuoptr[ind_t] * osuusala; // *86400 kerrotaan lopussa: mol/s * s -> mol
	    args->ala_ja_aika1[(int)kausiptr[ind_t]] += ala;                      // *86400 kerrotaan lopussa: m²*d -> m²*s
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

	ALKUUN(t,ala,ala_kost);

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
	    args->ainemäärä1  [(int)kausiptr[ind_t]] += virtaama; // *86400 kerrotaan lopussa: mol/s * s -> mol
	    args->ala_ja_aika1[(int)kausiptr[ind_t]] += ala_kost; // *86400 kerrotaan lopussa: m²*d -> m²*s
	}
    pois_aikasilmukasta:
	hyväksy_data_välitilasta(args);
    seuraava:;
    }
}

void kirjoita_csv(struct laskenta* args, double tallenn[kausia][luokkia], FILE** ulos) {
    args->ala_ja_aika[0]=args->ainemäärä[0] = 0;
    for(int i=1; i<kausia; i++) {
	args->ala_ja_aika[0] += args->ala_ja_aika[i];
	args->ainemäärä  [0] += args->ainemäärä  [i];
    }
    for(int i=0; i<kausia; i++) {
	args->ainemäärä[i]   *= 86400;
	args->ala_ja_aika[i] *= 86400;
	fprintf(ulos[i], "%s,%.4lf,%.5lf,%.4lf\n", args->lajinimi,
		args->ainemäärä[i] * 16.0416 * 1e-12,          // Tg
		args->ainemäärä[i] / args->ala_ja_aika[i]*1e9, // nmol/s/m²
		args->ala_ja_aika[i] / args->ala_ja_aika[0]    // 1
	    );
	tallenn[i][args->lajinum] = args->ainemäärä[i] / args->ala_ja_aika[i]*1e9;
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
    lue_yleiskosteikko();
    nct_vset vuo;
    nct_var* apuvar;
    FILE* ulos[kausia];
    const char** luoknimet[]   = { [kopp_e]=köppnimet, [ikir_e]=ikirnimet, [wetl_e]=wetlnimet, };
    const char* luokitus_ulos[] = { [kopp_e]="köppen",  [ikir_e]="ikir",    [wetl_e]="wetland", };
    luokkia = ( luokenum==kopp_e? ARRPIT(köppnimet):
		luokenum==ikir_e? ARRPIT(ikirnimet):
		luokenum==wetl_e? ARRPIT(wetlnimet):
		luokenum==kart_e? 1:
		-1 );
    time_t t0 = mktime(&tm0); // haluttu alkuhetki

    nct_read_ncfile_gd0(&vuo, "./flux1x1.nc");
    int v_alku = hae_alku(&vuo, t0);
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

    if(luokenum != kart_e)
	for(int i=0; i<kausia; i++) {
	    if(!(ulos[i] =
		 fopen(aprintf("vuotaulukot/%svuo_%s_%s_k%i.csv",
			       luokitus_ulos[luokenum], pripost_ulos[ppnum], kaudet[i], KOSTEIKKO*(luokenum!=wetl_e)), "w"))) {
		printf("Ei luotu ulostiedostoa\n");
		return 1;
	    }
	    fprintf(ulos[i], "#%s kosteikko%i\n,Tg,nmol/s/m²,season_length\n", kaudet[i], KOSTEIKKO*(luokenum!=wetl_e));
	}
    double tallenn[kausia][luokkia+1];
    for(int lajinum=0; lajinum<luokkia; lajinum++) {
	double ainemäärä   [kausia] = {0}; // mol
	double ala_ja_aika [kausia] = {0}; // m²*s
	double ainemäärä1  [kausia] = {0}; // mol
	double ala_ja_aika1[kausia] = {0}; // m²*s
	double ainemäärä2  [kausia] = {0}; // mol
	double ala_ja_aika2[kausia] = {0}; // m²*s

	struct laskenta l_args = {.ainemäärä=ainemäärä, .ala_ja_aika=ala_ja_aika,
				  .ainemäärä1=ainemäärä1, .ala_ja_aika1=ala_ja_aika1,
				  .ainemäärä2=ainemäärä2, .ala_ja_aika2=ala_ja_aika2,
				  .lajinum=lajinum, .kausiptr=kausiptr,
				  .alkuhetki=(tmt){.t=t0, .tm=tm0},
				  .lajinimi=luokenum!=kart_e? luoknimet[luokenum][lajinum]: NULL};

	switch(luokenum) {
	case wetl_e: laske_kosteikko(&l_args); break;
	case ikir_e: laske_ikir     (&l_args); break;
	case kopp_e: laske_köpp     (&l_args); break;
	case kart_e: tee_kartta     (&l_args); goto vapauta;
	}

	kirjoita_csv(&l_args, tallenn, ulos);
    }

    if(luokenum == wetl_e) {
	double ainemäärä   [kausia] = {0}; // mol
	double ala_ja_aika [kausia] = {0}; // m²*s
	double ainemäärä1  [kausia] = {0}; // mol
	double ala_ja_aika1[kausia] = {0}; // m²*s
	double ainemäärä2  [kausia] = {0}; // mol
	double ala_ja_aika2[kausia] = {0}; // m²*s
	struct laskenta l_args = {.ainemäärä=ainemäärä, .ala_ja_aika=ala_ja_aika,
				  .ainemäärä1=ainemäärä1, .ala_ja_aika1=ala_ja_aika1,
				  .ainemäärä2=ainemäärä2, .ala_ja_aika2=ala_ja_aika2,
				  .kausiptr=kausiptr,
				  .alkuhetki=(tmt){.t=t0, .tm=tm0},
				  .lajinum=luokkia, .kausiptr=kausiptr, .lajinimi="dryland"};
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
vapauta:
    nct_free_vset(&kausivset);
    kausivset = (nct_vset){0};
    
    free(luok_c);
    free(yleiskosteikko); yleiskosteikko=NULL;
    nct_free_vset(luok_vs);
    nct_free_vset(&vuo);
    return 0;
}

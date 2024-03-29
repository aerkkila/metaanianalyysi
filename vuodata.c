#include <nctietue3.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <assert.h>
#include <err.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include "pintaalat.h"
#include "aikaväli.py"

#define Lat(i) (lat0+(i)/360)

#define lonpit 360
#define KANSIO "vuodata/"
#define LOPUSTA_PUUTTUU 1 // Metaanidatasta viimeisen vuoden lopussa puuttuvien päivien määrä. Esim. 1 -> 30.12. viimeinen
const char* ikirnimet[]      = {"non-permafrost", "sporadic", "discontinuous", "continuous"};
const char* köppnimet[]      = {"Db", "Dc", "Dd", "ET"};
const char* wetlnimet[]      = {"wetland", "bog", "fen", "marsh", "permafrost_bog", "tundra_wetland"};
const char* totlnimet[]      = {"total"};
const char* kaudet[]         = {"whole_year", "thaw", "freezing", "winter"};
enum                           {whole_year_e, thaw_e, freezing_e, winter_e};
const char* luokitus_ulos[]  = {"total", "köppen", "ikir", "wetland"};
enum luokitus_e                {totl_e,   köpp_e,   ikir_e, wetl_e};
const char* vuolaji_sisään[] = {"flux_bio_prior", "flux_bio_posterior", "flux_antro_prior", "flux_antro_posterior"};
const char* vuolaji_ulos[]   = {"biopri", "biopost", "antropri", "antropost"};
#define kausia 4
#define wraja 0.05
#define vuosi0_ 2011

enum alue_e     {kokoalue_e, nontemperate_e, temperate_e} alueenum;
enum luokitus_e luokenum;
int vlnum=1, kosteikko, vuosittain; // argumentteja
int ikirvuosi0, ikirvuosia, vuosi1kaikki, luokkia; // määritettäviä
typeof(&ikirnimet) luoknimet;
double lat0, koko_vuoden_jakaja, jakajien_summa;

struct tiedot {
    double *vuo, *WET;
    short *alut, *loput;
    int *vuodet, res, v0, v1;
    time_t aika0;
    char* alue;
    double (*summan_kerroin)(const struct tiedot* restrict, int);
    double (*jakajan_kerroin)(const struct tiedot* restrict, int);
    /* wetland */
    double* wet;
    /* ikirouta */
    char* ikir;
    int luokka;
};

struct tulos {
    double *summat, *jakajat, *alat, lat, jak1, sum1;
    int pisteitä;
};

#define epäluku 1e24
#define on_epäluku(f) ((f)>1e23)

int argumentit(int argc, char** argv) {
    for(int i=1; i<argc; i++)
	if(!strcmp(argv[i], "totl"))
	    luokenum = totl_e;
	else if(!strcmp(argv[i], "köpp"))
	    luokenum = köpp_e;
	else if(!strcmp(argv[i], "ikir"))
	    luokenum = ikir_e;
	else if(!strcmp(argv[i], "wetl"))
	    luokenum = wetl_e;
	else if(!strcmp(argv[i], "pri"))
	    vlnum = 0;
	else if(!strcmp(argv[i], "post"))
	    vlnum = 1;
	else if(!strcmp(argv[i], "antro"))
	    vlnum += 2;
	else if(!strcmp(argv[i], "kosteikko"))
	    kosteikko = 1;
	else if(!strcmp(argv[i], "vuosittain"))
	    vuosittain = 1;
	else if(!strcmp(argv[i], "temperate"))
	    alueenum = temperate_e;
	else if(!strcmp(argv[i], "nontemperate"))
	    alueenum = nontemperate_e;
	else {
	    fprintf(stderr, "\033[91mVirheellinen argumentti\033[0m %s\n", argv[i]);
	    return 1;
	}
    return 0;
}

#define VIRHE -1234567
#define PÄIVÄTÄYTTÖ 999
int montako_päivää(time_t aika0, int vuosi, short päivä) {
    if(päivä == PÄIVÄTÄYTTÖ)
	return VIRHE;
    struct tm aikatm = {
	.tm_year = vuosi-1900,
	.tm_mon  = 0,
	.tm_mday = 1+päivä,
    };
    time_t kohdeaika = mktime(&aikatm);
    return (kohdeaika - aika0) / 86400;
}

#define pisteen_summa(i) (i)
#define pisteen_jakaja(i) (-1)
double laske_piste(const struct tiedot* restrict tiedot, int i) {
    static double jakaja, summa;
    if(i == pisteen_jakaja(i))
	return jakaja;
    jakaja = summa = 0;
    double ala = pintaalat[i/lonpit];
    int vuosia = 0;
    for(int v=tiedot->v0; v<tiedot->v1; v++) {
	if(luokenum==ikir_e && tiedot->ikir[v*tiedot->res+i] != tiedot->luokka)
	    continue;
	int alku  = montako_päivää(tiedot->aika0, tiedot->vuodet[v], tiedot->alut [v*tiedot->res + i]),
	    loppu = montako_päivää(tiedot->aika0, tiedot->vuodet[v], tiedot->loput[v*tiedot->res + i]);
	if(alku == VIRHE || loppu == VIRHE)
	    continue;
	vuosia++;
	for(int t=alku; t<loppu; t++)
	    summa += tiedot->vuo[t*tiedot->res+i] * ala;
	jakaja += ala * (loppu-alku);
    }
    if(!vuosia)
	return epäluku;
    jakaja *=      tiedot->jakajan_kerroin(tiedot, i) / vuosia;
    return summa * tiedot-> summan_kerroin(tiedot, i) / vuosia;
}

void laske(const struct tiedot* restrict tiedot, struct tulos* tulos) {
    tulos->summat  = malloc(tiedot->res*sizeof(double)*3);
    tulos->jakajat = tulos->summat  + tiedot->res;
    tulos->alat    = tulos->jakajat + tiedot->res;
    int n = 0;
    tulos->sum1 = tulos->jak1 = tulos->lat = 0;

    for(int i=0; i<tiedot->res; i++) {
	if(!tiedot->alue[i])
	    continue;
	tulos->summat[n] = laske_piste(tiedot, pisteen_summa(i));
	if(on_epäluku(tulos->summat[n]))
	    continue;
	tulos->sum1 += tulos->summat[n];
	tulos->jak1 += (tulos->jakajat[n] = laske_piste(tiedot, pisteen_jakaja(i)));
	tulos->lat  += Lat(i) * tulos->jakajat[n];
	tulos->alat[n] = pintaalat[i/lonpit] * tiedot->jakajan_kerroin(tiedot, i);
	n++;
    }
    tulos->pisteitä = n;
    if(tulos->sum1 == 0)
	asm("int $3");
    if(tulos->sum1 * 86400 * 16.0416 * 1e-6 > 1e5)
	asm("int $3");
}

void vapauta_tulos(struct tulos* tulos) {
    free(tulos->summat);
}

double _summan_kerroin_wetl(const struct tiedot* restrict wt, int i) {
    return wt->wet[i] / wt->WET[i];
}
double _jakajan_kerroin_wetl(const struct tiedot* restrict wt, int i) {
    return wt->wet[i];
}
double _jakajan_kerroin_kost(const struct tiedot* restrict wt, int i) {
    return wt->WET[i];
}
double _palauta_1() { return 1; }

void* _lue_köpp() {
    int fd;
    struct stat st;
    if((fd = open("köppenmaski.txt", O_RDONLY)) < 0)
	err(1, "open köppenmaski.txt");
    fstat(fd, &st);
    char* luok = malloc(st.st_size);
    if(read(fd, luok, st.st_size) < 0)
	err(1, "read köppen");
    close(fd);
    for(int i=0; i<st.st_size; i++)
	luok[i] -= '1'; // '1' -> 0 jne.
    luoknimet = (typeof(luoknimet))&köppnimet;
    luokkia = sizeof(köppnimet)/sizeof(*köppnimet);
    return luok;
}
void* _lue_ikir() {
    nct_readm_nc(set, "./ikirdata.nc");
    nct_var* var = nct_get_var(&set, "luokka");
    char* ret = var->data;
    var->not_freeable = 1;
    var = nct_get_var(&set, "vuosi");
    ikirvuosi0 = nct_get_integer(var, 0);
    ikirvuosia = var->len;
    nct_free1(&set);
    luoknimet = (typeof(luoknimet))&ikirnimet;
    luokkia = sizeof(ikirnimet)/sizeof(*ikirnimet);
    return ret;
}
void* _lue_wetl() {
    nct_set* luok_vs = nct_read_ncf("./BAWLD1x1.nc", nct_rlazy);
    int pit = sizeof(wetlnimet)/sizeof(*wetlnimet);
    for(int i=0; i<pit; i++)
	nct_loadg_as(luok_vs, wetlnimet[i], NC_DOUBLE);
    luoknimet = (typeof(luoknimet))&wetlnimet;
    luokkia = pit;
    return luok_vs;
}
void* _lue_totl() {
    luokkia = 1;
    luoknimet = (typeof(luoknimet))&totlnimet;
    return NULL;
}
void* lue_luokitus() {
    static void* (*funktio[])(void) = { [köpp_e]=_lue_köpp, [ikir_e]=_lue_ikir, [wetl_e]=_lue_wetl, [totl_e]=_lue_totl };
    return funktio[luokenum]();
}

#define nonwetl_flag (1<<0)
void rajaa_aluetta_kosteikon_perusteella(char* alue, const struct tiedot* restrict td, int flags) {
    double* mix;
    switch(alueenum) {
	case temperate_e:
	    mix = nct_read_from_nc_as("BAWLD1x1.nc", "wetland_prf", NC_DOUBLE);
	    for(int i=0; i<td->res; i++)
		alue[i] &= (0.03 < mix[i]/td->WET[i] && mix[i]/td->WET[i] < 0.97);
	    free(mix);
	    break;
	case nontemperate_e:
	    mix = nct_read_from_nc_as("BAWLD1x1.nc", "wetland_prf", NC_DOUBLE);
	    for(int i=0; i<td->res; i++)
		alue[i] &= !(0.03 < mix[i]/td->WET[i] && mix[i]/td->WET[i] < 0.97);
	    free(mix);
	    break;
	default:
	    break;
    }
    if(flags & nonwetl_flag)
	for(int i=0; i<td->res; i++)
	    alue[i] &= td->WET[i] < 0.05;
    else if(luokenum == wetl_e || kosteikko)
	for(int i=0; i<td->res; i++)
	    alue[i] &= td->WET[i] >= 0.05;
}

void aseta_alku_ja_loppu(struct tiedot* restrict td, nct_set* kauvset, int kausi) {
    if(kausi == whole_year_e) {
	int vuosia = td->v1 - td->v0;
	td->alut =  malloc(    td->res*vuosia*2*sizeof(short));
	td->loput = td->alut + td->res*vuosia;
	for(int i=td->v0; i<td->v1; i++) {
	    int karkaus = !(td->vuodet[i]%4) && (td->vuodet[i]%100 || !(td->vuodet[i]%400));
	    short* alk = td->alut  + i*td->res;
	    short* lop = td->loput + i*td->res;
	    for(int r=0; r<td->res; r++) {
		alk[r] = 0;
		lop[r] = 365+karkaus;
		lop[r] -= LOPUSTA_PUUTTUU*(i == vuosi1kaikki-td->vuodet[0]-1);
	    }
	}
	return;
    }
    char nimi[40];
    nct_var* apu;

    sprintf(nimi, "%s_start", kaudet[kausi]);
    apu = nct_get_var(kauvset, nimi);
    if(!apu->data)
	nct_load(apu);
    td->alut = apu->data;

    sprintf(nimi, "%s_end", kaudet[kausi]);
    apu = nct_get_var(kauvset, nimi);
    if(!apu->data)
	nct_load(apu);
    td->loput = apu->data;
}

void poista_alku_ja_loppu(struct tiedot* restrict td, int kausi) {
    if(kausi == whole_year_e)
	free(td->alut);
    td->alut = td->loput = NULL;
}

/* tekee saman kuin system(mkdir -p kansio) */
void mkdir_p(const char *restrict nimi, int mode) {
    char *restrict k1 = strdup(nimi);
    char *restrict k2 = malloc(strlen(k1)+2);
    *k2 = 0;
    char* str = strtok(k1, "/");
    do {
	sprintf(k2+strlen(k2), "%s/", str);
	assert(!mkdir(k2, mode) || errno == EEXIST);
    } while((str=strtok(NULL, "/")));
    free(k2);
    free(k1);
}

FILE* alusta_csv(int kausi) {
    char nimi[160];
    char* kansio = (alueenum==nontemperate_e? KANSIO"nontemperate" :
	            alueenum==temperate_e?    KANSIO"temperate" :
	            KANSIO);
    mkdir_p(kansio, 0755);
    sprintf(nimi, "%s/%svuo_%s_%s_k%i.csv", kansio,
	    luokitus_ulos[luokenum], vuolaji_ulos[vlnum], kaudet[kausi], kosteikko);
    FILE* f = fopen(nimi, "w");
    if(!f)
	err(1, "fopen %s", nimi);
    fprintf(f, "#%s", kaudet[kausi]);
    if(kosteikko)
	fprintf(f, " kosteikko");
    fprintf(f, "\n,Tg,nmol/s/m²,season_length,lat,N,σ²\n");
    return f;
}

#define buff_size 2048
/* Toisin kuin yllä, tässä kirjoitetaan muistiin ja lopussa koko pötkö viedään yhteen tiedostoon.
   Erillisiä tiedostoja tulisi liian paljon auki kerralla. */
int alusta_csv_vuosittain(const char* luoknimi, int var, int v0, int v1, char* buf) {
    FILE* f = fmemopen(buf, buff_size, "w+");
    extern const char* varnimet[];
    fprintf(f, "#%s_%s", varnimet[var], luoknimi);
    if(kosteikko)
	fprintf(f, "W");
    if(!vlnum)
	fprintf(f, "_priori");
    switch(alueenum) {
	case nontemperate_e:
	    fprintf(f, "_puhdas"); break;
	case temperate_e:
	    fprintf(f, "_sekoitus"); break;
	default:
	    break;
    }
    fprintf(f, "\n");
    for(; v0<v1; v0++)
	fprintf(f, ",%i", v0);
    fprintf(f, "\n");
    int ret = ftell(f);
    fclose(f);
    return ret;
}

#define vakiotulos const struct tulos* restrict

/* Painotettuna luokan pinta-alalla. */
double varianssi(vakiotulos tulos) {
    double avg = tulos->sum1 / tulos->jak1 * 1e9; // erotus² voi olla pieni ellei kerrota suurella
    double summa = 0;
    double jakaja = 0;
    for(int i=0; i<tulos->pisteitä; i++) {
	if(tulos->jakajat[i] == 0)
	    continue;
	double tämävuo = tulos->summat[i] / tulos->jakajat[i] * 1e9;
	summa += (avg - tämävuo) * (avg - tämävuo) * tulos->alat[i];
	jakaja += tulos->alat[i];
    }
    return summa / jakaja;
}

double Tg_fun   (vakiotulos tulos) { return tulos->sum1 * 86400 * 16.0416 * 1e-6; }
double vuo_fun  (vakiotulos tulos) { return tulos->sum1 / tulos->jak1 * 1e9; }
double osuus_fun(vakiotulos tulos) { return tulos->jak1 / koko_vuoden_jakaja; }

void kirjoita_csvhen(FILE* f, vakiotulos tulos, const char* luoknimi) {
    fprintf(f, "%s,%.4lf,%.5lf,%.4lf,%.4lf,%i,%.5lf\n", luoknimi,
	    tulos->sum1 * 86400 * 16.0416 * 1e-6, // Tg (km² -> m²) && (g -> Tg) = (1e3)² * 1e-12 = 1e-6
	    tulos->sum1 / tulos->jak1 * 1e9,      // nmol/s/m²
	    tulos->jak1 / koko_vuoden_jakaja,     // 1
	    tulos->lat / tulos->jak1,             // °
	    tulos->pisteitä,                      // 1
	    varianssi(tulos)                      // (nmol/s/m²)²
	   );
}

const char* muoto[] = {",%.5lf", ",%.5lf", ",%.6lf", ",%.6lf"};
double (*varfun[])(vakiotulos) = {Tg_fun, vuo_fun, osuus_fun, varianssi};
const char* varnimet[] = {"emissio", "vuo", "kausiosuus", "varianssi"};
int nvars = sizeof(muoto)/sizeof(*muoto);

void kirjoita_csvhen_vuosittain(char* buf[nvars], int sij[nvars], vakiotulos tulos) {
    for(int var=0; var<nvars; var++)
	sij[var] += sprintf(buf[var]+sij[var], muoto[var], varfun[var](tulos));
}

void tee_lajin_kaudet(struct tiedot* tiedot, const char* luoknimi, nct_set* kauvset, FILE** f) {
    jakajien_summa = 0;
    for(int kausi=0; kausi<kausia; kausi++) {
	aseta_alku_ja_loppu(tiedot, kauvset, kausi);
	struct tulos tulos;
	laske(tiedot, &tulos);
	if(!kausi)
	    koko_vuoden_jakaja = tulos.jak1;
	else
	    jakajien_summa += tulos.jak1;
	kirjoita_csvhen(f[kausi], &tulos, luoknimi);
	vapauta_tulos(&tulos);
	poista_alku_ja_loppu(tiedot, kausi);
    }
}

void tee_lajin_kaudet_vuosittain(struct tiedot* tiedot, nct_set* kauvset, char* buf[nvars], int sij[nvars]) {
    const char v00 = tiedot->v0;
    const char v10 = tiedot->v1;
    for(int kausi=0; kausi<kausia; kausi++) {
	tiedot->v0 = v00;
	tiedot->v1 = v10;
	aseta_alku_ja_loppu(tiedot, kauvset, kausi);

	for(int var=0; var<nvars; var++)
	    sij[var] += sprintf(buf[var]+sij[var], "%s", kaudet[kausi]);

	int vuosi1 = v10 - (kausi==thaw_e);
	for(tiedot->v0=v00; tiedot->v0<vuosi1; tiedot->v0++) {
	    struct tulos tulos;
	    tiedot->v1 = tiedot->v0+1;
	    laske(tiedot, &tulos);
	    if(!kausi)
		koko_vuoden_jakaja = tulos.jak1;
	    kirjoita_csvhen_vuosittain(buf, sij, &tulos);
	    vapauta_tulos(&tulos);
	}
	for(int i=0; i<nvars; i++)
	    buf[i][sij[i]++] = '\n';
	poista_alku_ja_loppu(tiedot, kausi);
    }
    tiedot->v0 = v00;
    tiedot->v1 = v10;
}

void vie_tiedostoksi(char* buf[][nvars], int sij[][nvars]) {
    char nimi[128];
    char* aluenimi = alueenum==temperate_e?"_lauhkea": alueenum==nontemperate_e?"_eilauhkea": "";
    const char* kansio = vlnum>1? KANSIO"vuosittain/antro": KANSIO"vuosittain";
    mkdir_p(kansio, 0755);
    sprintf(nimi, "%s/%s%s%s%s.csv", kansio,
	    luokitus_ulos[luokenum], kosteikko?"W":"", aluenimi, !vlnum?"_priori":"");
    int fd = open(nimi, O_WRONLY|O_CREAT|O_TRUNC, 0644);
    if(fd < 0)
	err(1, "open ${ulostulo}.csv");
    for(int j=0; j<luokkia; j++)
	for(int i=0; i<nvars; i++) {
	    if(write(fd, buf[j][i], sij[j][i]) != sij[j][i])
		warn("write");
	}
    close(fd);
}

int main(int argc, char** argv) {
    nct_set *aluevset, *kauvset, *vuovset, *bawvset;
    nct_var *maski;

    if(argumentit(argc, argv))
	return 1;

    void* luokitus = lue_luokitus();
    if(luokenum == wetl_e) {
	bawvset = luokitus;
	luokitus = NULL;
    }
    else
	bawvset = nct_read_ncf("BAWLD1x1.nc", nct_rlazy);

    aluevset = nct_read_nc("aluemaski.nc");
    vuovset  = nct_read_ncf(vlnum>1? "../vuo_2212/flux1x1_.nc": "flux1x1.nc", nct_rlazy|nct_ratt);
    kauvset  = nct_read_ncf("kausien_päivät_int16.nc", nct_rlazy);
    maski    = nct_firstvar(aluevset);
    nct_loadg(vuovset, "time");

    lat0 = nct_get_floating(nct_get_var(aluevset, "lat"), 0);
    
    struct tiedot tiedot = {
	.vuo    = nct_loadg_as(vuovset, vuolaji_sisään[vlnum], NC_DOUBLE)->data,
	.WET    = nct_loadg_as(bawvset, "wetland",             NC_DOUBLE)->data,
	.vuodet = nct_loadg_as(kauvset, "vuosi",               NC_INT)->data,  
	.alue   = maski->data,
	.res    = maski->len,
	.aika0  = nct_mktime0g(vuovset, "time", NULL).a.t,
	.summan_kerroin  = _palauta_1,
	.jakajan_kerroin = kosteikko? _jakajan_kerroin_kost: _palauta_1,
    };
    tiedot.v0 = vuosi0_ - tiedot.vuodet[0];
    vuosi1kaikki = nct_get_integer_last(nct_get_var(kauvset, "vuosi"), 1) + 1;
    tiedot.v1 = (vuosittain? vuosi1kaikki: vuosi1_) - tiedot.vuodet[0];
    rajaa_aluetta_kosteikon_perusteella(tiedot.alue, &tiedot, 0);

    if(luokenum == ikir_e) {
	/* Siirretään ikiroudan alkukohta olemaan samaa vuotta kuin muun syötteen alku. */
	int siirto = tiedot.vuodet[0] - ikirvuosi0;
	ikirvuosia -= siirto;
	memmove(luokitus, luokitus+siirto*tiedot.res, ikirvuosia*tiedot.res);
	tiedot.ikir = luokitus;
	if (ikirvuosia < tiedot.v1) {
	    puts("Varoitus: jatketaan ikiroutaa");
	    luokitus = realloc(luokitus, tiedot.res*tiedot.v1);
	    if(!luokitus)
		err(1, "realloc luokitus %i", tiedot.res*(tiedot.v1-tiedot.v0));
	    /* Kopioidaan joka silmukassa yksi vuosi lisää loppuun. */
	    for(int v=ikirvuosia; v<tiedot.v1; v++)
		memcpy(luokitus+v*tiedot.res, luokitus+(v-1)*tiedot.res, tiedot.res);
	    tiedot.ikir = luokitus;
	}
    }

    FILE* f[kausia];             // ei vuosittain
    char* buf[luokkia+1][nvars]; // vuosittain
    char* bufbuf = NULL;         // vuosittain
    int sij[luokkia+1][nvars];   // vuosittain

    if(vuosittain)
	assert((bufbuf = malloc((luokkia+1)*nvars*buff_size)));
    else
	for(int i=0; i<kausia; i++)
	    f[i] = alusta_csv(i);

    char* toinen_aluemaski = NULL;

    for(int laji=0; laji<luokkia; laji++) {
	switch(luokenum) {
	    case wetl_e:
		tiedot.wet = nct_get_var(bawvset, wetlnimet[laji])->data;
		tiedot.summan_kerroin = _summan_kerroin_wetl;
		tiedot.jakajan_kerroin = _jakajan_kerroin_wetl;
		break;
	    case köpp_e:
		if(!toinen_aluemaski)
		    toinen_aluemaski = malloc(tiedot.res);
		tiedot.alue = toinen_aluemaski;
		for(int i=0; i<tiedot.res; i++)
		    tiedot.alue[i] = ((char*)maski->data)[i] && ((char*)luokitus)[i]==laji;
		break;
	    case ikir_e:
		tiedot.luokka = laji;
		break;
	    case totl_e:
		break;
	}
	if(vuosittain) {
	    for(int i=0; i<nvars; i++) {
		buf[laji][i] = bufbuf + buff_size*nvars*laji + buff_size*i;
		sij[laji][i] = alusta_csv_vuosittain((*luoknimet)[laji], i, vuosi0_, vuosi1kaikki, buf[laji][i]);
	    }
	    tee_lajin_kaudet_vuosittain(&tiedot, kauvset, buf[laji], sij[laji]);
	}
	else
	    tee_lajin_kaudet(&tiedot, (*luoknimet)[laji], kauvset, f);
    }
    if(luokenum == wetl_e) {
	tiedot.alue = nct_read_from_nc("aluemaski.nc", "maski");
	rajaa_aluetta_kosteikon_perusteella(tiedot.alue, &tiedot, nonwetl_flag);
	tiedot.summan_kerroin = _palauta_1;
	tiedot.jakajan_kerroin = _palauta_1;
	if(vuosittain) {
	    for(int i=0; i<nvars; i++) {
		buf[luokkia][i] = bufbuf + buff_size*nvars*luokkia + buff_size*i;
		sij[luokkia][i] = alusta_csv_vuosittain("non-wetland", i, tiedot.vuodet[0], vuosi1kaikki, buf[luokkia][i]);
	    }
	    tee_lajin_kaudet_vuosittain(&tiedot, kauvset, buf[luokkia], sij[luokkia]);
	}
	else
	    tee_lajin_kaudet(&tiedot, "non-wetland", kauvset, f);
	free(tiedot.alue);
    }

    if(vuosittain)
	vie_tiedostoksi(buf, sij);
    else
	for(int i=0; i<kausia; i++)
	    fclose(f[i]);

    free(luokitus);
    free(toinen_aluemaski);
    free(bufbuf);
    nct_free(aluevset, bawvset, vuovset, kauvset);
}

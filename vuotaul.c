#include <nctietue2.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <assert.h>
#include <err.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <math.h>

const double r2 = 6362.1320*6362.1320; // km, jotta luvut ovat maltillisempia
#define PINTAALA(lat, hila) ((hila) * r2 * (sin((lat)+0.5*(hila)) - sin((lat)-0.5*(hila))))
#define ASTE 0.017453293
#define Lat(i) (lat0+(i)/360)
#define Pintaala(i) PINTAALA(Lat(i)*ASTE, ASTE)

const char* ikirnimet[]      = {"nonpermafrost", "sporadic", "discontinuous", "continuous"};
const char* köppnimet[]      = {"D.b", "D.c", "D.d", "ET"};
const char* wetlnimet[]      = {"wetland", "bog", "fen", "marsh", "permafrost_bog", "tundra_wetland"};
enum                           {wetland_e, bog_e, fen_e, marsh_e, permafrost_bog_e, tundra_wetland_e};
const char* kaudet[]         = {"whole_year", "summer", "freezing", "winter"};
enum                           {whole_year_e, summer_e, freezing_e, winter_e};
const char* luokitus_ulos[]  = {"köppen", "ikir", "wetland"};
enum luokitus_e                {köpp_e,   ikir_e, wetl_e};
const char* pripost_sisään[] = {"flux_bio_prior", "flux_bio_posterior"};
const char* pripost_ulos[]   = {"pri", "post"};
#define kausia 4
#define wraja 0.05

enum alue_e     {kokoalue_e, pure_e, mixed_e} alueenum;
enum luokitus_e luokenum;
int ppnum=1, kosteikko, ikirvuosi0, ikirvuosia, luokkia;
typeof(&ikirnimet) luoknimet;
double lat0, koko_vuoden_jakaja;

struct tiedot {
    double *vuo, *WET;
    float *alut, *loput;
    int *vuodet, vuosia, res;
    time_t aika0;
    char* alue;
    double (*summan_kerroin)(const struct tiedot* restrict, int);
    double (*jakajan_kerroin)(const struct tiedot* restrict, int);
    /* wetland */
    double* wet;
};

struct tulos {
    double *summat, *jakajat, *alat, lat, jak1, sum1;
    int pisteitä;
};

#define epäluku 1e24
#define on_epäluku(f) (f>1e23)

int argumentit(int argc, char** argv) {
    for(int i=1; i<argc; i++)
	if(!strcmp(argv[i], "köpp"))
	    luokenum = köpp_e;
	else if (!strcmp(argv[i], "ikir"))
	    luokenum = ikir_e;
	else if (!strcmp(argv[i], "wetl"))
	    luokenum = wetl_e;
	else if(!strcmp(argv[i], "pri"))
	    ppnum = 0;
	else if(!strcmp(argv[i], "post"))
	    ppnum = 1;
	else if(!strcmp(argv[i], "kosteikkoalue"))
	    kosteikko = 1;
	else if(!strcmp(argv[i], "mixed"))
	    alueenum = mixed_e;
	else if(!strcmp(argv[i], "pure"))
	    alueenum = pure_e;
	else {
	    printf("\033[91mVirheellinen argumentti\033[0m %s\n", argv[i]);
	    return 1;
	}
    return 0;
}

#define VIRHE -1234567
int montako_päivää(time_t aika0, int vuosi, float fpäivä) {
    if(fpäivä != fpäivä)
	return VIRHE;
    struct tm aikatm = {
	.tm_year = vuosi-1900,
	.tm_mon  = 0,
	.tm_mday = 1+(int)fpäivä,
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
    double ala = Pintaala(i);
    int vuosia = 0;
    for(int v=0; v<tiedot->vuosia; v++) {
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
    jakaja *= tiedot->jakajan_kerroin(tiedot, i) / vuosia;
    return summa * tiedot->summan_kerroin(tiedot, i) / vuosia;
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
	tulos->alat[n] = Pintaala(i);
	n++;
    }
    tulos->pisteitä = n;
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
    nct_vset *vset = nct_read_ncfile("./ikirdata.nc");
    int varid = nct_get_varid(vset, "luokka");
    char* ret = vset->vars[varid]->data;
    vset->vars[varid]->nonfreeable_data = 1;
    nct_var* var = &NCTVAR(*vset, "vuosi");
    ikirvuosi0 = ((short*)var->data)[0]; // ei ole väliä, onko short vai int
    ikirvuosia = nct_get_varlen(var);
    nct_free_vset(vset);
    luoknimet = (typeof(luoknimet))&ikirnimet;
    luokkia = sizeof(ikirnimet)/sizeof(*ikirnimet);
    return ret;
}
void* _lue_wetl() {
    nct_vset* luok_vs = nct_read_ncfile_info("./BAWLD1x1.nc");
    int pit = sizeof(wetlnimet)/sizeof(*wetlnimet);
    for(int i=0; i<pit; i++) {
	int varid = nct_get_varid(luok_vs, wetlnimet[i]);
	nct_load_var_with(luok_vs->vars[varid], varid, nc_get_var_double, sizeof(double));
    }
    luoknimet = (typeof(luoknimet))&wetlnimet;
    luokkia = pit;
    return luok_vs;
}
void* lue_luokitus() {
    static void* (*funktio[])(void) = { [köpp_e]=_lue_köpp, [ikir_e]=_lue_ikir, [wetl_e]=_lue_wetl, };
    return funktio[luokenum]();
}

void rajaa_aluetta(char* alue, const struct tiedot* restrict td) {
    if(luokenum != wetl_e && !kosteikko)
	return;
    for(int i=0; i<td->res; i++)
	alue[i] &= td->WET[i] >= 0.05;
    double* mix;
    switch(alueenum) {
	case mixed_e:
	    mix = nct_read_from_ncfile("BAWLD1x1.nc", "wetland_prf", nc_get_var_double, sizeof(double));
	    for(int i=0; i<td->res; i++)
		alue[i] &= (0.03 < mix[i] && mix[i] < 0.97);
	    free(mix);
	    break;
	case pure_e:
	    mix = nct_read_from_ncfile("BAWLD1x1.nc", "wetland_prf", nc_get_var_double, sizeof(double));
	    for(int i=0; i<td->res; i++)
		alue[i] &= !(0.03 < mix[i] && mix[i] < 0.97);
	    free(mix);
	    break;
	default:
	    break;
    }
}

void aseta_alku_ja_loppu(struct tiedot* restrict td, nct_vset* kauvset, int kausi) {
    if(kausi == whole_year_e) {
	td->alut =  malloc(    td->res*td->vuosia*2*sizeof(float));
	td->loput = td->alut + td->res*td->vuosia;
	for(int i=0; i<td->vuosia; i++) {
	    int karkaus = !(td->vuodet[i]%4) && (td->vuodet[i]%100 || !(td->vuodet[i]%400));
	    float* alk = td->alut  + i*td->res;
	    float* lop = td->loput + i*td->res;
	    for(int r=0; r<td->res; r++) {
		alk[r] = 0;
		lop[r] = 365+karkaus;
	    }
	}
	return;
    }
    char nimi[40];
    nct_var* apu;

    sprintf(nimi, "%s_start", kaudet[kausi]);
    apu = nct_get_var(kauvset, nimi);
    if(!apu->data)
	nct_load_var_with(apu, -1, nc_get_var_float, sizeof(float));
    td->alut  = apu->data;

    sprintf(nimi, "%s_end", kaudet[kausi]);
    apu = nct_get_var(kauvset, nimi);
    if(!apu->data)
	nct_load_var_with(apu, -1, nc_get_var_float, sizeof(float));
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
    char* kansio = (alueenum==pure_e?  "vuotaulukot/kahtia" :
	            alueenum==mixed_e? "vuotaulukot/kahtia_keskiosa" :
	            "vuotaulukot");
    mkdir_p(kansio, 0755);
    sprintf(nimi, "%s/%svuo_%s_%s_k%i.csv", kansio,
	    luokitus_ulos[luokenum], pripost_ulos[ppnum], kaudet[kausi], kosteikko);
    FILE* f = fopen(nimi, "w");
    if(!f)
	err(1, "fopen %s", nimi);
    fprintf(f, "#%s", kaudet[kausi]);
    if(kosteikko)
	fprintf(f, " kosteikko");
    fprintf(f, "\n,Tg,nmol/s/m²,season_length,lat,N,σ²\n");
    return f;
}

double varianssi(struct tulos* restrict tulos) {
    double avg = tulos->sum1 / tulos->jak1 * 1e9; // erotus² voi olla pieni ellei kerrota 1e9:llä
    double summa = 0;
    double jakaja = 0;
    for(int i=0; i<tulos->pisteitä; i++) {
	double tämä = tulos->summat[i] / tulos->jakajat[i] * 1e9;
	if(!(tämä==tämä))
	    continue;
	summa += (avg - tämä) * (avg - tämä) * tulos->alat[i];
	jakaja += tulos->alat[i];
    }
    return summa / jakaja;
}

void kirjoita_csvhen(FILE* f, struct tulos* tulos, int luokka) {
    fprintf(f, "%s,%.4lf,%.5lf,%.4lf,%.4lf,%i,%.5f\n", (*luoknimet)[luokka],
	    tulos->sum1 * 86400 * 16.0416 * 1e-6, // Tg (km² -> m²) && (g -> Tg) = (1e3)² * 1e-12 = 1e-6
	    tulos->sum1 / tulos->jak1 * 1e9,      // nmol/s/m²
	    tulos->jak1 / koko_vuoden_jakaja,     // 1
	    tulos->lat / tulos->jak1,             // °
	    tulos->pisteitä,                      // 1
	    varianssi(tulos)                      // (nmol/s/m²)²
	   );
}

int main(int argc, char** argv) {
    nct_vset *aluevset, *kauvset, *vuovset, *bawvset;
    nct_var *maski, *vuoaika;

    if(argumentit(argc, argv))
	return 1;

    void* luokitus = lue_luokitus();
    if(luokenum == wetl_e) {
	bawvset = luokitus;
	luokitus = NULL;
    }
    else
	bawvset = nct_read_ncfile_info("BAWLD1x1.nc");

    aluevset = nct_read_ncfile("aluemaski.nc");
    vuovset  = nct_read_ncfile_info("flux1x1.nc");
    kauvset  = nct_read_ncfile_info("kausien_päivät.nc");
    maski    = nct_next_truevar(aluevset->vars[0], 0);
    vuoaika  = nct_get_var(vuovset, "time");
    nct_load_var(vuoaika, -1);

    lat0 = nct_get_floating(nct_get_var(aluevset, "lat"), 0);
    
    struct tiedot tiedot = {
	.vuo    = nct_load_data_with(vuovset, pripost_sisään[ppnum], nc_get_var_double, sizeof(double)),
	.WET    = nct_load_data_with(bawvset, "wetland",             nc_get_var_double, sizeof(double)),
	.vuodet = nct_load_data_with(kauvset, "vuosi",               nc_get_var_int,    sizeof(int)),
	.alue   = maski->data,
	.res    = nct_get_varlen(maski),
	.aika0  = nct_mktime0(vuoaika, NULL).a.t,
	.summan_kerroin  = _palauta_1,
	.jakajan_kerroin = kosteikko? _jakajan_kerroin_kost: _palauta_1,
    };
    tiedot.vuosia = 2021 - tiedot.vuodet[0];
    rajaa_aluetta(tiedot.alue, &tiedot);

    FILE* f[kausia];
    for(int i=0; i<kausia; i++)
	f[i] = alusta_csv(i);

    char* toinen_aluemaski = NULL;

    for(int laji=0; laji<luokkia; laji++) {
	if(luokenum == wetl_e) {
	    tiedot.wet = nct_get_var(bawvset, wetlnimet[laji])->data;
	    tiedot.summan_kerroin = _summan_kerroin_wetl;
	    tiedot.jakajan_kerroin = _jakajan_kerroin_wetl;
	}
	else {
	    if(!toinen_aluemaski)
		toinen_aluemaski = malloc(tiedot.res);
	    tiedot.alue = toinen_aluemaski;
	    for(int i=0; i<tiedot.res; i++)
		tiedot.alue[i] = ((char*)maski->data)[i] && ((char*)luokitus)[i]==laji;
	}

	for(int kausi=0; kausi<kausia; kausi++) {
	    aseta_alku_ja_loppu(&tiedot, kauvset, kausi);
	    struct tulos tulos;
	    laske(&tiedot, &tulos);
	    if(!kausi)
		koko_vuoden_jakaja = tulos.jak1;
	    kirjoita_csvhen(f[kausi], &tulos, laji);
	    vapauta_tulos(&tulos);
	    poista_alku_ja_loppu(&tiedot, kausi);
	}
    }

    for(int i=0; i<kausia; i++)
	fclose(f[i]);

    free(luokitus);
    free(toinen_aluemaski);
    nct_free_vset(aluevset);
    nct_free_vset(bawvset);
    nct_free_vset(vuovset);
    nct_free_vset(kauvset);
}

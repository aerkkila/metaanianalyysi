#include <nctietue3.h>
#include <stdlib.h>
#include <string.h>
#include "pintaalat.h"

int lonpit;
#define pintaala(i) (pintaalat[i/lonpit])

#define VIRHE -1234567
int montako_päivää(time_t aika0, int vuosi, short päivä) {
    if(päivä == 999)
	return VIRHE;
    struct tm aikatm = {
	.tm_year = vuosi-1900,
	.tm_mon  = 0,
	.tm_mday = 1+päivä,
    };
    time_t kohdeaika = mktime(&aikatm);
    return (kohdeaika - aika0) / 86400;
}

struct tiedot {
    double *vuo, *WET, *wet;
    short *alut, *loput;
    int *vuodet, vuosia, res;
    time_t aika0;
    char* alue;
};

double yksi_piste(const struct tiedot* restrict tiedot, int i) {
    static double jakaja, summa;
    if(i<0)
	return jakaja;
    jakaja = summa = 0;
    double ala = pintaala(i);
    for(int v=0; v<tiedot->vuosia; v++) {
	int alku  = montako_päivää(tiedot->aika0, tiedot->vuodet[v], tiedot->alut [v*tiedot->res + i]),
	    loppu = montako_päivää(tiedot->aika0, tiedot->vuodet[v], tiedot->loput[v*tiedot->res + i]);
	if(alku == VIRHE || loppu == VIRHE)
	    continue;
	for(int t=alku; t<loppu; t++)
	    summa += tiedot->vuo[t*tiedot->res+i] / tiedot->WET[i] * tiedot->wet[i] * ala;
	jakaja += tiedot->wet[i] * (loppu-alku) * ala;
    }
    return summa * 1e9;
}

double summa_ja_jakaja(const struct tiedot* restrict tiedot, int kumpi) {
    static double summa, jakaja;
    if(kumpi)
	return jakaja;
    summa = jakaja = 0;
    for(int i=0; i<tiedot->res; i++) {
	if(!tiedot->alue[i])
	    continue;
	double ala = pintaala(i);
	for(int v=0; v<tiedot->vuosia; v++) {
	    int alku  = montako_päivää(tiedot->aika0, tiedot->vuodet[v], tiedot->alut [v*tiedot->res + i]),
		loppu = montako_päivää(tiedot->aika0, tiedot->vuodet[v], tiedot->loput[v*tiedot->res + i]);
	    if(alku == VIRHE || loppu == VIRHE)
		continue;
	    for(int t=alku; t<loppu; t++)
		summa += tiedot->vuo[t*tiedot->res+i] / tiedot->WET[i] * tiedot->wet[i] * ala;
	    jakaja += tiedot->wet[i] * (loppu-alku) * ala;
	}
    }
    return summa*1e9;
}

char* luo_alue(const double* prfwet, const double* WET, char* alue, int xyres) {
    for(int i=0; i<xyres; i++) {
	double prf = prfwet[i] / WET[i];
	alue[i] = alue[i] && WET[i] >= 0.05 && prf < 0.97 && prf > 0.03;
    }
    return alue;
}

char* luo_koko_alue(const double* WET, char* alue, int xyres) {
    for(int i=0; i<xyres; i++)
	alue[i] = alue[i] && WET[i] >= 0.05;
    return alue;
}

const char* luokat[] = {"bog", "fen", "marsh", "permafrost_bog", "tundra_wetland"};
const int luokkia = sizeof(luokat)/sizeof(char*);

struct Arg {
    struct tiedot tiedot;
    nct_set *tallenn, *bawvset;
    int j;
};
int arg_luettu;

void* tee_luokka(void* varg) {
    struct Arg arg = *(struct Arg*)varg;
    arg_luettu = 1;
    arg.tiedot.wet = nct_loadg_as(arg.bawvset, luokat[arg.j], NC_DOUBLE)->data;
    const struct tiedot* restrict tiedot = &arg.tiedot;
    double summa  = summa_ja_jakaja(tiedot, 0);
    double jakaja = summa_ja_jakaja(tiedot, 1);
    double keskivuo = summa / jakaja;
    float *uusidata = malloc(tiedot->res*sizeof(float));

    for(int i=0; i<tiedot->res; i++) {
	if(!tiedot->alue[i]) {
	    uusidata[i] = 0.0f / 0.0f;
	    continue; }
	double summa1  = yksi_piste(tiedot, i);
	double jakaja1 = yksi_piste(tiedot, -1);
	uusidata[i] = (keskivuo - (summa-summa1) / (jakaja-jakaja1)) / pintaala(i) * 1e9;
    }

    return uusidata;
}

int main(int argc, char** argv) {
    int kokoalue = argc < 2 || strcmp(argv[1], "--lauhkea");
    nct_readflags = nct_rlazy;
    nct_set *aluevset = nct_read_ncf("aluemaski.nc", 0),
	    *bawvset  = nct_read_nc("BAWLD1x1.nc"),
	    *vuovset  = nct_read_ncf("flux1x1.nc", nct_rlazy|nct_ratt),
	    *kauvset  = nct_read_nc("kausien_päivät_int16.nc");

    nct_var* maski = nct_firstvar(aluevset);
    double* prfwet = nct_loadg_as(bawvset, "wetland_prf", NC_DOUBLE)->data;
    int xyres = maski->len;
    
    struct tiedot tiedot = {
	.vuo    = nct_loadg_as(vuovset, "flux_bio_posterior", NC_DOUBLE)->data,
	.alut   = nct_loadg_as(kauvset, "summer_start",       NC_SHORT )->data,
	.loput  = nct_loadg_as(kauvset, "summer_end",         NC_SHORT )->data,
	.WET    = nct_loadg_as(bawvset, "wetland",            NC_DOUBLE)->data,
	.vuodet = nct_loadg_as(kauvset, "vuosi",              NC_INT   )->data,
	.res    = xyres,
	.aika0  = nct_mktime0g(vuovset, "time", NULL).a.t,
    };
    tiedot.vuosia = 2021 - tiedot.vuodet[0];
    tiedot.alue = kokoalue?
	luo_koko_alue(   tiedot.WET, maski->data, xyres):
	luo_alue(prfwet, tiedot.WET, maski->data, xyres);

    nct_set tallenn = {0};
    nct_copy_var(&tallenn, nct_get_var(aluevset, "lat"), 1);
    nct_copy_var(&tallenn, nct_get_var(aluevset, "lon"), 1);
    lonpit = tallenn.vars[1]->len;
    
    for(int j=0; j<luokkia; j++) {
	struct Arg arg = {
	    .tiedot  = tiedot,
	    .tallenn = &tallenn,
	    .bawvset = bawvset,
	    .j       = j,
	};
	void* data = tee_luokka(&arg);
	int varid[] = {0,1};
	nct_add_var(&tallenn, data, NC_FLOAT, (char*)luokat[j], 2, varid);
    }

    nct_write_nc(&tallenn, "vuosijainnit.nc");

    nct_free(&tallenn, aluevset, bawvset, vuovset, kauvset);
}

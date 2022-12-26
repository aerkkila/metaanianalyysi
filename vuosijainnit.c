#include <nctietue2.h>
#include <stdlib.h>

#include <math.h>
const double r2 = 6362132.0*6362132.0;
#define PINTAALA(lat, hila) ((hila) * r2 * (sin((lat)+0.5*(hila)) - sin((lat)-0.5*(hila))))
#define ASTE 0.017453293
double *lat;
int lonpit;
double pintaala(int i) {
    return PINTAALA(lat[i/lonpit]*ASTE, ASTE);
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

struct tiedot {
    double *vuo, *alut, *loput, *WET, *wet;
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

const char* luokat[] = {"bog", "fen", "marsh", "permafrost_bog", "tundra_wetland"};
const int luokkia = sizeof(luokat)/sizeof(char*);

struct Arg {
    struct tiedot tiedot;
    nct_vset *tallenn, *bawvset;
    int j;
};
int arg_luettu;

void* tee_luokka(void* varg) {
    struct Arg arg = *(struct Arg*)varg;
    arg_luettu = 1;
    arg.tiedot.wet = nct_load_data_with(arg.bawvset, luokat[arg.j], nc_get_var_double, sizeof(double));
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

int main() {
    nct_vset *aluevset = nct_read_ncfile("aluemaski.nc"),
	     *bawvset  = nct_read_ncfile_info("BAWLD1x1.nc"),
	     *vuovset  = nct_read_ncfile_info("flux1x1.nc"),
	     *kauvset  = nct_read_ncfile_info("kausien_päivät.nc");

    nct_var* maski = nct_next_truevar(aluevset->vars[0], 0);
    double* prfwet = nct_load_data_with(bawvset, "wetland_prf", nc_get_var_double, sizeof(double));
    int xyres = nct_get_varlen(maski);
    
    struct tiedot tiedot = {
	.vuo    = nct_load_data_with(vuovset, "flux_bio_posterior", nc_get_var_double, sizeof(double)),
	.alut   = nct_load_data_with(kauvset, "summer_start",       nc_get_var_double, sizeof(double)),
	.loput  = nct_load_data_with(kauvset, "summer_end",         nc_get_var_double, sizeof(double)),
	.WET    = nct_load_data_with(bawvset, "wetland",            nc_get_var_double, sizeof(double)),
	.vuodet = nct_load_data_with(kauvset, "vuosi",              nc_get_var_int,    sizeof(int)),
	.res    = xyres,
	.aika0  = nct_mktime0(nct_get_var(vuovset, "time"), NULL).a.t,
    };
    tiedot.vuosia = 2021 - tiedot.vuodet[0];
    tiedot.alue   = luo_alue(prfwet, tiedot.WET, maski->data, xyres);

    nct_vset tallenn = {0};
    nct_copy_var(&tallenn, nct_get_var(aluevset, "lat"), 1);
    nct_copy_var(&tallenn, nct_get_var(aluevset, "lon"), 1);
    lat = tallenn.vars[0]->data;
    lonpit = nct_get_varlen(tallenn.vars[1]);
    
    for(int j=0; j<luokkia-1; j++) {
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
    struct Arg arg = {
	.tiedot  = tiedot,
	.tallenn = &tallenn,
	.bawvset = bawvset,
	.j       = luokkia-1,
    };
    void* loppudata = tee_luokka(&arg);
    int varid[] = {0,1};
    nct_add_var(&tallenn, loppudata, NC_FLOAT, (char*)luokat[luokkia-1], 2, varid);

    nct_write_ncfile(&tallenn, "vuosijainnit.nc");

    nct_free_vset(&tallenn);
    nct_free_vset(aluevset);
    nct_free_vset(bawvset);
    nct_free_vset(vuovset);
    nct_free_vset(kauvset);
}

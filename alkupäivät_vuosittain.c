#include <nctietue2.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdarg.h>
#include <fcntl.h>
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

const char* ikirnimet[] = {"nonpermafrost", "sporadic", "discontinuous", "continuous"};
const char* koppnimet[] = {"D.b", "D.c", "D.d", "ET"};
const char* wetlnimet[] = {"wetland", "bog", "fen", "marsh", "tundra_wetland", "permafrost_bog"};
const char* kaudet[]    = {"whole_year", "summer", "freezing", "winter"};
enum                      {whole_year_e, summer_e, freezing_e, winter_e};
enum                      {kopp_e, ikir_e, wetl_e} luokenum;
const char*** luoknimet;
const char* kansio = "kausijakaumadata";
#define kausia 4
#define wraja 0.05

static nct_vset *luok_vs;
static char  *restrict luok_c;
static double *restrict alat;
static int ikirvuosi0, ikirvuosia, vuosi0, vuosi1;

struct laskenta {
    const char* lajinimi;
    float* kausiptr;
    int kausi, lajinum, vuosi;
    /* *.bin-tiedostot */
    float *cdf, *päivät;
    int pisteitä;
    /* *.csv-tiedostot */
    double *päiv0sum, *n_päiv0; // painotettuina pinta-alalla
};

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

void päivä_keskiarvoon(struct laskenta* args, double ala, int kausi, float päivä) {
    args->päiv0sum[kausia*args->vuosi + kausi] += päivä * ala;
    args->n_päiv0 [kausia*args->vuosi + kausi] += ala;

    int pisteitä = args->pisteitä++;
    args->päivät[pisteitä] = päivä;
    args->cdf[pisteitä] = ala;
}

void päivä_keskiarvoon_w(struct laskenta* args, double ala, int kausi, float päivä, double paino) {
    args->päiv0sum[kausia*args->vuosi + kausi] += päivä * ala * paino;
    args->n_päiv0 [kausia*args->vuosi + kausi] += ala * paino;

    int pisteitä = args->pisteitä++;
    args->päivät[pisteitä] = päivä;
    args->cdf[pisteitä] = ala*paino;
}

void täytä_kosteikkodata(struct laskenta* args) {
    double *restrict osuus0ptr = NCTVAR(*luok_vs, "wetland").data;
    double *restrict osuus1ptr = NCTVAR(*luok_vs, wetlnimet[args->lajinum]).data;
    for (int r=0; r<resol; r++) {
	if (osuus0ptr[r] < wraja) continue;
	float päivä = args->kausiptr[args->vuosi*resol+r];
	if (päivä != päivä) continue;
	päivä_keskiarvoon_w(args, alat[r/360], args->kausi, päivä, osuus1ptr[r]);
    }
}

void täytä_köppendata(struct laskenta* args) {
    for (int r=0; r<resol; r++) {
	if (luok_c[r] != args->lajinum) continue;
	float päivä = args->kausiptr[args->vuosi*resol+r];
	if (päivä != päivä) continue;
	päivä_keskiarvoon(args, alat[r/360], args->kausi, päivä);
    }
}

void täytä_ikirdata(struct laskenta* args) {
    int ikirv = vuosi0 + args->vuosi - ikirvuosi0;
    if (ikirv >= ikirvuosia)
	ikirv = ikirvuosia-1;
    for(int r=0; r<resol; r++) {
	if (luok_c[ikirv*resol+r] != args->lajinum) continue;
	float päivä = args->kausiptr[args->vuosi*resol+r];
	if (päivä != päivä) continue;
	päivä_keskiarvoon(args, alat[r/360], args->kausi, päivä);
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

#define Write(a,b,c) (write(a,b,c) != c)
void tallenna(struct laskenta* args, void* data, int kirjpit, int kausi) {
    int fd = open(aprintf("./%s/%s_%s.bin", kansio, args->lajinimi, kaudet[kausi]), O_WRONLY|O_CREAT, 0644);
    assert(fd>=0);
    if (
	    Write(fd, &kirjpit, 4) |
	    Write(fd, &vuosi0, 4)  |
	    Write(fd, data, kirjpit*(vuosi1-vuosi0)*4)
       )
	warn("write %s", aprintapu);
    close(fd);
}
#undef Write

float* laita_data(struct laskenta* args, float *kohde, int kirjpit, int kausi, int vuosi) {
    float* data = args->päivät;
    int    pit  = args->pisteitä;
    float* cdf  = pintaaloista_kertymäfunktio(data, args->cdf, pit);
    if(pit < kirjpit)
	printf("liian vähän dataa %i %s, %s, %i\n", pit, args->lajinimi, kaudet[kausi], vuosi);
    int ind = 0;
    for(int i=0; i<kirjpit; i++) {
	ind = binsearch(cdf, (float)i/kirjpit, ind, pit);
	kohde[i] = data[ind];
    }
    return kohde;
}

void laita_alkupäivä(struct laskenta* args) {
    FILE* f = fopen(aprintf("%s/alkupäivät_%s.csv", kansio, args->lajinimi), "w");
    fprintf(f, "#%s\n", args->lajinimi);
    for(int v=vuosi0; v<vuosi1; v++)
	fprintf(f, ",%i", v);
    fputc('\n', f);
    for(int kausi=1; kausi<kausia; kausi++) {
	fprintf(f, "%s", kaudet[kausi]);
	for(int v=0; v<vuosi1-vuosi0; v++) {
	    int tavg = args->päiv0sum[v*kausia+kausi] / args->n_päiv0[v*kausia+kausi];
	    fprintf(f, ",%i", tavg);
	}
	fputc('\n', f);
    }
    fclose(f);
}

int main(int argc, char** argv) {
    if(argumentit(argc, argv))
	return 1;
    nct_vset apuvset = {0};
    const char** _luoknimet[] = { [kopp_e]=koppnimet, [ikir_e]=ikirnimet, [wetl_e]=wetlnimet, };
    luoknimet = _luoknimet;
    int lajeja = ( luokenum==kopp_e? ARRPIT(koppnimet):
		   luokenum==ikir_e? ARRPIT(ikirnimet):
		   luokenum==wetl_e? ARRPIT(wetlnimet):
		   -1 );
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

    nct_vset *kausivset = nct_read_ncfile("kausien_päivät.nc");
    nct_var* vuodet = nct_get_var(kausivset, "vuosi");
    vuosi0 = nct_get_integer(vuodet, 0);
    vuosi1 = nct_get_integer(vuodet, vuodet->len-1);
    const int kirjpit = 240;
    float* apu = malloc(kirjpit*(vuosi1-vuosi0)*kausia*resol*sizeof(float));

    if(mkdir(kansio, 0755) < 0 && errno != EEXIST)
	err(1, "mkdir %s epäonnistui, rivi %i", kansio, __LINE__);

    int tilaa = (vuosi1-vuosi0)*kausia;
    double päivsum_tila[tilaa*2];
    double* n_päiv_tila = päivsum_tila+tilaa;

    for(int lajinum=0; lajinum<lajeja; lajinum++) {
	memset(päivsum_tila, 0, tilaa*2*sizeof(double));
	struct laskenta l_args;

	for(int kausi_ind=1; kausi_ind<kausia; kausi_ind++) {
	    char varnimi[20];
	    sprintf(varnimi, "%s_start", kaudet[kausi_ind]);
	    nct_var* alkuvar = nct_get_var(kausivset, varnimi);
	    assert(alkuvar->xtype == NC_FLOAT);

	    /* Jos kausi kestää monta vuotta, se on katkaistu jostain päivästä,
	       jotta emissio saadaan jaettua eri vuosille.
	       Älköön siis huomioitako kohtia,
	       joissa alkupäivä[vuosi] == loppupäivä[vuosi-1]-vuoden_päivät. */
	    sprintf(varnimi, "%s_end", kaudet[kausi_ind]);
	    nct_var* loppuvar = nct_get_var(kausivset, varnimi);
	    float *ad=alkuvar->data, *ld=loppuvar->data;
	    for(int v=1; v<vuosi1-vuosi0; v++) {
		int vuosi = vuosi0+v;
		int vuoden_päivät = 365 + (!(vuosi%4) && (vuosi%100 || !(vuosi%400)));
		for(int i=0; i<resol; i++) {
		    float *falku = ad + v*resol+i;
		    float floppu = ld[(v-1)*resol+i];
		    if(*falku != *falku || floppu != floppu) continue;
		    if((int)*falku == (int)floppu-vuoden_päivät)
			*falku = 0.0f/0.0f;
		}
	    }

	    l_args = (struct laskenta) {
		.kausiptr = alkuvar->data,
		.lajinimi = luoknimet[luokenum][lajinum],
		.lajinum  = lajinum,
		.päivät   = malloc(resol*sizeof(float)),
		.cdf      = malloc(resol*sizeof(float)),
		.kausi    = kausi_ind,
		.päiv0sum = päivsum_tila,
		.n_päiv0  = n_päiv_tila,
	    };
	    assert(l_args.päivät && l_args.cdf);

	    for(int v=0; v<(vuosi1-vuosi0); v++) {
		l_args.vuosi = v;
		l_args.pisteitä = 0;
		switch(luokenum) {
		    case wetl_e: täytä_kosteikkodata(&l_args); break;
		    case kopp_e: täytä_köppendata(&l_args);    break;
		    case ikir_e: täytä_ikirdata(&l_args);      break;
		}
		laita_data(&l_args, apu+v*kirjpit, kirjpit, kausi_ind, vuosi0+v);
	    }
	    tallenna(&l_args, apu, kirjpit, kausi_ind);
	    free(l_args.päivät);
	    free(l_args.cdf);
	}
	laita_alkupäivä(&l_args);
    }

    nct_free_vset(kausivset);
    kausivset = NULL;
    free(luok_c);
    free(apu);
    nct_free_vset(luok_vs);
    return 0;
}

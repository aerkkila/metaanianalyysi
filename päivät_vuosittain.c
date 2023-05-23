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
#include "pintaalat.h"

#define ARRPIT(a) (sizeof(a)/sizeof(*(a)))
#define MIN(a,b) (a)<(b)? (a): (b)

const int resol = 19800;

const char* ikirnimet[] = {"non-permafrost", "sporadic", "discontinuous", "continuous"};
const char* köppnimet[] = {"Db", "Dc", "Dd", "ET"};
const char* wetlnimet[] = {"wetland", "bog", "fen", "marsh", "tundra_wetland", "permafrost_bog"};
const char* kaudet[]    = {"summer", "freezing", "winter"};
const char* päänimet [] = {"köppen", "ikir", "wetland"};
enum                      {köpp_e,   ikir_e, wetl_e} luokenum;
const char* muuttujat[] = {"start", "end", "length"};
enum                      {start_e, end_e, length_e, muuttujia} mitkä;
const char*** luoknimet;
const char* kansio = "kausidata";
#define kausia 3
#define wraja 0.05

static char ei_katkaistuja, kertymä, kaikki_muuttujat;
static nct_vset *luok_vs;
static char  *restrict luok_c;
static int ikirvuosi0, ikirvuosia, vuosi0, vuosi1;

struct laskenta {
    const char* lajinimi;
    char* maski;
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

#define jos(a) else if (!strcmp(argv[i], #a))
void argumentit(int argc, char** argv) {
    for(int i=1; i<argc; i++) {
	if(0);
	jos(köpp)
	    luokenum = köpp_e;
	jos(wetl)
	    luokenum = wetl_e;
	jos(ikir)
	    luokenum = ikir_e;
	jos(alku)
	    mitkä = start_e;
	jos(loppu)
	    mitkä = end_e;
	jos(pituus)
	    mitkä = length_e;
	jos(kaikki_muuttujat)
	    kaikki_muuttujat = 1;
	jos(kertymä)
	    kertymä = 1;
	jos(eikatkaistuja)
	    ei_katkaistuja = 1;
	else
	    printf("tuntematon argumentti %s\n", argv[i]);
    }
}
#undef jos

static void* lue_köpp() {
    char* luok = malloc(resol);
    int pit;
    FILE* f = fopen("./köppenmaski.txt", "r");
    if(!f) return NULL;
    if((pit=fread(luok, 1, resol, f))!=resol)
	printf("Luettiin %i eikä %i\n", pit, resol);
    for(int i=0; i<resol; i++)
	luok[i] -= '1';
    fclose(f);
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
    static void* (*funktio[])(void) = { [köpp_e]=lue_köpp, [ikir_e]=lue_ikir, [wetl_e]=lue_wetl, };
    return funktio[luokenum]();
}

void päivä_keskiarvoon(struct laskenta* args, double ala, int kausi, float päivä) {
    args->päiv0sum[kausia*args->vuosi + kausi] += päivä * ala;
    args->n_päiv0 [kausia*args->vuosi + kausi] += ala;

    if(kertymä) {
	int pisteitä = args->pisteitä++;
	args->päivät[pisteitä] = päivä;
	args->cdf[pisteitä] = ala;
    }
}

void päivä_keskiarvoon_w(struct laskenta* args, double ala, int kausi, float päivä, double paino) {
    args->päiv0sum[kausia*args->vuosi + kausi] += päivä * ala * paino;
    args->n_päiv0 [kausia*args->vuosi + kausi] += ala * paino;

    if(kertymä) {
	int pisteitä = args->pisteitä++;
	args->päivät[pisteitä] = päivä;
	args->cdf[pisteitä] = ala*paino;
    }
}

void täytä_kosteikkodata(struct laskenta* args) {
    double *restrict osuus0ptr = NCTVAR(*luok_vs, "wetland").data;
    double *restrict osuus1ptr = NCTVAR(*luok_vs, wetlnimet[args->lajinum]).data;
    for (int r=0; r<resol; r++) {
	if (!args->maski[r] || osuus0ptr[r] < wraja) continue;
	float päivä = args->kausiptr[args->vuosi*resol+r];
	if (päivä != päivä) continue;
	päivä_keskiarvoon_w(args, pintaalat[r/360], args->kausi, päivä, osuus1ptr[r]);
    }
}

void täytä_köppendata(struct laskenta* args) {
    for (int r=0; r<resol; r++) {
	if (!args->maski[r] || luok_c[r] != args->lajinum) continue;
	float päivä = args->kausiptr[args->vuosi*resol+r];
	if (päivä != päivä) continue;
	päivä_keskiarvoon(args, pintaalat[r/360], args->kausi, päivä);
    }
}

void täytä_ikirdata(struct laskenta* args) {
    int ikirv = vuosi0 + args->vuosi - ikirvuosi0;
    if (ikirv >= ikirvuosia)
	ikirv = ikirvuosia-1;
    for(int r=0; r<resol; r++) {
	if (!args->maski[r] || luok_c[ikirv*resol+r] != args->lajinum) continue;
	float päivä = args->kausiptr[args->vuosi*resol+r];
	if (päivä != päivä) continue;
	päivä_keskiarvoon(args, pintaalat[r/360], args->kausi, päivä);
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

void kirjoita_csv(struct laskenta* args, FILE* f) {
    fprintf(f, "#%s_%s\n", muuttujat[mitkä], args->lajinimi);
    for(int v=vuosi0; v<vuosi1; v++)
	fprintf(f, ",%i", v);
    fputc('\n', f);
    for(int kausi=0; kausi<kausia; kausi++) {
	fprintf(f, "%s", kaudet[kausi]);
	for(int v=0; v<vuosi1-vuosi0; v++) {
	    float tavg = args->päiv0sum[v*kausia+kausi] / args->n_päiv0[v*kausia+kausi];
	    if(tavg == tavg)
		fprintf(f, ",%i", (int)tavg);
	    else
		fputc(',',f);
	}
	fputc('\n', f);
    }
}

int main(int argc, char** argv) {
    argumentit(argc, argv);
alku:
    nct_vset maskivset = {0};
    const char** _luoknimet[] = { [köpp_e]=köppnimet, [ikir_e]=ikirnimet, [wetl_e]=wetlnimet, };
    luoknimet = _luoknimet;
    int lajeja = ( luokenum==köpp_e? ARRPIT(köppnimet):
		   luokenum==ikir_e? ARRPIT(ikirnimet):
		   luokenum==wetl_e? ARRPIT(wetlnimet):
		   -1 );
    assert(lue_luokitus());

    nct_read_ncfile_gd(&maskivset, "aluemaski.nc");
    int lonpit = nct_get_varlen(&NCTVAR(maskivset, "lon"));
    int latpit = nct_get_varlen(&NCTVAR(maskivset, "lat"));
    assert(lonpit*latpit == resol);
    char* maski = nct_next_truevar(maskivset.vars[0], 0)->data;

    nct_vset *kausivset = nct_read_ncfile("kausien_päivät.nc");
    nct_var* vuodet = nct_get_var(kausivset, "vuosi");
    vuosi0 = nct_get_integer(vuodet, 0);
    vuosi1 = nct_get_integer(vuodet, -1) + 1;
    const int kirjpit = 240;
    float* apu = malloc(kirjpit*(vuosi1-vuosi0)*kausia*resol*sizeof(float));

    if(mkdir(kansio, 0755) < 0 && errno != EEXIST)
	err(1, "mkdir %s epäonnistui, rivi %i", kansio, __LINE__);

    int tilaa = (vuosi1-vuosi0)*kausia;
    double päivsum_tila[tilaa*2];
    double* n_päiv_tila = päivsum_tila+tilaa;
    float* pituustaul[kausia] = {0};

    /* Tallennustiedosto */
    FILE* f = fopen(aprintf("%s/%s_%s.csv", kansio, muuttujat[mitkä], päänimet[luokenum]), "w");

    for(int lajinum=0; lajinum<lajeja; lajinum++) {
	memset(päivsum_tila, 0, tilaa*2*sizeof(double));
	struct laskenta l_args;

	for(int kausi_ind=0; kausi_ind<kausia; kausi_ind++) {
	    char varnimi[20];
	    sprintf(varnimi, "%s_start", kaudet[kausi_ind]);
	    nct_var* alkuvar = nct_get_var(kausivset, varnimi);
	    assert(alkuvar->xtype == NC_FLOAT);
	    sprintf(varnimi, "%s_end", kaudet[kausi_ind]);
	    nct_var* loppuvar = nct_get_var(kausivset, varnimi);
	    float *ad=alkuvar->data, *ld=loppuvar->data;

	    /* Jos kausi kestää monta vuotta, se on katkaistu jostain päivästä,
	       jotta emissio saadaan jaettua eri vuosille.
	       Älköön siis välttämättä huomioitako kohtia,
	       joissa alkupäivä[vuosi] == loppupäivä[vuosi-1]-vuoden_päivät. */
	    if(ei_katkaistuja)
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
		.lajinimi = luoknimet[luokenum][lajinum],
		.lajinum  = lajinum,
		.maski    = maski,
		.kausi    = kausi_ind,
		.päiv0sum = päivsum_tila,
		.n_päiv0  = n_päiv_tila,
	    };

	    switch(mitkä) {
		case start_e:
		    l_args.kausiptr = ad;
		    break;
		case end_e:
		    l_args.kausiptr = ld;
		    break;
		case length_e:
		    if(!pituustaul[kausi_ind]) {
			assert((pituustaul[kausi_ind] = malloc(resol*(vuosi1-vuosi0)*sizeof(float))));
			for(int i=0; i<resol*(vuosi1-vuosi0); i++)
			    pituustaul[kausi_ind][i] = ld[i] - ad[i];
		    }
		    l_args.kausiptr = pituustaul[kausi_ind];
		    break;
		case muuttujia:
		    errx(1, "enum mitkä sai ylimenevän arvon");
	    }

	    if(kertymä) {
		l_args.päivät = malloc(resol*sizeof(float));
		l_args.cdf    = malloc(resol*sizeof(float));
		assert(l_args.päivät && l_args.cdf);
	    }
	    for(int v=0; v<(vuosi1-vuosi0); v++) {
		l_args.vuosi = v;
		l_args.pisteitä = 0;
		switch(luokenum) {
		    case wetl_e: täytä_kosteikkodata(&l_args); break;
		    case köpp_e: täytä_köppendata(&l_args);    break;
		    case ikir_e: täytä_ikirdata(&l_args);      break;
		}
		if(kertymä)
		    laita_data(&l_args, apu+v*kirjpit, kirjpit, kausi_ind, vuosi0+v);
	    }
	    if(kertymä) {
		tallenna(&l_args, apu, kirjpit, kausi_ind); // kertymäfunktio
		free(l_args.päivät);
		free(l_args.cdf);
	    }
	}
	kirjoita_csv(&l_args, f);
    }

    fclose(f);
    for(int i=0; i<kausia; i++)
	free(pituustaul[i]);
    maskivset = (nct_free_vset(&maskivset), (nct_vset){0});
    kausivset = luok_vs = luok_c = apu = (nct_free_vset(kausivset), nct_free_vset(luok_vs), free(luok_c), free(apu), NULL);
    if(kaikki_muuttujat)
	if(++mitkä < muuttujia)
	    goto alku;
    return 0;
}

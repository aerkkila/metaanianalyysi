#include <nctietue2.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdarg.h>
#include <unistd.h>
#include <fcntl.h>
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
#define SUHT2ABS_KERR(hila) (r2 * ASTE * (hila))

#ifndef VUODET_ERIKSEEN
#define VUODET_ERIKSEEN 0
#endif

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

static nct_vset *luok_vs;
static int       ppnum;
static char  *restrict luok_c;
static double *restrict alat;
static double* kost;
static int ikirvuosi0, ikirvuosia, vuosi0, vuosi1, t1max;
char* kansio;

struct laskenta {
    const char* lajinimi;
    float *kausiptr0, *kausiptr1, *vuoptr;
    int kausi, lajinum, vuosi, vuo_t0;
    /* kirjoittaminen */
    float *vuoulos, *cdf;
    int sijainti;
    /* vuodet erikseen */
    double *emissio;
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
    if(argc < 3) {
	printf("Käyttö: %s luokitus:köpp/ikir/wetl pri/post\n", argv[0]);
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
    if (argc <= 3)
	return 0;
    if (!strcmp(argv[3], "kost"))
	kost = nct_read_from_ncfile("BAWLD1x1.nc", "wetland", nc_get_var_double, sizeof(double));
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

int hae_raja(struct laskenta* args, int päivä) {
    struct tm tm0 = {
	.tm_year = vuosi0+args->vuosi-1900,
	.tm_mon  = 0,
	.tm_mday = 1+päivä,
    };
    return (mktime(&tm0) - args->vuo_t0) / 86400;
}

int alkuun(struct laskenta* args, int r, int* t0, int* t1) {
    float päivä0, päivä1;
    päivä0 = args->kausiptr0[resol*args->vuosi+r];
    if (päivä0 != päivä0)
	return 1;
    päivä1 = args->kausiptr1[resol*args->vuosi+r];
    if (päivä1 != päivä1)
	return 1;
    *t0 = hae_raja(args, päivä0);
    *t1 = hae_raja(args, päivä1);
    *t1 = MIN(*t1, t1max);
    return 0;
}

void aikasilmukka_kosteikko(struct laskenta* args, int r, double* kost, double* laji) {
    int t0, t1;
    if(alkuun(args, r, &t0, &t1)) return;
    double ala = alat[r/360];
    for(int t=t0; t<t1; t++) {
	int ind_t = t*resol + r;
	args->vuoulos[args->sijainti]   = args->vuoptr[ind_t] / kost[r];
	args->cdf    [args->sijainti++] = ala * laji[r];
	if(VUODET_ERIKSEEN)
	    *args->emissio += args->vuoptr[ind_t] * ala * laji[r]/kost[r];
    }
}

void aikasilmukka(struct laskenta* args, int r) {
    int t0, t1;
    if(alkuun(args, r, &t0, &t1)) return;
    double ala = alat[r/360];
    for(int t=t0; t<t1; t++) {
	int ind_t = t*resol + r;
	args->vuoulos[args->sijainti]   = args->vuoptr[ind_t];
	args->cdf    [args->sijainti++] = ala;
	if(VUODET_ERIKSEEN)
	    *args->emissio += args->vuoptr[ind_t] * ala;
    }
}

void täytä_kosteikkodata(struct laskenta* args) {
    double *restrict osuus0ptr = NCTVAR(*luok_vs, "wetland").data;
    double *restrict osuus1ptr = NCTVAR(*luok_vs, wetlnimet[args->lajinum]).data;
    for(int r=0; r<resol; r++) {
	if (osuus0ptr[r] < wraja)   continue;
	aikasilmukka_kosteikko(args, r, osuus0ptr, osuus1ptr);
    }
}

void täytä_köppendata(struct laskenta* args) {
    if (kost) goto kosteikko;

    for (int r=0; r<resol; r++)
	if (luok_c[r] == args->lajinum)
	    aikasilmukka(args, r);
    return;

kosteikko:
    for (int r=0; r<resol; r++)
	if (luok_c[r] == args->lajinum)
	    aikasilmukka_kosteikko(args, r, kost, kost);
}

/* Jos ikiroutaluokka vaihtuu, aloitettu kausi käydään kuitenkin loppuun samana ikiroutaluokkana. */
void täytä_ikirdata(struct laskenta* args) {
    int ikirv = vuosi0 + args->vuosi - ikirvuosi0;
    if (ikirv >= ikirvuosia)
	ikirv = ikirvuosia-1;
    if (kost) goto kosteikko;

    for (int r=0; r<resol; r++)
	if (luok_c[ikirv*resol+r] == args->lajinum)
	    aikasilmukka(args, r);
    return;

kosteikko:
    for (int r=0; r<resol; r++)
	if (luok_c[ikirv*resol+r] == args->lajinum)
	    aikasilmukka_kosteikko(args, r, kost, kost);
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
    int fd = open(aprintf("%s/%s_%s_%s.bin", kansio, args->lajinimi, kaudet[kausi], pripost_ulos[ppnum]),
		  O_WRONLY|O_CREAT, 0644);
    assert(fd>=0);
    if (
	    (write(fd, &kirjpit, 4) != 4) |
#if VUODET_ERIKSEEN
	    (write(fd, &vuosi0, 4) != 4)  |
#endif
	    (write(fd, data, kirjpit * (VUODET_ERIKSEEN? vuosi1-vuosi0 : 1) * 4) < kirjpit*4)
       )
	warn("write %s", aprintapu);
    close(fd);
}

float* laita_data(struct laskenta* args, float *kohde, int kirjpit) {
    float* data = args->vuoulos;
    int    pit  = args->sijainti;
    float* cdf  = pintaaloista_kertymäfunktio(data, args->cdf, pit);
    if(pit < kirjpit)
	printf("liian vähän dataa %i %s, %s\n", pit, args->lajinimi, kaudet[args->kausi]);
    int ind = 0;
    for(int i=0; i<kirjpit; i++) {
	ind = binsearch(cdf, (float)i/kirjpit, ind, pit);
	kohde[i] = data[ind]*1e9;
    }
    return kohde;
}

void laita_emissio(struct laskenta* args) {
    FILE* f = fopen(aprintf("%s/emissio_%s_%s.csv", kansio,  args->lajinimi, pripost_ulos[ppnum]), "w");
    assert(f);
    fprintf(f, "#%s %s\n", args->lajinimi, pripost_ulos[ppnum]);
    for(int v=vuosi0; v<vuosi1; v++)
	fprintf(f, ",%i", v);
    fputc('\n', f);
    for(int kausi=1; kausi<kausia; kausi++) {
	fprintf(f, "%s", kaudet[kausi]);
	for(int v=0; v<vuosi1-vuosi0; v++)
	    fprintf(f, ",%.4lf", args->emissio[kausi*(vuosi1-vuosi0)+v] * SUHT2ABS_KERR(1) * 86400 * 16.0416 * 1e-12);
	fputc('\n', f);
    }
    fclose(f);
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

int main(int argc, char** argv) {
    if(argumentit(argc, argv))
	return 1;
    char kansio_[60];
    sprintf(kansio_, "vuojakaumadata%s%s", kost? "/kost": "", VUODET_ERIKSEEN? "/vuosittain": "");
    kansio = kansio_;
    nct_vset vuo;
    nct_var* apuvar;
    const char** _luoknimet[] = { [kopp_e]=koppnimet, [ikir_e]=ikirnimet, [wetl_e]=wetlnimet, };
    luoknimet = _luoknimet;
    int lajeja = ( luokenum==kopp_e? ARRPIT(koppnimet):
		   luokenum==ikir_e? ARRPIT(ikirnimet):
		   luokenum==wetl_e? ARRPIT(wetlnimet):
		   -1 );

    nct_read_ncfile_gd0(&vuo, "./flux1x1.nc");
    apuvar = &NCTVAR(vuo, pripost_sisaan[ppnum]);
    assert(apuvar->xtype == NC_FLOAT);
    float* vuoptr = (float*)apuvar->data;

    assert(lue_luokitus());

    int lonpit = NCTVARDIM(*apuvar,2).len;
    int latpit = NCTVARDIM(*apuvar,1).len;
    assert(lonpit*latpit == resol);
    assert((apuvar=&NCTVAR(vuo, "lat"))->xtype == NC_FLOAT);
    float* lat = apuvar->data;
    double _alat[latpit];
    alat = _alat;
    for(int i=0; i<latpit; i++)
	alat[i] = SUHT_ALA(lat[i], 1);

    nct_vset *kausivset = nct_read_ncfile("kausien_päivät.nc");
    nct_var* vuosivar = nct_get_var(kausivset, "vuosi");

    vuosi0 = nct_get_integer(vuosivar, 0);
    apuvar = &NCTVAR(vuo, "time");
    t1max  = apuvar->len;
    vuosi1 = VUODET_ERIKSEEN? 2021: 2020;

    nct_anyd res = nct_mktime(apuvar, NULL, 0);
    if(res.d < 0)
	warn("nct_mktime rivillä %i", __LINE__);
    int vuo_t0 = res.a.t;

    int vuosia_yht = vuosi1-vuosi0;
    int vuosia = VUODET_ERIKSEEN? 1: vuosia_yht;
    float* vuotila = malloc(366*vuosia*resol*0.9*sizeof(float));
    float* cdftila = malloc(366*vuosia*resol*0.9*sizeof(float));
    assert(vuotila && cdftila);

    mkdir_p(kansio, 0755);

    const int kirjpit = 1000;
    float* apu = malloc(kirjpit*vuosia_yht*kausia*sizeof(float));
    double emissiotila[vuosia_yht*kausia];

    for(int lajinum=0; lajinum<lajeja; lajinum++) {
	memset(emissiotila, 0, vuosia_yht*kausia*sizeof(double));
	struct laskenta l_args;

	for (int kausi_ind=1; kausi_ind<kausia; kausi_ind++) {
	    l_args = (struct laskenta) {
		.vuoptr   = vuoptr,
		    .kausiptr0 = nct_get_var(kausivset, aprintf("%s_start", kaudet[kausi_ind]))->data,
		    .kausiptr1 = nct_get_var(kausivset, aprintf("%s_end",   kaudet[kausi_ind]))->data,
		    .vuo_t0    = vuo_t0,
		    .lajinimi  = luoknimet[luokenum][lajinum],
		    .lajinum   = lajinum,
		    .vuoulos   = vuotila,
		    .cdf       = cdftila,
		    .kausi     = kausi_ind,
		    .sijainti  = 0,
	    };
	    assert(l_args.vuoulos && l_args.cdf);

	    for(int v=0; v<vuosia_yht; v++) {
		l_args.vuosi = v;
		l_args.emissio = emissiotila + kausi_ind*vuosia_yht + v;
		switch(luokenum) {
		    case wetl_e: täytä_kosteikkodata(&l_args); break;
		    case kopp_e: täytä_köppendata(&l_args);    break;
		    case ikir_e: täytä_ikirdata(&l_args);      break;
		}
		if(VUODET_ERIKSEEN) {
		    laita_data(&l_args, apu+v*kirjpit, kirjpit);
		    l_args.sijainti = 0;
		}
	    }

	    if(!VUODET_ERIKSEEN)
		laita_data(&l_args, apu, kirjpit);
	    tallenna(&l_args, apu, kirjpit, kausi_ind);
	}

	l_args.emissio = emissiotila;
	if(VUODET_ERIKSEEN)
	    laita_emissio(&l_args);
    }

    nct_free_vset(kausivset);
    kausivset = NULL;
    free(luok_c);
    free(apu);
    free(vuotila);
    free(cdftila);
    free(kost);
    nct_free_vset(luok_vs);
    nct_free_vset(&vuo);
    return 0;
}

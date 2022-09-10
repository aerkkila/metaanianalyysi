#include <nctietue2.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdarg.h>
#include <unistd.h>

// kääntäjä tarvitsee argumentit `pkg-config --libs nctietue2` -lm
// nctietue2-kirjasto on osoitteessa https://github.com/aerkkila/nctietue2.git

#define ARRPIT(a) (sizeof(a)/sizeof(*(a)))
#define MIN(a,b) (a)<(b)? (a): (b)
#define ABS(a) (a)<0? -(a): a
const char* ikirnimet[]      = {"non permafrost", "sporadic", "discontinuous", "continuous"};
const char* koppnimet[]      = {"D.c", "D.d", "ET"};
const char* wetlnimet[]      = {"wetland", "bog", "fen", "marsh", "tundra_wetland", "permafrost_bog"};
enum {wetl_we, bog_we, fen_we, marsh_we, twet_we, pbog_we};
const char* kaudet[]         = {"whole_year", "summer", "freezing", "winter"};
enum kaudet_e                  {whole_year_e, summer_e, freezing_e, winter_e};
const char* pripost_sisaan[] = {"flux_bio_prior", "flux_bio_posterior"};
const char* pripost_ulos[]   = {"pri", "post"};
size_t* kauden_kapasit;
const int resol = 19800;
enum luokitus_e {kopp_e, ikir_e, wetl_e} luokenum;
int ppnum, kausia, aikapit;

float *restrict vuoptr;
char *restrict kausiptr, *restrict luok_c;
nct_vset *luok_vs;

static int compfun(const void* a, const void* b) {
    float ero = *(float*)a - *(float*)b;
    return ero<0? -1: ero==0? 0: 1;
}

int binsearch(const float* a, float f, int lower, int upper) {
    while(1) {
	int mid = (lower+upper)/2;
	if(upper-lower <= 1)
	    return f<lower? lower: f<upper? upper: upper+1;
	if(f<a[mid])
	    upper = mid-1;
	else if(f>a[mid])
	    lower = mid+1;
	else
	    return mid;
    }
}

double Q_ks(double f) {
    double summa=0, lisa;
    int j=1;
    while(j<1000) {
	int etum = j%2? 1: -1;
	lisa = etum * exp(-2*j*j*f*f);
	if(lisa<1e-7)
	    return 2*summa;
	summa += lisa;
    }
    printf("Q_ks ei supistunut: lisa=%lf, summa=%lf\n", lisa, summa);
    return 2*summa;
}

float ks_2samp_approx(float* a, size_t alen, float* b, size_t blen) {
    float *cdf_a, *cdf_b; //molemmissa x-akselilla on concatenate(a,b)
    qsort(a, alen, 4, compfun);
    qsort(b, blen, 4, compfun);

    cdf_a = malloc((alen+blen)*4);
    for(size_t i=0; i<alen; i++)
	cdf_a[i] = (float)i / alen;
    for(size_t i=0; i<blen; i++)
	cdf_a[i+alen] = (float)binsearch(a, b[i], 0, alen) / alen;

    cdf_b = malloc((alen+blen)*4);
    for(size_t i=0; i<alen; i++)
	cdf_b[i] = (float)binsearch(b, a[i], 0, blen) / blen;
    for(size_t i=0; i<blen; i++)
	cdf_b[i+alen] = (float)i / blen;

    float maxero = -INFINITY;
    for(size_t i=0; i<alen+blen; i++) {
	float ero = ABS(cdf_a[i]-cdf_b[i]);
	if(ero > maxero)
	    maxero = ero;
    }
    printf("max ero = %f\n", maxero);

    double Ne = (double)(alen*blen) / (alen+blen);
    return Q_ks((sqrt(Ne) + 0.12 + 0.11/sqrt(Ne)) * maxero);
}

int kausi(char* str) {
    for(int i=0; i<sizeof(kaudet)/sizeof(*kaudet); i++)
	if(!strcmp(kaudet[i], str))
	    return i;
    return -1;
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
	luok[i] -= '0'+1; // '1' -> 0 jne.
    return (luok_c = luok);
}
static void* lue_ikir() {
    nct_vset *vset = nct_read_ncfile("./ikirdata.nc");
    int varid = nct_get_varid(vset, "luokka");
    char* ret = vset->vars[varid]->data;
    vset->vars[varid]->nonfreeable_data = 1;
    nct_free_vset(vset);
    free(vset);
    return (luok_c = ret);
}
static void* lue_wetl() {
    return (luok_vs = nct_read_ncfile("./BAWLD1x1.nc"));
}
void* lue_luokitus() {
    static void* (*funktio[])(void) = { [kopp_e]=lue_kopp, [ikir_e]=lue_ikir, [wetl_e]=lue_wetl, };
    return funktio[luokenum]();
}

void data_binaarista(int lajinum, float** vuoulos, int* ind_kausi) {
    memset(ind_kausi, 0, sizeof(int)*kausia);
    for(int r=0; r<resol; r++)
	for(int t=0; t<aikapit; t++) {
	    int ind_t = t*resol + r;
	    int kausi = kausiptr[ind_t];
	    if(!kausi)               continue;
	    if(luok_c[r] != lajinum) continue;
	    vuoulos[kausi][lajinum*kauden_kapasit[kausi] + ind_kausi[kausi]++] = vuoptr[ind_t];
	    vuoulos[0]    [lajinum*kauden_kapasit[0]     + ind_kausi[0]++]     = vuoptr[ind_t];
	}
}

void data_kosteikosta(int lajinum, float** vuoulos, int* ind_kausi) {
    double *restrict osuus0ptr = NCTVAR(*luok_vs, "wetland").data;
    double *restrict osuus1ptr = NCTVAR(*luok_vs, wetlnimet[lajinum]).data;

    memset(ind_kausi, 0, sizeof(int)*kausia);
    for(int r=0; r<resol; r++)
	for(int t=0; t<aikapit; t++) {
	    int ind_t = t*resol + r;
	    int kausi = kausiptr[ind_t];
	    if(!kausi)              continue;
	    if(osuus1ptr[r] < 0.05) continue;
	    vuoulos[kausi][lajinum*kauden_kapasit[kausi] + ind_kausi[kausi]++] = vuoptr[ind_t] * osuus1ptr[r]/osuus0ptr[r];
	    vuoulos[0]    [lajinum*kauden_kapasit[0]     + ind_kausi[0]++]     = vuoptr[ind_t] * osuus1ptr[r]/osuus0ptr[r];
	}
}

char aprintapu[256];
char* aprintf(const char* muoto, ...) {
    va_list args;
    va_start(args, muoto);
    vsprintf(aprintapu, muoto, args);
    va_end(args);
    return aprintapu;
}

int main(int argc, char** argv) {
    if(argumentit(argc, argv))
	return 1;
    nct_vset vuo;
    nct_var* apuvar;
    int kausia=ARRPIT(kaudet);
    const char** luoknimet[]    = { [kopp_e]=koppnimet, [ikir_e]=ikirnimet, [wetl_e]=wetlnimet, };
    int lajeja = ( luokenum==kopp_e? ARRPIT(koppnimet):
		   luokenum==ikir_e? ARRPIT(ikirnimet):
		   luokenum==wetl_e? ARRPIT(wetlnimet):
		   -1 );

    nct_read_ncfile_gd0(&vuo, "./flux1x1.nc");
    if(!lue_luokitus()) {
	printf("Luokitusta ei luettu\n");
	return 1;
    }

    apuvar = &NCTVAR(vuo, pripost_sisaan[ppnum]);
    if(apuvar->xtype != NC_FLOAT) {
	printf("Vuodatan tyyppi ei täsmää koodissa ja datassa.\n");
	return 1;
    }
    vuoptr  = apuvar->data;

    for(int ftnum=2; ftnum<3; ftnum++) {
	nct_vset kausivset;
	nct_read_ncfile_gd0(&kausivset, aprintf("./kaudet%i.nc", ftnum));

	apuvar = &NCTVAR(kausivset, "kausi");
	if(apuvar->xtype != NC_BYTE && apuvar->xtype != NC_UBYTE) {
	    printf("Kausidatan tyyppi ei täsmää koodissa ja datassa.\n");
	    return 1;
	}
	kausiptr = apuvar->data;
	
	int l1 = NCTDIM(kausivset, "time").len;
	int l2 = NCTDIM(vuo, "time").len;
	aikapit = MIN(l1, l2);
	int vuosia  = roundf(aikapit / 365.25f);
	aikapit = vuosia*365.25;

	size_t kauden_kapasit_arr[kausia];
	kauden_kapasit = kauden_kapasit_arr;
	kauden_kapasit[whole_year_e] = (size_t)(aikapit*1.0 * resol*0.75);
	kauden_kapasit[summer_e]     = (size_t)(aikapit*0.7 * resol*0.75);
	kauden_kapasit[winter_e]     = (size_t)(aikapit*0.6 * resol*0.75);
	kauden_kapasit[freezing_e]   = (size_t)(aikapit*0.1 * resol*0.75);
	float* vuojako[kausia];
	for(int i=0; i<kausia; i++)
	    if(!(vuojako[i]=malloc(kauden_kapasit[i] * lajeja * 4))) {
		fprintf(stderr, "malloc #%i epäonnistui\n", i);
		return 1;
	    }

	int kausi_ind[kausia*lajeja]; memset(kausi_ind, 0, kausia*lajeja*sizeof(int));

	for(int lajinum=0; lajinum<lajeja; lajinum++)
	    if(luokenum == wetl_e)
		data_kosteikosta(lajinum, vuojako, kausi_ind+kausia*lajinum);
	    else
		data_binaarista(lajinum, vuojako, kausi_ind+kausia*lajinum);

	/*
	printf("%s; %s: %f\n", luoknimet[luokenum][1], luoknimet[luokenum][2],
	       ks_2samp_approx(vuojako[whole_year_e]+(kauden_kapasit[whole_year_e]*1), kausi_ind[kausia*1+whole_year_e],
			       vuojako[whole_year_e]+(kauden_kapasit[whole_year_e]*2), kausi_ind[kausia*2+whole_year_e]));
	*/
	FILE *pros = popen("./piirtäjä.py", "w");

#define _data(k,l) (vuojako[k]+(kauden_kapasit[k]*l))
#define _pit(k,l) (kausi_ind[kausia*l+k])
#define kirj(k, l) do {					\
	    qsort(_data(k,l), _pit(k,l), 4, compfun);	\
	    fwrite(&_pit(k,l), sizeof(int), 1, pros);	\
	    fwrite(_data(k,l), 4, _pit(k,l), pros);	\
	} while(0)
	kirj(whole_year_e, bog_we);
	kirj(whole_year_e, fen_we);
	kirj(freezing_e, bog_we);
#undef kirj
#undef _pit
#undef _data
	/*fwrite(vuojako[whole_year_e]+(kauden_kapasit[whole_year_e]*1), 4, kausi_ind[kausia*1+whole_year_e], pros);
	fwrite(vuojako[whole_year_e]+(kauden_kapasit[whole_year_e]*2), 4, kausi_ind[kausia*2+whole_year_e], pros);
	fwrite(vuojako[whole_year_e]+(kauden_kapasit[whole_year_e]*1), 4, kausi_ind[kausia*1+whole_year_e], pros);
	fwrite(vuojako[whole_year_e]+(kauden_kapasit[whole_year_e]*1), 4, kausi_ind[kausia*1+whole_year_e], pros);*/
	fclose(pros);

	nct_free_vset(&kausivset);
	kausivset = (nct_vset){0};
	for(int i=0; i<kausia; i++) {
	    free(vuojako[i]);
	    vuojako[i] = NULL;
	}
	kauden_kapasit = NULL;
    }
    free(luok_c);
    nct_free_vset(luok_vs);
    free(luok_vs);
    nct_free_vset(&vuo);
    return 0;
}

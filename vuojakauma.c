#include <nctietue2.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdarg.h>
#include <unistd.h>
#include <gsl/gsl_sort.h>
#include <gsl/gsl_statistics.h>

// kääntäjä tarvitsee argumentit `pkg-config --libs nctietue2 gsl` -lm
// nctietue2-kirjasto on osoitteessa https://github.com/aerkkila/nctietue2.git

#define ARRPIT(a) (sizeof(a)/sizeof(*(a)))
#define MIN(a,b) (a)<(b)? (a): (b)
#define ABS(a) (a)<0? -(a): a
#define ASTE 0.017453293
#define SUHT_ALA(lat, hila) (sin(((lat)+(hila)*0.5) * ASTE) - sin(((lat)-(hila)*0.5) * ASTE))

const int resol = 19800;
#define LATPIT 55

const char* ikirnimet[]      = {"non permafrost", "sporadic", "discontinuous", "continuous"};
const char* koppnimet[]      = {"D.c", "D.d", "ET"};
const char* wetlnimet[]      = {"wetland", "bog", "fen", "marsh", "tundra_wetland", "permafrost_bog"};
enum                           {wetl_we, bog_we, fen_we, marsh_we, twet_we,          pbog_we};
const char* kaudet[]         = {"whole_year", "summer", "freezing", "winter"};
enum                           {whole_year_e, summer_e, freezing_e, winter_e};
const char* pripost_sisaan[] = {"flux_bio_prior", "flux_bio_posterior"};
const char* pripost_ulos[]   = {"pri", "post"};
enum                           {kopp_e, ikir_e, wetl_e} luokenum;
const char*** luoknimet;

int      *kausi_pit;
size_t   *kauden_kapasit;
float     alat[LATPIT] = {0};
nct_vset *luok_vs;
int       ppnum, kausia, aikapit;
float *restrict vuoptr;
char  *restrict kausiptr, *restrict luok_c;
int pakota, verbose;

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
	printf("Käyttö: %s luokitus:köpp/ikir/wetl pri/post [-Bv]\n", argv[0]);
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
    for(int i=3; i<argc; i++)
	if(!strcmp(argv[i], "-B"))
	    pakota = 1;
	else if(!strcmp(argv[i], "-v"))
	    verbose = 1;
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

void nouda_data(int lajinum, float** vuoulos, float** cdf, int* kauden_pit) {
    FILE *f;

    if(pakota) goto TEE_DATA;
    for(int i=0; i<kausia; i++)
	if(access(aprintf("./vuojakaumadata/%s_%s_%s.bin", luoknimet[luokenum][lajinum], kaudet[i], pripost_ulos[ppnum]), F_OK))
	    goto TEE_DATA;

    for(int i=0; i<kausia; i++) {
	f = fopen(aprintf("./vuojakaumadata/%s_%s_%s.bin", luoknimet[luokenum][lajinum], kaudet[i], pripost_ulos[ppnum]), "r");
	if(fread(kauden_pit+i, sizeof(int), 1, f) != 1) goto TEE_DATA;
	if(fread(vuoulos[i] + lajinum*kauden_kapasit[i], 4, kauden_pit[i], f) != kauden_pit[i]) goto TEE_DATA;
	if(fread(cdf[i]     + lajinum*kauden_kapasit[i], 4, kauden_pit[i], f) != kauden_pit[i]) goto TEE_DATA;
	fclose(f);
    }
    return;

TEE_DATA:;
    float *osdet[kausia];
    if(luokenum == wetl_e)
	for(int i=0; i<kausia; i++)
	    osdet[i] = malloc(kauden_kapasit[i]*4);

    memset(kauden_pit, 0, sizeof(int)*kausia);
    if(luokenum == wetl_e) {
	double *restrict osuus0ptr = NCTVAR(*luok_vs, "wetland").data;
	double *restrict osuus1ptr = NCTVAR(*luok_vs, wetlnimet[lajinum]).data;
	for(int r=0; r<resol; r++)
	    for(int t=0; t<aikapit; t++) {
		int ind_t = t*resol + r;
		int kausi = kausiptr[ind_t];
		if(!kausi)              continue;
		if(osuus0ptr[r] < 0.05) continue;
		osdet[kausi][kauden_pit[kausi]] = osuus1ptr[r]/osuus0ptr[r];
		osdet[0]    [kauden_pit[0]]     = osuus1ptr[r]/osuus0ptr[r];
		vuoulos[kausi][lajinum*kauden_kapasit[kausi] + kauden_pit[kausi]]   = vuoptr[ind_t] * osuus1ptr[r]/osuus0ptr[r];
		vuoulos[0]    [lajinum*kauden_kapasit[0]     + kauden_pit[0]]       = vuoptr[ind_t] * osuus1ptr[r]/osuus0ptr[r];
		cdf[kausi][lajinum*kauden_kapasit[kausi]     + kauden_pit[kausi]++] = alat[r/360];
		cdf[0]    [lajinum*kauden_kapasit[0]         + kauden_pit[0]++]     = alat[r/360];
	    }
    }
    else // binääridata
	for(int r=0; r<resol; r++)
	    for(int t=0; t<aikapit; t++) {
		int ind_t = t*resol + r;
		int kausi = kausiptr[ind_t];
		if(!kausi)               continue;
		if(luok_c[r] != lajinum) continue;
		vuoulos[kausi][lajinum*kauden_kapasit[kausi] + kauden_pit[kausi]]   = vuoptr[ind_t];
		vuoulos[0]    [lajinum*kauden_kapasit[0]     + kauden_pit[0]]       = vuoptr[ind_t];
		cdf[kausi][lajinum*kauden_kapasit[kausi]     + kauden_pit[kausi]++] = alat[r/360];
		cdf[0]    [lajinum*kauden_kapasit[0]         + kauden_pit[0]++]     = alat[r/360];
	    }

    if(access("./vuojakaumadata", F_OK))
	if(system("mkdir vuojakaumadata")) {
	    register int eax asm("eax");
	    printf("system(mkdir)-komento palautti arvon %i", eax);
	}

    for(int kausi=0; kausi<kausia; kausi++) {
	float* data   = vuoulos[kausi] + kauden_kapasit[kausi]*lajinum;
	float* cdfptr = cdf[kausi]     + kauden_kapasit[kausi]*lajinum;
	int    pit    = kauden_pit[kausi];

	gsl_sort2_float(data, 1, cdfptr, 1, pit);

	/*lyhennetään, koska taulukot ovat valtavan pitkiä
	int N = 320000, n;
	float vali = (float)pit/N;
	if(vali > 1) {
	    if(luokenum==wetl_e)
		for(n=0; n<N && n*vali<pit; n++) {
		    data        [n] = data        [(int)(n*vali)];
		    osdet[kausi][n] = osdet[kausi][(int)(n*vali)];
		}
	    else
		for(n=0; n<N && n*vali<pit; n++)
		    data[n] = data[(int)(n*vali)];
	    kauden_pit[kausi] = n;
	}

	//gsl_sort2_float(data, 1, cdfptr, 1, kauden_pit[kausi]);*/

	if(luokenum==wetl_e) {
	    float avg = gsl_stats_float_mean(osdet[kausi], 1, kauden_pit[kausi]);
	    free(osdet[kausi]);
	    for(int j=0; j<kauden_pit[kausi]; j++)
		data[j] /= avg;
	}
	
	for(int i=1; i<kauden_pit[kausi]; i++)
	    cdfptr[i] += cdfptr[i-1];
	for(int i=0; i<kauden_pit[kausi]; i++)
	    cdfptr[i] /= cdfptr[kauden_pit[kausi]-1];

	if(!(f = fopen(aprintf("./vuojakaumadata/%s_%s_%s.bin",
			       luoknimet[luokenum][lajinum], kaudet[kausi], pripost_ulos[ppnum]), "w")))
	    puts("Mitä ihmettä");
	fwrite(kauden_pit+kausi, 4, 1, f);
	fwrite(vuoulos[kausi] + lajinum*kauden_kapasit[kausi], 4, kauden_pit[kausi], f);
	fwrite(cdf[kausi]     + lajinum*kauden_kapasit[kausi], 4, kauden_pit[kausi], f);
	fclose(f);
    }
}

int main(int argc, char** argv) {
    if(argumentit(argc, argv))
	return 1;
    nct_vset vuo;
    nct_var* apuvar;
    kausia = ARRPIT(kaudet);
    const char** _luoknimet[]    = { [kopp_e]=koppnimet, [ikir_e]=ikirnimet, [wetl_e]=wetlnimet, };
    luoknimet = _luoknimet;
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

    for(int i=0; i<LATPIT; i++)
	alat[i] = SUHT_ALA(29.5+i, 1);

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
	float* cdf[kausia];
	for(int i=0; i<kausia; i++)
	    if(!(cdf[i]=malloc(kauden_kapasit[i] * lajeja * 4))) {
		fprintf(stderr, "malloc #%i epäonnistui (cdf)\n", i);
		return 1;
	    }

	int _kausi_pit[kausia*lajeja]; memset(_kausi_pit, 0, kausia*lajeja*sizeof(int));
	kausi_pit = _kausi_pit;

	for(int lajinum=0; lajinum<lajeja; lajinum++)
	    nouda_data(lajinum, vuojako, cdf, kausi_pit+kausia*lajinum);

	FILE *pros = popen("./vuojakauman_piirtäjä.py", "w");

	void kirj(int kausi, int laji) {
	    int pit = kausi_pit[kausia*laji + kausi];
	    float* xdata = vuojako[kausi] + kauden_kapasit[kausi]*laji;
	    float* ydata = cdf[    kausi] + kauden_kapasit[kausi]*laji;
	    fprintf(pros, "%s, %s\n", luoknimet[luokenum][laji], kaudet[kausi]);
	    fwrite(&pit, sizeof(int), 1, pros);
	    fwrite(xdata, 4, pit, pros);
	    fwrite(ydata, 4, pit, pros);
	    if(verbose) {
		for(int i=pit-1; i>0; i--)
		    ydata[i] -= ydata[i-1];
		printf("%.4f %s, %s\n",
		       gsl_stats_float_wmean(ydata, 1, xdata, 1, pit)*1e9,
		       luoknimet[luokenum][laji], kaudet[kausi]);
	    }
	}
	void vaihda_kuva() {
	    fputc('\n', pros);
	}

	switch(luokenum) {
	case wetl_e:
	    for(int laji=0; laji<3; laji++)
		for(int kausi=0; kausi<4; kausi++)
		    kirj(kausi, laji);
	    vaihda_kuva();
	    for(int laji=3; laji<5; laji++)
		for(int kausi=0; kausi<4; kausi++)
		    kirj(kausi, laji);
	    break;
	case ikir_e:
	    for(int laji=0; laji<2; laji++)
		for(int kausi=0; kausi<4; kausi++)
		    kirj(kausi, laji);
	    vaihda_kuva();
	    for(int laji=2; laji<4; laji++)
		for(int kausi=0; kausi<4; kausi++)
		    kirj(kausi, laji);
	    break;
	case kopp_e:
	    for(int laji=0; laji<lajeja; laji++)
		for(int kausi=0; kausi<4; kausi++)
		    kirj(kausi, laji);
	    break;
	}

	fclose(pros);

	nct_free_vset(&kausivset);
	kausivset = (nct_vset){0};
	for(int i=0; i<kausia; i++) {
	    free(vuojako[i]);
	    vuojako[i] = NULL;
	    free(cdf[i]);
	    cdf[i] = NULL;
	}
	kauden_kapasit = NULL;
    }
    free(luok_c);
    nct_free_vset(luok_vs);
    free(luok_vs);
    nct_free_vset(&vuo);
    return 0;
}

#include <nctietue2.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdarg.h>
#include <unistd.h>
#include <gsl/gsl_sort.h>
#include <gsl/gsl_statistics.h>

// kääntäjä tarvitsee argumentit `pkg-config --libs nctietue2` -lm
// nctietue2-kirjasto on osoitteessa https://github.com/aerkkila/nctietue2.git

/* Tämä ohjelma lukee valtavan määrän dataa, mutta tiivistää sitä sitten paljon.
   Muistia kuitenkin alustetaan aina sama valtava määrä, vaikka tiivistetty vain luettaisiin muistista.
   Sen voisi tästä ainakin korjata. */

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
enum {wetl_we, bog_we, fen_we, marsh_we, twet_we, pbog_we};
const char* kaudet[]         = {"whole_year", "summer", "freezing", "winter"};
enum kaudet_e                  {whole_year_e, summer_e, freezing_e, winter_e};
const char* pripost_sisaan[] = {"flux_bio_prior", "flux_bio_posterior"};
const char* pripost_ulos[]   = {"pri", "post"};
const char*** luoknimet;

int      *kausi_ind;
size_t   *kauden_kapasit;
float     alat[LATPIT] = {0};
nct_vset *luok_vs;
int       ppnum, kausia, aikapit;
float *restrict vuoptr;
char  *restrict kausiptr, *restrict luok_c;
enum luokitus_e {kopp_e, ikir_e, wetl_e} luokenum;

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

void nouda_data(int lajinum, float** vuoulos, float** cdf, int* ind_kausi) {
    FILE *f;

    for(int i=0; i<kausia; i++)
	if(access(aprintf("./vuojakaumadata/%s_%s.bin", luoknimet[luokenum][lajinum], kaudet[i]), F_OK))
	    goto TEE_DATA;

    for(int i=0; i<kausia; i++) {
	f = fopen(aprintf("./vuojakaumadata/%s_%s.bin", luoknimet[luokenum][lajinum], kaudet[i]), "r");
	if(fread(ind_kausi+i, sizeof(int), 1, f) != 1) goto TEE_DATA;
	if(fread(vuoulos[i] + lajinum*kauden_kapasit[i], 4, ind_kausi[i], f) != ind_kausi[i]) goto TEE_DATA;
	if(fread(cdf[i]     + lajinum*kauden_kapasit[i], 4, ind_kausi[i], f) != ind_kausi[i]) goto TEE_DATA;
	fclose(f);
    }
    return;

TEE_DATA:;
    double *restrict osuus0ptr = NCTVAR(*luok_vs, "wetland").data;
    double *restrict osuus1ptr = NCTVAR(*luok_vs, wetlnimet[lajinum]).data;

    float *osdet[kausia];
    for(int i=0; i<kausia; i++)
	osdet[i] = malloc(kauden_kapasit[i]*4);

    memset(ind_kausi, 0, sizeof(int)*kausia);
    if(luokenum == wetl_e)
	for(int r=0; r<resol; r++)
	    for(int t=0; t<aikapit; t++) {
		int ind_t = t*resol + r;
		int kausi = kausiptr[ind_t];
		if(!kausi)              continue;
		if(osuus0ptr[r] < 0.05) continue;
		osdet[kausi][ind_kausi[kausi]] = osuus1ptr[r]/osuus0ptr[r];
		osdet[0]    [ind_kausi[0]]     = osuus1ptr[r]/osuus0ptr[r];
		vuoulos[kausi][lajinum*kauden_kapasit[kausi] + ind_kausi[kausi]]   = vuoptr[ind_t] * osuus1ptr[r]/osuus0ptr[r];
		vuoulos[0]    [lajinum*kauden_kapasit[0]     + ind_kausi[0]]       = vuoptr[ind_t] * osuus1ptr[r]/osuus0ptr[r];
		cdf[kausi][lajinum*kauden_kapasit[kausi]     + ind_kausi[kausi]++] = alat[r/360];
		cdf[0]    [lajinum*kauden_kapasit[0]         + ind_kausi[0]++]     = alat[r/360];
	    }
    else // binääridata
	for(int r=0; r<resol; r++)
	    for(int t=0; t<aikapit; t++) {
		int ind_t = t*resol + r;
		int kausi = kausiptr[ind_t];
		if(!kausi)               continue;
		if(luok_c[r] != lajinum) continue;
		vuoulos[kausi][lajinum*kauden_kapasit[kausi] + ind_kausi[kausi]]   = vuoptr[ind_t];
		vuoulos[0]    [lajinum*kauden_kapasit[0]     + ind_kausi[0]]       = vuoptr[ind_t];
		cdf[kausi][lajinum*kauden_kapasit[kausi]     + ind_kausi[kausi]++] = alat[r/360];
		cdf[0]    [lajinum*kauden_kapasit[0]         + ind_kausi[0]++]     = alat[r/360];
	    }

    if(access("./vuojakaumadata", F_OK))
	if(system("mkdir vuojakaumadata")) {
	    register int eax asm("eax");
	    printf("system(mkdir)-komento palautti arvon %i", eax);
	}

    for(int kausi=0; kausi<kausia; kausi++) {
	float* data   = vuoulos[kausi] + kauden_kapasit[kausi]*lajinum;
	float* cdfptr = cdf[kausi]     + kauden_kapasit[kausi]*lajinum;
	int    pit    = kausi_ind[kausia*lajinum + kausi];

	gsl_sort2_float(data, 1, cdfptr, 1, pit);

	/*lyhennetään, koska taulukot ovat valtavan pitkiä*/
	int N = 4096, n;
	float vali = (float)pit/N;
	if(vali > 1) {
	    for(n=0; n<N && n*vali<pit; n++) {
		data        [n] = data        [(int)(n*vali)];
		osdet[kausi][n] = osdet[kausi][(int)(n*vali)];
	    }
	    ind_kausi[kausi] = n;
	}

	float avg = gsl_stats_float_mean(osdet[kausi], 1, ind_kausi[kausi]);
	free(osdet[kausi]);
	for(int j=0; j<ind_kausi[kausi]; j++)
	    data[j] /= avg;
	
	for(int i=1; i<ind_kausi[kausi]; i++)
	    cdfptr[i] += cdfptr[i-1];
	for(int i=0; i<ind_kausi[kausi]; i++)
	    cdfptr[i] /= cdfptr[ind_kausi[kausi]-1];

	if(!(f = fopen(aprintf("./vuojakaumadata/%s_%s.bin", luoknimet[luokenum][lajinum], kaudet[kausi]), "w")))
	    puts("Mitä ihmettä");
	fwrite(ind_kausi+kausi, 4, 1, f);
	fwrite(vuoulos[kausi] + lajinum*kauden_kapasit[kausi], 4, ind_kausi[kausi], f);
	fwrite(cdf[kausi]     + lajinum*kauden_kapasit[kausi], 4, ind_kausi[kausi], f);
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

	int _kausi_ind[kausia*lajeja]; memset(_kausi_ind, 0, kausia*lajeja*sizeof(int));
	kausi_ind = _kausi_ind;

	for(int lajinum=0; lajinum<lajeja; lajinum++)
	    nouda_data(lajinum, vuojako, cdf, kausi_ind+kausia*lajinum);

	FILE *pros = popen("./piirtäjä.py", "w");

	void kirj(int kausi, int laji) {
	    int pit = kausi_ind[kausia*laji + kausi];
	    float* data = vuojako[kausi] + kauden_kapasit[kausi]*laji;
	    fprintf(pros, "%s, %s\n", luoknimet[luokenum][laji], kaudet[kausi]);
	    fwrite(&pit, sizeof(int), 1, pros);
	    fwrite(data, 4, pit, pros);
	    fwrite(cdf[kausi], 4, pit, pros);
	}

	if (luokenum == wetl_e) {
	    kirj(whole_year_e, bog_we);
	    //kirj(whole_year_e, fen_we);
	    kirj(whole_year_e, marsh_we);
	    kirj(freezing_e, bog_we);
	    //kirj(freezing_e, fen_we);
	    kirj(freezing_e, marsh_we);
	    //kirj(freezing_e, twet_we);
	} else if (luokenum == ikir_e) {
	    for(int i=0; i<4; i++)
		kirj(whole_year_e, i);
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

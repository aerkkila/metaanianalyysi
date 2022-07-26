#include <nctietue2.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdarg.h>

// kääntäjä tarvitsee argumentit `pkg-config --libs nctietue2` -lm
// nctietue2-kirjasto on osoitteessa https://github.com/aerkkila/nctietue2.git

const double r2 = 40592558970441; //(6371229 m)^2;
#define PINTAALA(lat, hila) ((hila)*r2*(sin((lat)+(hila))-sin(lat)))//*1.0e-6)
#define ASTE 0.017453293

#define ARRPIT(a) sizeof(a)/sizeof(*(a))
#define MIN(a,b) (a)<(b)? (a): (b)
const char* ikirnimet[]      = {"non permafrost", "sporadic", "discontinuous", "continuous"};
const char* koppnimet[]      = {"D.c", "D.d", "ET"};
const char* wetlnimet[]      = {"wetland", "bog", "fen", "marsh", "tundra_wetland", "permafrost_bog"};
const char* kaudet[]         = {"whole_year", "summer", "freezing", "winter"};
const char* pripost_sisaan[] = {"flux_bio_prior", "flux_bio_posterior"};
const char* pripost_ulos[]   = {"pri", "post"};
const int resol = 19800;
enum luokitus_e {kopp_e, ikir_e, wetl_e} luokenum;
int ppnum;

float *vuoptr, *lat;
char *kausiptr, *luok_c;
nct_vset *luok_vs;
int lonpit, latpit;

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

void* lue_kopp() {
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
void* lue_ikir() {
    nct_vset *vset = nct_read_ncfile("./ikirdata.nc");
    int varid = nct_get_varid(vset, "luokka");
    char* ret = vset->vars[varid]->data;
    vset->vars[varid]->nonfreeable_data = 1;
    nct_free_vset(vset);
    free(vset);
    return (luok_c = ret);
}
void* lue_wetl() {
    return (luok_vs = nct_read_ncfile("./BAWLD1x1.nc"));
}
void* lue_luokitus() {
    static void* (*funktio[])(void) = { [kopp_e]=lue_kopp, [ikir_e]=lue_ikir, [wetl_e]=lue_wetl, };
    return funktio[luokenum]();
}

void laske_binaarista(int lajinum, double* ainemaara, double* ala_ja_aika, int vuosia) {
    for(int t=0; t<(int)(vuosia*365.25); t++) {
	for(int j=0; j<latpit; j++) {
	    double ala = PINTAALA((double)ASTE*lat[j], ASTE);
	    for(int i=0; i<lonpit; i++) {
		int ind   = j*lonpit + i;
		int ind_t = t*latpit*lonpit + ind;
		if(!kausiptr[ind_t]) continue;
		if(luok_c[ind] != lajinum) continue;

		double vuo1 = vuoptr[ind_t] * ala;
		if(vuo1 == vuo1) {
		    ainemaara[(int)kausiptr[ind_t]]   += vuo1; // *86400 kerrotaan lopussa: mol/s * s -> mol
		    ala_ja_aika[(int)kausiptr[ind_t]] += ala;  // *86400 kerrotaan lopussa: m²*d -> m²*s
		    ainemaara[0]   += vuo1;
		    ala_ja_aika[0] += ala;
		}
	    }
	}
    }
}

void laske_wetland(int lajinum, double* ainemaara, double* ala_ja_aika, int vuosia) {
    double* osuus0ptr = NCTVAR(*luok_vs, "wetland").data;
    double* osuus1ptr = NCTVAR(*luok_vs, wetlnimet[lajinum]).data;
    for(int t=0; t<(int)(vuosia*365.25); t++) {
	for(int j=0; j<latpit; j++) {
	    if(lat[j]<49.5)
		continue;
	    double ala = PINTAALA(ASTE*lat[j], ASTE);
	    for(int i=0; i<lonpit; i++) {
		int ind   = j*lonpit + i;
		int ind_t = t*latpit*lonpit + ind;
		if(!kausiptr[ind_t]) continue;
		if(osuus0ptr[ind] == 0) continue;

		double ala1 = osuus1ptr[ind] * ala;
		double vuo1 = vuoptr[ind_t] * ala1 / osuus0ptr[ind]; // pinta-ala on osuutena wetlandista
		if(vuo1 == vuo1) {
		    ainemaara[(int)kausiptr[ind_t]]   += vuo1; // *86400 kerrotaan lopussa: mol/s * s -> mol
		    ala_ja_aika[(int)kausiptr[ind_t]] += ala1; // *86400 kerrotaan lopussa: m²*d -> m²*s
		    ainemaara[0]   += vuo1;
		    ala_ja_aika[0] += ala1;
		}
	    }
	}
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
    FILE* ulos[kausia];
    const char** luoknimet[]    = { [kopp_e]=koppnimet, [ikir_e]=ikirnimet, [wetl_e]=wetlnimet, };
    const char* luokitus_ulos[] = { [kopp_e]="köppen",  [ikir_e]="ikir",    [wetl_e]="wetland", };
    int luokkia = ( luokenum==kopp_e? ARRPIT(koppnimet):
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

    lonpit  = NCTVARDIM(*apuvar,2).len;
    latpit  = NCTVARDIM(*apuvar,1).len;

    for(int ftnum=0; ftnum<3; ftnum++) {
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
	int aikapit = MIN(l1, l2);
	lat = NCTVAR(vuo, "lat").data;

	for(int i=0; i<kausia; i++) {
	    if(!(ulos[i] = fopen(aprintf("vuotaulukot/%svuo_%s_%s_ft%i.csv",
					 luokitus_ulos[luokenum], pripost_ulos[ppnum], kaudet[i], ftnum), "w"))) {
		printf("Ei luotu ulostiedostoa\n");
		return 1;
	    }
	    fprintf(ulos[i], "#%s, data %i\n,Tg,mol/s,mol/m²,nmol/s/m²,season_length\n", kaudet[i], ftnum);
	}
	for(int lajinum=0; lajinum<luokkia; lajinum++) {
	    int     vuosia              = round(aikapit / 365.25);
	    double  ainemaara[kausia];    memset(ainemaara, 0, kausia*sizeof(double));   // mol
	    double  ala_ja_aika[kausia];  memset(ala_ja_aika, 0, kausia*sizeof(double)); // m²*s

	    if(luokenum == wetl_e)
		laske_wetland(lajinum, ainemaara, ala_ja_aika, vuosia);
	    else
		laske_binaarista(lajinum, ainemaara, ala_ja_aika, vuosia);

	    double pintaala = ala_ja_aika[0] / (vuosia*365.25);
	    //printf("%15s: %.3lf Mkm²\n", vars[lajinum], pintaala*1e-12);
	    for(int i=0; i<kausia; i++) {
		ainemaara[i]   *= 86400;
		ala_ja_aika[i] *= 86400;
		double kauden_osuus = ala_ja_aika[i]/ala_ja_aika[0]; // molemmissa on sama ala, koska luokka on sama
		double aika         = kauden_osuus * vuosia*365.25*86400;
		fprintf(ulos[i], "%s,%.4lf,%.4lf,%.4lf,%.5lf,%.4lf\n", luoknimet[luokenum][lajinum],
			ainemaara[i] / vuosia * 1e-12*16.0416, // Tg
			ainemaara[i] / aika,                   // mol/s
			ainemaara[i] / vuosia / pintaala,      // mol/m²
			ainemaara[i] / ala_ja_aika[i]*1e9,     // nmol/s/m²
			kauden_osuus
		    );
	    }
	}
	for(int i=0; i<kausia; i++)
	    fclose(ulos[i]);
	nct_free_vset(&kausivset);
	kausivset = (nct_vset){0};
    }
    free(luok_c);
    nct_free_vset(luok_vs);
    free(luok_vs);
    nct_free_vset(&vuo);
    return 0;
}
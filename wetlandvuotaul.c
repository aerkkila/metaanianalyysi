#include <nctietue.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdarg.h>

// gcc wetlandvuosumma.c `pkg-config --libs nctietue` -lm
// nctietue-kirjasto on osoitteessa https://github.com/aerkkila/nctietue.git

const double r2 = 40592558970441; //(6371229 m)^2;
#define PINTAALA(lat, hila) ((hila)*r2*(sin((lat)+(hila))-sin(lat)))//*1.0e-6)
#define ASTE 0.017453293

char* vars[] = {"wetland", "bog", "fen", "marsh", "tundra_wetland", "permafrost_bog"};
#define ARRPIT(a) sizeof(a)/sizeof(*(a))
char* kaudet[] = {"whole_year", "summer", "freezing", "winter"};

int ftnum;

int kausi(char* str) {
    for(int i=0; i<sizeof(kaudet)/sizeof(*kaudet); i++)
	if(!strcmp(kaudet[i], str))
	    return i;
    return -1;
}

int argumentit(int argc, char** argv) {
    if(argc < 2) {
	printf("Käyttö: %s ftnum:0..3\n", argv[0]);
	return 1;
    }
    if(sscanf(argv[1], "%d", &ftnum)!=1) {
	printf("Ei luettu ftnum-argumenttia\n");
	return 1;
    }
    return 0;
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
    nct_vset baw, vuo, kausivset;
    nct_var* apuvar;
    double *wetlptr;
    float *vuoptr;
    int kausia=ARRPIT(kaudet), lonpit, latpit, aikapit;
    FILE* ulos[kausia];
    nct_read_ncfile_gd(&vuo, "./flux1x1_whole_year.nc");
    nct_read_ncfile_gd(&baw, "./BAWLD1x1.nc");
    nct_read_ncfile_gd(&kausivset, aprintf("./kaudet%i.nc", ftnum));
    char* kausiptr = kausivset.vars[3].data;

    apuvar = baw.vars + nct_get_varid(&baw, "wetland");
    if(apuvar->xtype != NC_DOUBLE) {
	printf("Wetland-datan tyyppi ei täsmää koodissa ja datassa.\n");
	return 1;
    }
    wetlptr = apuvar->data;

    apuvar = vuo.vars + nct_get_varid(&vuo, "flux_bio_posterior");
    if(apuvar->xtype != NC_FLOAT) {
	printf("Vuodatan tyyppi ei täsmää koodissa ja datassa.\n");
	return 1;
    }
    vuoptr  = apuvar->data;

    lonpit  = NCTVARDIM(*apuvar,2).len;
    latpit  = NCTVARDIM(*apuvar,1).len;
    aikapit = NCTVARDIM(*apuvar,0).len;

    for(int i=0; i<kausia; i++) {
	if(!(ulos[i] = fopen(aprintf("wetlandvuotaulukot/wetlandvuo_%s_ft%i.csv", kaudet[i], ftnum), "w"))) {
	    printf("Ei luotu ulostiedostoa\n");
	    return 1;
	}
	fprintf(ulos[i], "#%s, data %i\n,Tg,mol/s,mol/m²,nmol/s/m²,frac(season)\n", kaudet[i], ftnum);
    }

    for(int lajinum=0; lajinum<ARRPIT(vars); lajinum++) {
	double* wlajiptr;
	double* lat                 = baw.vars[nct_get_varid(&baw, "lat")].data;
	int     vuosia              = round(aikapit / 365.25);
	double  ainemaara[kausia];    memset(ainemaara, 0, kausia*sizeof(double));   // mol
	double  ala_ja_aika[kausia];  memset(ala_ja_aika, 0, kausia*sizeof(double)); // m²*s
	int     pisteita[kausia];     memset(pisteita, 0, kausia*sizeof(int));

	apuvar = baw.vars + nct_get_varid(&baw, vars[lajinum]);
	if(apuvar->xtype != NC_DOUBLE) {
	    printf("%s-datan tyyppi ei täsmää koodissa ja datassa..\n", vars[lajinum]);
	    return 1;
	}
	wlajiptr = apuvar->data;

	for(int t=0; t<aikapit; t++) {
	    for(int j=0; j<latpit; j++) {
		if(lat[j]<49.5)
		    continue;
		double ala = PINTAALA(ASTE*lat[j], ASTE);
		for(int i=0; i<lonpit; i++) {
		    int ind_t = t*latpit*lonpit + j*lonpit + i;
		    if(!kausiptr[ind_t])
			continue;
		    int ind   = j*lonpit + i;
		    if(wetlptr[ind] == 0) continue;

		    double ala_baw = wlajiptr[ind] * ala;
		    double vuo_baw = vuoptr[ind_t] * ala_baw / wetlptr[ind]; // pinta-ala on osuutena wetlandista
		    if(vuo_baw == vuo_baw) {
			ainemaara[(int)kausiptr[ind_t]]   += vuo_baw; // *86400 kerrotaan lopussa: mol/s * s -> mol
			ala_ja_aika[(int)kausiptr[ind_t]] += ala_baw; // *86400 kerrotaan lopussa: m²*d -> m²*s
			++pisteita[(int)kausiptr[ind_t]];
			ainemaara[0]   += vuo_baw;
			ala_ja_aika[0] += ala_baw;
			++pisteita[0];
		    }
		}
	    }
	}
	double pintaala = ala_ja_aika[0] / (vuosia*365.25);
	//printf("%15s: %.3lf Mkm²\n", vars[lajinum], pintaala*1e-12);
	for(int i=0; i<kausia; i++) {
	    ainemaara[i]   *= 86400;
	    ala_ja_aika[i] *= 86400;
	    double kauden_osuus = ala_ja_aika[i]/ala_ja_aika[0]; // molemmissa on sama ala
	    double aika         = kauden_osuus * vuosia*365.25*86400;
	    fprintf(ulos[i], "%s,%.4lf,%.4lf,%.4lf,%.5lf,%.4lf\n", vars[lajinum],
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
    nct_free_vset(&baw);
    nct_free_vset(&vuo);
    nct_free_vset(&kausivset);
    return 0;
}

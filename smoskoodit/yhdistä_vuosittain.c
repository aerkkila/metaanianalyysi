#include <nctietue3.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <time.h>

/* Yhdistää sulamisdatasta kunkin vuoden tiedostot yhdeksi täyttäen puuttuvat päivät edellisellä arvolla. */

const int pit = 720*720;
int year0=2010, year1=2022;
const char* varname = "L3FT";

int on_koordinaatit = 0;

void koordinaatit(nct_set* set, nct_set* ulos) {
    nct_var* var;
    void* coord;
    var = nct_get_var(set, "x");
    nct_load_as(var, NC_DOUBLE);
    coord = var->data;
    var->not_freeable = 1;
    var = nct_get_dim(ulos, "x");
    nct_dim2coord(var, coord, NC_DOUBLE);

    var = nct_get_var(set, "y");
    nct_load_as(var, NC_DOUBLE);
    coord = var->data;
    var->not_freeable = 1;
    var = nct_get_dim(ulos, "y");
    nct_dim2coord(var, coord, NC_DOUBLE);

    on_koordinaatit = 1;
}

int main(int argc, char** argv) {
    if (argc > 2) {
	year0 = atoi(argv[1]);
	year1 = atoi(argv[2]);
    }
    char units[60];
    strcpy(units, "days since 0000-00-00"); // jotta strlen on heti oikein
    char* uusi = malloc(366*pit);
    if(!uusi) {
	fprintf(stderr, "malloc uusi epäonnistui\n");
	return 1;
    }

    struct tm aikatm = {0};
    char tiednimi[35];
    strcpy(tiednimi, "purettu/");
    char* tiednimi1 = tiednimi + strlen(tiednimi);

    nct_var* var;
    nct_set tallenn = {0};
    
    nct_put_interval(nct_dim2coord(nct_add_dim(&tallenn, 366, "time"), NULL, NC_USHORT), 0, 1);
    nct_add_varatt_text(tallenn.vars[0], "units",    units,                 0);
    nct_add_varatt_text(tallenn.vars[0], "calendar", "proleptic_gregorian", 0);
    nct_add_dim(&tallenn, 720, "y");
    nct_add_dim(&tallenn, 720, "x");
    nct_add_var_alldims(&tallenn, uusi, NC_BYTE, "data");

    puts("");
    int yday0=-1;
    for(int y=year0; y<year1; y++) {
	int päiviä = 0;
	aikatm.tm_year = y-1900;
	sprintf(units, "days since %4i-01-01", y);
	for(int m=1; m<=12; m++) {
	    aikatm.tm_mon = m-1;
	    for(int d=1; d<=31; d++) {
		aikatm.tm_mday = d;
		sprintf(tiednimi1, "FT_%i%02i%02i.nc", y, m, d);
		if(access(tiednimi, F_OK))
		    continue;
		printf("\033[A\r%s\033[K\n", tiednimi1+3);
		fflush(stdout);
		nct_set* set = nct_read_ncf(tiednimi, nct_rlazy);
		nct_var* var = nct_get_var(set, varname);
		if (!var < 0) {
		    printf("Ei muuttujaa %s\n", varname);
		    exit(1);
		}
		nct_load_as(var, NC_UBYTE);
		if (!on_koordinaatit)
		    koordinaatit(set, &tallenn);
		char* taul = var->data;
		/* Datasta puuttuu osa päivistä. Tässä täytetään puuttuvat kohdat viimeisimmällä arvolla.
		   Kun päiviä ei puutu, while-silmukka käydään vain kerran. */
		mktime(&aikatm);
		if(yday0 < 0)
		    yday0 = aikatm.tm_yday;
		while(päiviä < aikatm.tm_yday+1) { // Toistetaan luettua dataa kunnes kirjoitettuja päiviä on riittävästi.
		    for(int i=0; i<pit; i++)
			uusi[päiviä*pit+i] = taul[i];
		    päiviä++;
		}
		nct_free1(set);
	    }
	}
	/* Tarkistetaan, että vuosi kirjoitetaan loppuun, vaikka dataa puuttuisi lopusta. */
	aikatm.tm_mday = 31;
	aikatm.tm_mon = 11;
	mktime(&aikatm);
	char* ptr = uusi + (päiviä-1)*pit;
	while (päiviä < aikatm.tm_yday+1) {
	    for(int i=0; i<pit; i++)
		uusi[päiviä*pit+i] = ptr[i];
	    päiviä++;
	}
	/* Jos ensimmäisen vuoden alusta puuttuu pitkästi, niin kuin puuttuukin,
	   laitetaan alkuun asti nollaksi. */
	if(y==year0 && yday0>9)
	    memset(uusi, 0, yday0*pit);

	char tallnimi[32];
	tallenn.dims[0]->len = aikatm.tm_yday+1;
	sprintf(tallnimi, "FT_720_%i.nc", y);
	nct_write_nc(&tallenn, tallnimi);
    }
    nct_free1(&tallenn);
    return 0;
}

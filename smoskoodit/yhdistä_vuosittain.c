#include <nctietue2.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <time.h>

/* Yhdistää sulamisdatasta kunkin vuoden tiedostot yhdeksi täyttäen puuttuvat päivät edellisellä arvolla
   kääntäjä tarvitsee argumentin `pkg-config --libs nctietue2`
   github.com/aerkkila/nctietue2 pitää olla asennettuna*/

const int pit = 720*720;
const int year0=2010, year1=2022;

int main() {
    char units[60];
    strcpy(units, "days since 0000-00-00"); // jotta strlen on heti oikein
    /* Tämä lukeminen on vain muistin alustamiseksi */
    nct_vset* vset = nct_read_ncfile("purettu/FT_20140101.nc");
    int varid = nct_get_varid(vset, "L3FT");
    char tiednimi[35];
    unsigned char* uusi = malloc(366*pit);
    if(!uusi) {
	fprintf(stderr, "malloc uusi epäonnistui\n");
	return 1;
    }
    double* taul = vset->vars[varid]->data;
    struct tm aikatm = {0};

    strcpy(tiednimi, "purettu/");
    char* tiednimi1 = tiednimi + strlen(tiednimi);

    nct_vset tallenn = {0};
    nct_add_dim(&tallenn, nct_range_NC_USHORT(0,366,1), 366, NC_USHORT, "time");
    nct_add_varatt_text(tallenn.vars[0], "units",    units,                 0);
    nct_add_varatt_text(tallenn.vars[0], "calendar", "proleptic_gregorian", 0);
    char* dimnames[] = {"time", "y", "x"};
    size_t dimlens[] = {-1,     720, 720};
    nct_add_var_(&tallenn, uusi, NC_UBYTE, "data", 3, NULL, dimlens, dimnames);

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
		NCFUNK(nc_open, tiednimi, NC_NOWRITE, &vset->ncid);
		nct_load_var(vset->vars[varid], varid); // Kirjoittaa olemassaolevan päälle, joten ei ole muistivuoto.
		NCFUNK(nc_close, vset->ncid);
		vset->ncid = -1;
		/* Datasta puuttuu osa päivistä. Tässä täytetään puuttuvat kohdat viimeisimmällä arvolla.
		   Kun päiviä ei puutu, while-silmukka käydään vain kerran. */
		mktime(&aikatm);
		if(yday0 < 0)
		    yday0 = aikatm.tm_yday;
		while(päiviä < aikatm.tm_yday+1) { // Toistetaan luettua dataa kunnes kirjoitettuja päiviä on riittävästi.
		    for(int i=0; i<pit; i++)
			uusi[päiviä*pit+i] = (char)taul[i];
		    päiviä++;
		}
	    }
	}
	/* Tarkistetaan, että vuosi kirjoitetaan loppuun, vaikka dataa puuttuisi lopusta. */
	aikatm.tm_mday = 31;
	aikatm.tm_mon = 11;
	mktime(&aikatm);
	while (päiviä < aikatm.tm_yday+1) {
	    for(int i=0; i<pit; i++)
		uusi[päiviä*pit+i] = (char)taul[i];
	    päiviä++;
	}
	/* Jos ensimmäisen vuoden alusta puuttuu pitkästi, niin kuin puuttuukin,
	   laitetaan alkuun asti nollaksi. */
	if(y==year0 && yday0>9)
	    memset(uusi, 0, yday0*pit);

	char tallnimi[32];
	tallenn.dims[0]->len = aikatm.tm_yday+1;
	sprintf(tallnimi, "FT_720_%i.nc", y);
	nct_write_ncfile(&tallenn, tallnimi);
    }
    nct_free_vset(&tallenn);
    nct_free_vset(vset);
    return 0;
}

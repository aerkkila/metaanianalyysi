#include <nctietue.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <time.h>

/* Yhdistää sulamisdatasta kunkin vuoden tiedostot yhdeksi täyttäen puuttuvat päivät edellisellä arvolla
   kääntäjä tarvitsee argumentin `pkg-config --libs nctietue` */

const int pit = 720*720;

int main(int argc, char** argv) {
    char units[60];
    int data2 = argc > 1;
    /* Tämä lukeminen on vain muistin alustamiseksi */
    nct_vset* vset = nct_read_ncfile(data2? "purettu_2/FT_20140101.nc": "purettu/FT_20140101.nc");
    int varid = nct_get_varid(vset, "L3FT");
    char tiednimi[35];
    unsigned char* uusi = malloc(366*pit);
    if(!uusi) {
	fprintf(stderr, "malloc uusi epäonnistui\n");
	return 1;
    }
    double* taul = vset->vars[varid].data;
    struct tm aikatm = {0};

    strcpy(tiednimi, data2? "purettu_2/": "purettu/");
    char* tiednimi1 = tiednimi + strlen(tiednimi);

    nct_vset tallenn = {0};
    nct_add_coord(&tallenn, nct_range_NC_USHORT(0,366,1), 366, NC_USHORT, "time");
    nct_add_coord(&tallenn, nct_range_NC_USHORT(0,720,1), 720, NC_USHORT, "y");
    nct_add_coord(&tallenn, nct_range_NC_USHORT(0,720,1), 720, NC_USHORT, "x");
    nct_add_att_text(&tallenn, 0, "units", units, 0);
    nct_add_att_text(&tallenn, 0, "calendar", "proleptic_gregorian", 0);
    tallenn.vars = realloc(tallenn.vars, (tallenn.nvars+1)*sizeof(nct_var));
    int dimids[] = {0,1,2};
    nct_simply_add_var(&tallenn, uusi, NC_UBYTE, 3, dimids, "data");

    puts("");
    for(int y=2010; y<=2021; y++) {
	int paivia = 0;
	aikatm.tm_year = y-1900;
	sprintf(units, "days since %4i-01-01", y);
	memset(uusi, 0, 366*pit); // Tämä lienee turha.
	for(int m=1; m<=12; m++) {
	    aikatm.tm_mon = m-1;
	    for(int d=1; d<=31; d++) {
		aikatm.tm_mday = d;
		sprintf(tiednimi1, "FT_%i%02i%02i.nc", y, m, d);
		if(access(tiednimi, F_OK))
		    continue;
		printf("\033[F%s\033[K\n", tiednimi1+3);
		fflush(stdout);
		/* vset on sisältää jo dataa, mutta uuden datan lukeminen ei ole muistivuoto.
		   nct_load_var alustaa uutta muistia, jos data==NULL, ja muuten kirjoittaa sen päälle. */
		NCFUNK(nc_open, tiednimi, NC_NOWRITE, &vset->ncid);
		nct_load_var(vset, varid);
		NCFUNK(nc_close, vset->ncid);
		/* Datasta puuttuu osa päivistä. Tässä täytetään puuttuvat kohdat viimeisimmällä arvolla.
		   Kun päiviä ei puutu, while-silmukka käydään vain kerran. */
		mktime(&aikatm);
		while(paivia < aikatm.tm_yday+1) { // Toistetaan luettua dataa kunnes kirjoitettuja päiviä on riittävästi
		    for(int i=0; i<pit; i++)
			uusi[paivia*pit+i] = (char)taul[i];
		    paivia++;
		}
	    }
	}
	/* Tarkistetaan, että vuosi kirjoitetaan loppuun, vaikka dataa puuttuisi lopusta. */
	aikatm.tm_mday = 31;
	aikatm.tm_mon = 11;
	mktime(&aikatm);
	while (paivia < aikatm.tm_yday+1) {
	    for(int i=0; i<pit; i++)
		uusi[paivia*pit+i] = (char)taul[i];
	    paivia++;
	}

	char tallnimi[32];
	tallenn.dims[0].len = aikatm.tm_yday+1;
	sprintf(tallnimi, "FT%i_720_%i.nc", data2? 2: 1, y);
	nct_write_ncfile(&tallenn, tallnimi);
    }
    nct_free_vset(&tallenn);
    nct_free_vset(vset);
    free(vset);
    return 0;
}

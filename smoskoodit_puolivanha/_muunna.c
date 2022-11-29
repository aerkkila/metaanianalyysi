#include <nctietue.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <time.h>

// kääntäjälle `pkg-config --libs nctietue`

const int pit = 19800;

int main(int argc, char** argv) {
    int data2 = argc > 1;
    /* Tätä käytetään lähinnä muistin alustamiseen, jotta monen tiedoston lukeminen on tehokkaampaa */
    nct_vset* vset = nct_read_ncfile(data2? "purettu_2/FT_20140101.nc": "purettu/FT_20140101.nc");
    int varid = nct_get_varid(vset, "L3FT");

    double* restrict lat = nct_range_NC_DOUBLE(29.5, 84, 1);
    double* restrict lon = nct_range_NC_DOUBLE(-179.5, 180, 1);
    int* restrict koordind = malloc(pit*sizeof(int));
  
    FILE* f = fopen("koordind.bin", "r");
    if(fread(koordind, sizeof(int), pit, f) != pit)
	printf("Lukeminen epäonnistui\n");
    fclose(f);

    char tiednimi[35];
    unsigned char* uusi = malloc(12*366*pit);
    double* taul = vset->vars[varid].data;

    int aikapit = 0;
    struct tm aikatm = {0};

    strcpy(tiednimi, data2? "purettu_2/": "purettu/");
    char* tiednimi1 = tiednimi + strlen(tiednimi);
    /* haetaan ensimmäinen tiedosto päivämäärän yksikön merkitsemiseksi */
    time_t aika_t0;
    char units[60];
    for(int y=2010; y<=2021; y++)
	for(int m=1; m<=12; m++)
	    for(int d=1; d<=31; d++) {
		sprintf(tiednimi1, "FT_%i%02i%02i.nc", y, m, d);
		if(!access(tiednimi, F_OK)) {
		    sprintf(units, "days since %4i-%02i-%02i", y, m, d);
		    aikatm = (struct tm){.tm_year=y, .tm_mon=m, .tm_mday=d};
		    aika_t0 = mktime(&aikatm);
		    goto ULOS;
		}
	    }
ULOS:

    int uusi_ind = 0;
    puts("");
    for(int y=2010; y<=2021; y++) {
	aikatm.tm_year = y;
	for(int m=1; m<=12; m++) {
	    aikatm.tm_mon = m;
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
		time_t aika_t = mktime(&aikatm); // luetun tiedoston ajankohta
		int tama = (aika_t-aika_t0)/86400; // takana olevia päiviä yhteensä tähän asti
		while(aikapit <= tama) { // Toistetaan luettua dataa kunnes kirjoitettuja päiviä on riittävästi
		    for(int i=0; i<pit; i++)
			uusi[uusi_ind++] = taul[koordind[i]];
		    aikapit++;
		}
	    }
	}
    }

    nct_vset tallenn = {0};
    nct_add_coord(&tallenn, nct_range_NC_INT(0,aikapit,1), aikapit, NC_INT, "time");
    nct_add_coord(&tallenn, lat, 55, NC_DOUBLE, "lat");
    nct_add_coord(&tallenn, lon, 360, NC_DOUBLE, "lon");
    nct_add_att_text(&tallenn, 0, "units", units, 0);
    nct_add_att_text(&tallenn, 0, "calendar", "proleptic_gregorian", 0);
    tallenn.vars = realloc(tallenn.vars, (tallenn.nvars+1)*sizeof(nct_var));
    int dimids[] = {0,1,2};
    nct_simply_add_var(&tallenn, uusi, NC_UBYTE, 3, dimids, "data");
    nct_write_ncfile(&tallenn, data2? "FT1x1_2.nc": "FT1x1.nc");

    nct_free_vset(&tallenn);
    nct_free_vset(vset);
    free(vset);
    free(koordind);
    return 0;
}

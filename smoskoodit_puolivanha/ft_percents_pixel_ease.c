#include <nctietue.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

/* kääntäjälle `pkg-config --libs nctietue` -O3
   github.com/aerkkila/nctietue pitää olla asennettuna
   Tämä tekee saman kuin vastaava Python-koodi, mutta merkittävästi nopeammin. */

void transpose(double* taul) {
    double* uusi = malloc(720*720*sizeof(double));
    for(int i=0; i<720; i++)
	for(int j=0; j<720; j++)
	    uusi[i*720+j] = taul[j*720+i];
    memcpy(taul, uusi, 720*720*sizeof(double));
    free(uusi);
}

const int resol = 55*360;

int main(int argc, char** argv) {
    int data1vai2=argc, nfrozen, npartly, nthaw;
    nct_vset ftset, easelon, easelat, aluemaskiset;
    char apustr[256];
    unsigned char *aluemaski;
    int valinta[32], valintapit;
    unsigned char *ft;
    double *e2lon, *e2lat;

    nct_read_ncfile_gd(&easelon, "../Tyotiedostot/Carbon_tracker/EASE_2_lon.nc");
    nct_read_ncfile_gd(&easelat, "../Tyotiedostot/Carbon_tracker/EASE_2_lat.nc");
    nct_read_ncfile_gd(&aluemaskiset, "./aluemaski.nc");

    aluemaski = aluemaskiset.vars[2].data;
    e2lon = easelon.vars[0].data;
    e2lat = easelat.vars[0].data;
    /* En ymmärrä miksi, mutta pituuspiirit on merkitty siten, että tarvitaan tälläinen muunnos */
    transpose(e2lon);
    for(int i=0; i<720*720; i++) {
	e2lon[i] = -e2lon[i]+180;
	if(e2lon[i] > 180)
	    e2lon[i] -= 360;
    }
    double* restrict lat = nct_range_NC_DOUBLE(29.5, 84, 1);
    double* restrict lon = nct_range_NC_DOUBLE(-179.5, 180, 1);

    float* frozen = malloc(366*resol*4);
    float* partly = malloc(366*resol*4);
    float* thaw = malloc(366*resol*4);
    char* numgrids = malloc(366*resol);
    if(!thaw || !numgrids || !partly || !frozen) {
	fprintf(stderr, "malloc epäonnistui\n");
	return 1;
    }

    nct_vset tallenn = {0};
    int dimids[] = {0,1,2};
    nct_add_coord(&tallenn, nct_range_NC_INT(0,366,1), 366, NC_INT, "time");
    nct_add_coord(&tallenn, lat, 55, NC_DOUBLE, "lat");
    nct_add_coord(&tallenn, lon, 360, NC_DOUBLE, "lon");
    nct_add_att_text(&tallenn, 0, "units", NULL, 0);
    nct_add_att_text(&tallenn, 0, "calendar", "proleptic_gregorian", 0);
    tallenn.vars = realloc(tallenn.vars, (tallenn.nvars+1)*sizeof(nct_var));
    nct_simply_add_var(&tallenn, frozen, NC_FLOAT, 3, dimids, "data");

    int y0 = 2010;
    for(int y=y0; y<2022; y++) {
	sprintf(apustr, "FT%i_720_%i.nc", data1vai2, y);
	nct_read_ncfile_gd(&ftset, apustr);
	ft = ftset.vars[nct_get_noncoord_varid(&ftset)].data;
	int tpit = ftset.dims[nct_get_dimid(&ftset, "time")].len;
	tallenn.dims[0].len = tpit;
	memset(frozen,   0, 366*resol*4);
	memset(partly,   0, 366*resol*4);
	memset(thaw,     0, 366*resol*4);
	memset(numgrids, 0, 366*resol);
	for(int j=0; j<55; j++) {
	    printf("\rvuosi %i, lat %i/%i\033[K", y, j+1, 55);
	    fflush(stdout);
	    float lat1 = lat[j];
	    for(int i=0; i<360; i++) {
		if(!aluemaski[j*360+i])
		    continue;
		float lon1 = lon[i];
		valintapit=0;
		/* Mitkä pisteet otetaan huomioon */
		for(int k=0; k<720*720; k++)
		    if(e2lon[k]>=lon1-0.5 && e2lon[k]<lon1+0.5 && e2lat[k]>=lat1-0.5 && e2lat[k]<lat1+0.5)
			valinta[valintapit++] = k;

		if(!valintapit)
		    continue;
		/* Käydään kyseiset pisteet läpi kaikilla ajanhetkillä */
		for(int t=0; t<tpit; t++) {
		    nfrozen = npartly = nthaw = 0;
		    for(int k=0; k<valintapit; k++) {
			unsigned char h = ft[valinta[k]+720*720*t];
			nfrozen += h==3;
			npartly += h==2;
			nthaw   += h==1;
		    }
		    int ind = t*resol+j*360+i;
		    frozen[ind] = (float)nfrozen / valintapit;
		    partly[ind] = (float)npartly / valintapit;
		    thaw[ind]   = (float)nthaw   / valintapit;
		    numgrids[ind] = valintapit;
		}
	    }
	}

	sprintf(apustr, "days since %i-01-01", y);
	tallenn.vars[0].attrs[0].value = strdup(apustr);

	tallenn.vars[3].data = frozen;
	sprintf(apustr, "data%i/frozen_percent_pixel_%i.nc", data1vai2, y);
	nct_write_ncfile(&tallenn, apustr);

	tallenn.vars[3].data = partly;
	sprintf(apustr, "data%i/partly_frozen_percent_pixel_%i.nc", data1vai2, y);
	nct_write_ncfile(&tallenn, apustr);

	tallenn.vars[3].data = thaw;
	sprintf(apustr, "data%i/thaw_percent_pixel_%i.nc", data1vai2, y);
	nct_write_ncfile(&tallenn, apustr);

	tallenn.vars[3].data = numgrids;
	tallenn.vars[3].xtype = NC_UBYTE;
	sprintf(apustr, "data%i/number_of_pixel_%i.nc", data1vai2, y);
	nct_write_ncfile(&tallenn, apustr);
	tallenn.vars[3].xtype = NC_FLOAT;

	free(tallenn.vars[0].attrs[0].value);
	tallenn.vars[0].attrs[0].value = NULL;

	tallenn.vars[3].data = NULL;
	nct_free_vset(&ftset);
    }
    puts("");
    nct_free_vset(&tallenn);
    nct_free_vset(&easelon);
    nct_free_vset(&easelat);
    nct_free_vset(&aluemaskiset);
    free(frozen);
    free(partly);
    free(thaw);
    free(numgrids);
    return 0;
}

#include <nctietue2.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h> // mkdir
#include <err.h>

/*
 * Written based on a Python code which was written by Maria Tenkanen 
 * kääntäjälle `pkg-config --libs nctietue2` [-O3]
 * github.com/aerkkila/nctietue2 pitää olla asennettuna
 */

void transpose(double* taul) {
    double* uusi = malloc(720*720*sizeof(double));
    for(int i=0; i<720; i++)
	for(int j=0; j<720; j++)
	    uusi[i*720+j] = taul[j*720+i];
    memcpy(taul, uusi, 720*720*sizeof(double));
    free(uusi);
}

const int resol = 55*360;

#define vnta_maxpit 50
int* tee_valintaindeksit(double* lat, double* lon) {
    double *e2lon, *e2lat;
    e2lon = nct_read_from_ncfile("EASE_2_lon.nc", NULL, nc_get_var_double, sizeof(double));
    e2lat = nct_read_from_ncfile("EASE_2_lat.nc", NULL, nc_get_var_double, sizeof(double));
    unsigned char* data = nct_read_from_ncfile("FT_720_2016.nc", "data", nc_get_var_ubyte, 1);

    /* Pituuspiirit pitää jostain syystä muuntaa näin. */
    transpose(e2lon);
    for(int i=0; i<720*720; i++) {
	e2lon[i] = -e2lon[i]+180;
	if(e2lon[i] > 180)
	    e2lon[i] -= 360;
    }

    int* indeksit = malloc(resol*vnta_maxpit*sizeof(int));
    for(int j=0; j<55; j++) {
	float lat1 = lat[j];
	for(int i=0; i<360; i++) {
	    float lon1 = lon[i];
	    int valintapit=0;
	    int* valinta = indeksit + (j*360+i)*vnta_maxpit;
	    for(int k=0; k<720*720; k++)
		if(data[k] && e2lon[k]>=lon1-0.5 && e2lon[k]<lon1+0.5 && e2lat[k]>=lat1-0.5 && e2lat[k]<lat1+0.5) {
		    valinta[valintapit++] = k;
		    if(valintapit >= vnta_maxpit) {
			fprintf(stderr, "vnta_maxpit-arvoa (%i) pitää kasvattaa\n\n", vnta_maxpit);
			abort(); }
		}
	    valinta[valintapit] = -1;
	}
    }
    free(data);
    free(e2lat);
    free(e2lon);
    return indeksit;
}

int main() {
    int nfrozen, npartly, nthaw;
    nct_vset ftset;
    char apustr[256];
    unsigned char *aluemaski;
    unsigned char *ft;

    double* restrict lat = nct_range_NC_DOUBLE(29.5, 84, 1);
    double* restrict lon = nct_range_NC_DOUBLE(-179.5, 180, 1);

    float* frozen = malloc(366*resol*4);
    float* partly = malloc(366*resol*4);
    float* thaw = malloc(366*resol*4);
    char* numgrids = malloc(resol);
    if(!thaw || !numgrids || !partly || !frozen) {
	fprintf(stderr, "malloc epäonnistui\n");
	return 1;
    }

    nct_vset tallenn = {0};
    int dimids[] = {0,1,2};
    nct_add_dim(&tallenn, nct_range_NC_INT(0,366,1), 366, NC_INT, "time");
    nct_add_dim(&tallenn, lat, 55, NC_DOUBLE, "lat");
    nct_add_dim(&tallenn, lon, 360, NC_DOUBLE, "lon");
    nct_add_varatt_text(tallenn.vars[0], "units", strdup("days since 0000-00-00"), 1);
    nct_add_varatt_text(tallenn.vars[0], "calendar", "proleptic_gregorian", 0);
    nct_add_var(&tallenn, frozen, NC_FLOAT, "data", 3, dimids);

    int* vntaind = tee_valintaindeksit(lat, lon);

    if(mkdir("ft_percent", 0755) && errno != EEXIST)
	err(1, "mkdir ft_percent (rivi %i)", __LINE__);

    int y0 = 2010;
    putchar('\n');
    for(int y=y0; y<2022; y++) {
	printf("\033[A\rvuosi %i\033[K\n", y);
	sprintf(apustr, "FT_720_%i.nc", y);
	nct_read_ncfile_gd0(&ftset, apustr);
	ft = nct_next_truevar(ftset.vars[0], 0)->data;
	int tpit = NCTDIM(ftset, "time").len;
	tallenn.dims[0]->len = tpit;
	memset(frozen,   0, 366*resol*4);
	memset(partly,   0, 366*resol*4);
	memset(thaw,     0, 366*resol*4);
	memset(numgrids, 0, resol);
	for(int j=0; j<55; j++) {
	    for(int i=0; i<360; i++) {
		int k, ij = (j*360+i)*vnta_maxpit;
		for(int t=0; t<tpit; t++) {
		    nfrozen = npartly = nthaw = 0;
		    for(k=0; vntaind[ij+k]>=0; k++) {
			unsigned char h = ft[vntaind[ij+k]+720*720*t];
			nfrozen += h==3;
			npartly += h==2;
			nthaw   += h==1;
		    }
		    int ind1 = j*360 + i;
		    int ind = t*resol + ind1;
		    frozen[ind] = (float)nfrozen / k;
		    partly[ind] = (float)npartly / k;
		    thaw[ind]   = (float)nthaw   / k;
		    numgrids[ind1] = k;
		}
	    }
	}

	sprintf(apustr, "days since %i-01-01", y);
	free(tallenn.vars[0]->atts[0].value);
	tallenn.vars[0]->atts[0].value = strdup(apustr);

	tallenn.vars[3]->data = frozen;
	sprintf(apustr, "ft_percent/frozen_percent_pixel_%i.nc", y);
	nct_write_ncfile(&tallenn, apustr);

	tallenn.vars[3]->data = partly;
	sprintf(apustr, "ft_percent/partly_frozen_percent_pixel_%i.nc", y);
	nct_write_ncfile(&tallenn, apustr);

	tallenn.vars[3]->data = thaw;
	sprintf(apustr, "ft_percent/thaw_percent_pixel_%i.nc", y);
	nct_write_ncfile(&tallenn, apustr);

	tallenn.vars[3]->data = NULL;
	nct_free_vset(&ftset);
    }

    /* Number of pixels on aina sama, joten tallennetaan ilman aikakoordinaattia. */
    NCTVAR(tallenn,"lat").nonfreeable_data = 1;
    NCTVAR(tallenn,"lon").nonfreeable_data = 1;
    nct_free_vset(&tallenn);
    tallenn = (nct_vset){0};
    nct_add_dim(&tallenn, lat, 55, NC_DOUBLE, "lat");
    nct_add_dim(&tallenn, lon, 360, NC_DOUBLE, "lon");
    int dimids2[] = {0,1};
    nct_add_var(&tallenn, numgrids, NC_UBYTE, "data", 2, dimids);
    nct_write_ncfile(&tallenn, "ft_percent/number_of_pixels.nc");

    nct_free_vset(&tallenn);
    free(frozen);
    free(partly);
    free(thaw);
    free(vntaind);
}

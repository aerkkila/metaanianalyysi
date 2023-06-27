#include <nctietue3.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>	// mkdir
#include <err.h>	// mkdir
#include <proj.h>

const int resol = 55*360;
const int year0 = 2010;
const int year1 = 2022;
int xpit, ypit, xypit;
#define indir "data/"
#define outdir "ftpercent/"

static char argmax3(char a, char b, char c) {
    int arg = 1;
    char max = b;
    if (a > b) {
	arg = 0;
	max = a;
    }
    return max > c ? arg : 2;
}

#define vnta_maxpit 50
int* tee_valintaindeksit(double* lat, double* lon) {
    float *e2lon, *e2lat;
    nct_set* set = nct_read_nc("maski.nc");
    char* data = nct_firstvar(set)->data;
    nct_var* var = nct_get_var(set, "x");
    double* x = var->data;
    xpit = var->len;
    var = nct_get_var(set, "y");
    double* y = var->data;
    ypit = var->len;
    xypit = xpit*ypit;

    PJ_CONTEXT* ctx = proj_context_create();
    PJ* pj = proj_create_crs_to_crs(ctx, "+proj=laea +lat_0=90", "+proj=longlat", NULL);
    e2lat = malloc(xypit*sizeof(float)*2);
    e2lon = e2lat + xypit;
    for(int j=0; j<ypit; j++)
	for(int i=0; i<xpit; i++) {
	    PJ_XY xy = proj_trans(pj, 1, (PJ_COORD){.xy={x[i], y[j]}}).xy;
	    e2lat[j*xpit+i] = xy.y;
	    e2lon[j*xpit+i] = xy.x;
	}

    int* indeksit = malloc(resol*vnta_maxpit*sizeof(int));
    for(int j=0; j<55; j++) {
	float lat1 = lat[j];
	for(int i=0; i<360; i++) {
	    float lon1 = lon[i];
	    int valintapit=0;
	    int* valinta = indeksit + (j*360+i)*vnta_maxpit;
	    for(int k=0; k<xypit; k++)
		if (data[k]>0 && e2lon[k]>=lon1-0.5 && e2lon[k]<lon1+0.5 && e2lat[k]>=lat1-0.5 && e2lat[k]<lat1+0.5) {
		    valinta[valintapit++] = k;
		    if (valintapit >= vnta_maxpit) {
			fprintf(stderr, "vnta_maxpit-arvoa (%i) pitää kasvattaa\n\n", vnta_maxpit);
			abort(); }
		}
	    valinta[valintapit] = -1;
	}
    }
    proj_context_destroy(ctx);
    proj_destroy(pj);
    nct_free1(set);
    free(e2lat);
    return indeksit;
}

int main() {
    nct_error_action = nct_interrupt;
    int nfrozen, npartly, nthaw;
    char apustr[256];

    double* restrict lat = nct_range_NC_DOUBLE(29.5, 84, 1);
    double* restrict lon = nct_range_NC_DOUBLE(-179.5, 180, 1);

    char* frozen = malloc(366*resol);
    char* partly = malloc(366*resol);
    char* thaw	 = malloc(366*resol);
    char* moodi  = malloc(366*resol);
    char* numgrids = malloc(resol);
    if (!thaw || !numgrids || !partly || !frozen) {
	fprintf(stderr, "malloc epäonnistui\n");
	return 1;
    }

    nct_set tallenn = {0};
    int dimids[] = {0,1,2};
    //nct_dim2coord(nct_add_dim(&tallenn, 366, "time"), nct_range_NC_INT(0,366,1), NC_INT);
    nct_dim2coord(nct_add_dim(&tallenn, 366, "time"), NULL, NC_SHORT) -> not_freeable = 1;
    nct_dim2coord(nct_add_dim(&tallenn, 55, "lat"), lat, NC_DOUBLE);
    nct_dim2coord(nct_add_dim(&tallenn, 360, "lon"), lon, NC_DOUBLE);
    nct_add_varatt_text(tallenn.vars[0], "units", strdup("days since 0000-00-00"), 1);
    nct_add_varatt_text(tallenn.vars[0], "calendar", "proleptic_gregorian", 0);
    nct_add_var(&tallenn, frozen, NC_BYTE, "data", 3, dimids);

    int* vntaind = tee_valintaindeksit(lat, lon);

    if (mkdir(outdir, 0755) && errno != EEXIST)
	err(1, "mkdir %s (rivi %i)", outdir, __LINE__);

    putchar('\n');
    for(int y=year0; y<year1; y++) {
	printf("\033[A\rvuosi %i\033[K\n", y);
	sprintf(apustr, indir "L3FT_%i.nc", y);
	if (access(apustr, F_OK))
	    break;
	nct_readm_nc(ftset, apustr);
	unsigned char* ft = nct_firstvar(&ftset)->data;
	nct_var* aika = nct_get_dim(&ftset, "time");
	int tpit = aika->len;
	nct_set_length(tallenn.dims[0], tpit);
	tallenn.dims[0]->data = aika->data;
	memset(frozen,   0, 366*resol);
	memset(partly,   0, 366*resol);
	memset(thaw,     0, 366*resol);
	memset(numgrids, 0, resol);
	for(int j=0; j<55; j++) {
	    for(int i=0; i<360; i++) {
		int k, ij = (j*360+i)*vnta_maxpit;
		for(int t=0; t<tpit; t++) {
		    nfrozen = npartly = nthaw = 0;
		    int jakaja = 0;
		    for(k=0; vntaind[ij+k]>=0; k++) {
			signed char h = ft[vntaind[ij+k]+xypit*t];
			jakaja	+= h>0;
			nfrozen += h==3;
			npartly += h==2;
			nthaw   += h==1;
		    }
		    int ind1 = j*360 + i;
		    int ind = t*resol + ind1;
		    frozen[ind] = jakaja > 0 ? (float)nfrozen / jakaja * 100 : -1;
		    partly[ind] = jakaja > 0 ? (float)npartly / jakaja * 100 : -1;
		    thaw[ind]   = jakaja > 0 ? (float)nthaw   / jakaja * 100 : -1;
		    moodi[ind]  = jakaja > 0 ? argmax3(nthaw, npartly, nfrozen) + 1 : 0;
		    numgrids[ind1] = k;
		}
	    }
	}

	sprintf(apustr, "days since %i-01-01", y);
	free(tallenn.vars[0]->atts[0].value);
	tallenn.vars[0]->atts[0].value = strdup(apustr);

	tallenn.vars[3]->data = frozen;
	sprintf(apustr, outdir "frozen_percent_%i.nc", y);
	nct_write_nc(&tallenn, apustr);

	tallenn.vars[3]->data = partly;
	sprintf(apustr, outdir "partly_frozen_percent_%i.nc", y);
	nct_write_nc(&tallenn, apustr);

	tallenn.vars[3]->data = thaw;
	sprintf(apustr, outdir "thaw_percent_%i.nc", y);
	nct_write_nc(&tallenn, apustr);

	tallenn.vars[3]->data = moodi;
	sprintf(apustr, outdir "mode_class_%i.nc", y);
	nct_write_nc(&tallenn, apustr);

	tallenn.vars[3]->data = NULL;
	tallenn.dims[0]->data = NULL;
	nct_free1(&ftset);
    }

    /* Pikselien määrä on aina sama, joten tallennettakoon ilman aikakoordinaattia. */
    nct_get_var(&tallenn,"lat")->not_freeable = 1;
    nct_get_var(&tallenn,"lon")->not_freeable = 1;
    nct_free1(&tallenn);
    tallenn = (nct_set){0};
    nct_dim2coord(nct_add_dim(&tallenn, 55, "lat"), lat, NC_DOUBLE);
    nct_dim2coord(nct_add_dim(&tallenn, 360, "lon"), lon, NC_DOUBLE);
    nct_add_var(&tallenn, numgrids, NC_UBYTE, "data", 2, dimids);
    nct_write_nc(&tallenn, outdir "number_of_pixels.nc");

    nct_free1(&tallenn);
    free(frozen);
    free(partly);
    free(thaw);
    free(vntaind);
}

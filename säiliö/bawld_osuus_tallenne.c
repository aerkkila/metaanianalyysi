#include <nctietue2.h>
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <string.h>
#define HAVE_INLINE
//#include <gsl/gsl_statistics_double.h>
#include <gsl/gsl_math.h>

static const char* nimet[] = {"bog", "fen", "marsh", "permafrost_bog", "tundra_wetland"};

int main() {
    nct_vset *a0,*a1;
    int lajeja = sizeof(nimet)/sizeof(*nimet);
    int varid[lajeja], wid;
    char apu[64];
    a0 = nct_read_ncfile("BAWLD1x1.nc");
    a1 = nct_read_ncfile("BAWLD1x1_H.nc");

    wid = nct_get_varid(a0, "wetland");
    assert(wid>=0);
    for(int i=0; i<lajeja; i++)
	assert((varid[i] = nct_get_varid(a0, nimet[i])) >= 0);

    int pit = nct_get_varlen(a1->vars[wid]);
    double *v0, *v1, *w0=a0->vars[wid]->data, *w1=a1->vars[wid]->data;
    nct_vset u = {0};
    nct_add_dim(&u, nct_range_NC_DOUBLE(29.5, 29.5+55.4, 1), 55, NC_DOUBLE, "lat");
    nct_add_dim(&u, nct_range_NC_DOUBLE(-179.5, 180, 1),    360, NC_DOUBLE, "lon");
    int uid[] = {0,1};
    char kirjain[] = "HL";
    int merkki[] = {1,-1};
    for(int i=0; i<lajeja; i++) {
	int k=0;
    silmukka:
	v0 = a0->vars[varid[i]]->data;
	v1 = a1->vars[varid[i]]->data;
	//double cov2 = 2*gsl_stats_covariance(v0, 1, w0, 1, pit);
	double *data = calloc(pit, sizeof(double));
	sprintf(apu, "%s_%c", nimet[i], kirjain[k]);
	nct_add_var(&u, data, NC_DOUBLE, strdup(apu), 2, uid)->freeable_name=1;
	for(int i=0; i<pit; i++) {
	    if(w0[i] < 0.05) continue;
	    double s0 = v0[i]/w0[i];
	    double errw = w1[i]-w0[i];
	    double errv = v1[i]-v0[i];
	    double cov2 = 2*errw*errv;
	    data[i] = s0 + merkki[k] * s0*sqrt(gsl_pow_2(errv/v0[i]) + gsl_pow_2(errw/w0[i]) - cov2/(w0[i]*v0[i]));
	    data[i] *= data[i]>=0;
	}
	if(k++==0) {
	    nct_free_vset(a1);
	    assert(kirjain[k] == 'L');
	    a1 = nct_read_ncfile("BAWLD1x1_L.nc");
	    goto silmukka;
	}
    }
    nct_write_ncfile(&u, "wetland_hl.nc");
    nct_free_vset(&u);
    nct_free_vset(a0);
    nct_free_vset(a1);
}

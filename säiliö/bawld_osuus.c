#include <nctietue2.h>
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <string.h>
#define HAVE_INLINE
#include <gsl/gsl_statistics_double.h>
#include <gsl/gsl_math.h>

static const char* nimet[] = {"bog", "fen", "marsh", "permafrost_bog", "tundra_wetland"};

int main() {
    nct_vset *a0,*al,*ah;
    int lajeja = sizeof(nimet)/sizeof(*nimet);
    int varid[lajeja], wid;
    char apu[64];
    a0 = nct_read_ncfile("BAWLD1x1.nc");
    ah = nct_read_ncfile("BAWLD1x1_H.nc");
    al = nct_read_ncfile("BAWLD1x1_L.nc");

    wid = nct_get_varid(a0, "wetland");
    assert(wid>=0);
    for(int i=0; i<lajeja; i++) {
	assert((varid[i] = nct_get_varid(a0, nimet[i])) >= 0);
	assert(!strcmp(a0->vars[varid[i]]->name, ah->vars[varid[i]]->name));
    }

    int pit = nct_get_varlen(a0->vars[wid]);
    double *v0, *v1, *w[]={a0->vars[wid]->data, al->vars[wid]->data, ah->vars[wid]->data};
    nct_vset u = {0};
    nct_add_dim(&u, nct_range_NC_DOUBLE(29.5, 29.5+55.4, 1), 55, NC_DOUBLE, "lat");
    nct_add_dim(&u, nct_range_NC_DOUBLE(-179.5, 180, 1),    360, NC_DOUBLE, "lon");
    int uid[] = {0,1};
    int merkki[] = {-1,1};
    char* kirjain = "LH";
#ifndef PISTEITTÄIN
    double* apuv = malloc(pit*sizeof(double));
    double* apuw = malloc(pit*sizeof(double));
#endif

    for(int i=0; i<lajeja; i++) {
	double *v[] = {a0->vars[varid[i]]->data, al->vars[varid[i]]->data, ah->vars[varid[i]]->data};
	double *data[2];
	for(int k=0; k<2; k++) {
	    data[k] = calloc(pit, sizeof(double));
	    sprintf(apu, "%s_%c", nimet[i], kirjain[k]);
	    nct_add_var(&u, data[k], NC_DOUBLE, strdup(apu), 2, uid)
		-> freeable_name = 1;
	}

#ifdef PISTEITTÄIN
	for(int i=0; i<pit; i++) {
	    if(w[0][i] < 0.05) continue;
	    double s0 = v[0][i]/w[0][i];
	    for(int k=0; k<2; k++) {
		double errw = w[k+1][i] - w[0][i];
		double errv = v[k+1][i] - v[0][i];
		double cov2 = 2*errw*errv;
		data[k][i] = s0 + merkki[k]*s0*sqrt(gsl_pow_2(errv/v[0][i]) + gsl_pow_2(errw/w[0][i]) - cov2/(w[0][i]*v[0][i]));
		//data[i] *= data[i]>=0;
	    }
	}
#else
#define NCOV 10
#define VCOV (1.0/NCOV)
	double cov2[NCOV];
	double varw[NCOV];
	double varv[NCOV];
	for(int k=0; k<2; k++) {
	    for(int j=0; j<NCOV; j++) {
		double d0 = j*VCOV;
		double d1 = j<NCOV-1? (j+1)*VCOV: 1.01;
		int ind=0;
		for(int i=0; i<pit; i++) {
		    double s0 = v[0][i]/w[0][i];
		    if(!(d0<=s0 && s0<d1)) continue;
		    apuv[ind]   = v[k+1][i] - v[0][i];
		    apuw[ind++] = w[k+1][i] - w[0][i];
		}
		//cov2[j] = 2*gsl_stats_covariance(apuv, 1, apuw, 1, ind);
		varw[j] = gsl_stats_mean(apuw, 1, ind);
		varv[j] = gsl_stats_mean(apuv, 1, ind);
		for(int i=0; i<ind; i++)
		    apuw[i] *= apuv[i];
		cov2[j] = 2*gsl_stats_mean(apuw, 1, ind);
		//printf("%.2lf: %.4lf - %.4lf - %.4lf\t%s\n", d0, cov2[j], varw[j], varv[j], nimet[i]);
	    }

	    for(int i=0; i<pit; i++) {
		if(w[0][i] < 0.05) continue;
		double s0 = v[0][i]/w[0][i];
		int coi = (int)(s0*NCOV);
		data[k][i] = s0 + merkki[k]*s0*sqrt(gsl_pow_2(varv[coi]/v[0][i])
						    + gsl_pow_2(varw[coi]/w[0][i])
						    - cov2[coi]/(w[0][i]*v[0][i]));
	    }
	    //double errw = w[k+1][i] - w[0][i];
	    //double errv = v[k+1][i] - v[0][i];
	    //data[0][i] = s0 - s0*sqrt(gsl_pow_2(errv/v[0][i]) + gsl_pow_2(errw/w[0][i]) - cov2[coi]/(w[0][i]*v[0][i]));
	    //data[1][i] = s0 + s0*sqrt(gsl_pow_2(errv/v[0][i]) + gsl_pow_2(errw/w[0][i]) - cov2[coi]/(w[0][i]*v[0][i]));
	    //data[0][i] *= data[0][i]>=0;
	}
#endif
    }
    nct_write_ncfile(&u, "testi.nc");//wetland_hl.nc");
    nct_free_vset(&u);
    nct_free_vset(a0);
    nct_free_vset(ah);
    nct_free_vset(al);
#ifndef PISTEITTÄIN
    free(apuw);
    free(apuv);
#endif
}

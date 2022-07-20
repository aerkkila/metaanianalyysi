#include <stdio.h>
#include <stdlib.h>
#include <nctietue2.h>
#include <assert.h>

#define GSL_RANGE_CHECK_OFF
#define HAVE_INLINE
#include <gsl/gsl_multifit.h>
#include <gsl/gsl_statistics_double.h>

const char* vuomuutt = "flux_bio_prior";

#define ASTE 0.017453293
#define SUHT_ALA(lat, hila) (sin(((lat)+(hila)) * ASTE) - sin((lat) * ASTE)) * 100
#define PIT 19800
#define VAK 0
#define SEL 4

gsl_vector* luo_painovektori() {
    gsl_vector* vec = gsl_vector_alloc(PIT);
    for(int i=0; i<55; i++) {
	double paino = SUHT_ALA(29+i, 1);
	for(int j=0; j<360; j++)
	    gsl_vector_set(vec, i*360+j, paino);
    }
    return vec;
}

int main() {
    nct_vset vset[4] = {0};
    nct_var* var0;
    nct_read_ncfile_gd(vset+0, "./flux1x1.nc");
    nct_read_ncfile_gd(vset+1, "../lpx_data/LPX_area_peat.nc");
    nct_read_ncfile_gd(vset+2, "../lpx_data/LPX_area_inund.nc");
    nct_read_ncfile_gd(vset+3, "../lpx_data/LPX_area_wetsoil.nc");

    var0 = &NCTVAR(vset[0], vuomuutt);
    size_t pit = nct_get_varlen(var0);
    for(size_t i=0; i<pit; i++)
	((float*)var0->data)[i] = ((float*)var0->data)[i]*1e9;

    pit = nct_get_varlen(nct_varmean_first(var0));
    for(int i=1; i<4; i++)
	assert(nct_get_varlen(nct_varmeannan_first(&NCTVAR(vset[i], "data"))) == pit);
    assert(pit==PIT);

    gsl_matrix *xmatrix = gsl_matrix_alloc(pit, SEL);
    gsl_vector *yvec = gsl_vector_alloc(pit);
    gsl_vector *wvec = luo_painovektori();
    gsl_vector *cvec = gsl_vector_alloc(SEL);
    gsl_multifit_linear_workspace *work = gsl_multifit_linear_alloc(pit, SEL);
    gsl_matrix *covm = gsl_matrix_alloc(SEL, SEL);
    double chi2;
    switch(0) { // tekee sisäisistä muuttujista tiläpäiset
    case 0:;
	float* data[4];
	data[0] = NCTVAR(vset[0], vuomuutt).data;
	for(int i=1; i<4; i++)
	    data[i] = NCTVAR(vset[i], "data").data;

	for(size_t i=0; i<pit; i++)
	    gsl_vector_set(yvec, i, (double)data[0][i]);

	for(int i=0; i<pit; i++) {
	    gsl_matrix_set(xmatrix, i, 0, VAK);
	    for(int j=1; j<SEL; j++)
		gsl_matrix_set(xmatrix, i, j, (double)data[j][i]);
	}
    }

    float *data = var0->data; // ei jakseta alustaa uutta muistia
    var0->nonfreeable_data = 1;
    for(int i=0; i<4; i++)
	nct_free_vset(vset+i);

    gsl_multifit_wlinear(xmatrix, wvec, yvec, cvec, covm, &chi2, work);
    double r2 = 1 - (chi2 / gsl_stats_wtss(wvec->data, 1, yvec->data, 1, pit));

    gsl_vector_fprintf(stdout, cvec, "%.5lf");
    putchar('\n');
    gsl_matrix_fprintf(stdout, covm, "%.5lf");
    printf("\n%.5lf\n", r2);

    vset[0] = (nct_vset){0};
    nct_add_dim(vset, nct_range_NC_DOUBLE(29.5, 84, 1), 55, NC_DOUBLE, "lat");
    nct_add_dim(vset, nct_range_NC_DOUBLE(-179.5, 180, 1), 360, NC_DOUBLE, "lon");
    int dimids[] = {0,1};
    nct_add_var(vset, data, NC_FLOAT, "data", 2, dimids);

    for(int i=0; i<pit; i++) {
	float summa = 0;
	for(int j=0; j<SEL; j++)
	    summa += gsl_matrix_get(xmatrix, i, j)*cvec->data[j];
	data[i] = summa;
    }
    nct_write_ncfile(vset, "tehoisa_kosteikko.nc");

    nct_free_vset(vset);
    gsl_multifit_linear_free(work);
    gsl_matrix_free(xmatrix);
    gsl_vector_free(yvec);
    gsl_vector_free(wvec);
    gsl_vector_free(cvec);
    gsl_matrix_free(covm);
}

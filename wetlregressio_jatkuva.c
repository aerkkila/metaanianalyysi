#include <nctietue2.h>
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#define GSL_RANGE_CHECK_OFF
#define HAVE_INLINE
#include <gsl/gsl_multifit.h>
#include <gsl/gsl_fit.h>
#include <gsl/gsl_statistics.h>
#include <math.h>
#include <stdint.h>

const char* wetlnimet[]      = {"wetland", "bog", "fen", "marsh"};//, "tundra_wetland", "permafrost_bog"};
const char* kaudet[]         = {"whole_year", "summer", "freezing", "winter"};
enum                           {whole_year_e, summer_e, freezing_e, winter_e};
const char* pripost_sisään[] = {"flux_bio_prior", "flux_bio_posterior"};
const char* pripost_ulos[]   = {"pri", "post"};
#define kausi 0
#define ARRPIT(a) (sizeof(a)/sizeof(*(a)))

typedef struct {
    double *vuo;
    double *wdata[ARRPIT(wetlnimet)];
    double kerr[ARRPIT(kaudet)][ARRPIT(wetlnimet)];
    int resol;
    int aikaa;
    int pit;
    double *alat;
} data_t;

#if 0
double optimoi_neliösumma(data_t* dt, double summa0) {
    int kpit = ARRPIT(dt->kerr[kausi]);
    int muutt[kpit];
    int nmuutt = 0;
    for(int i=0; i<kpit; i++) {
	if(dt->kerr[kausi][i] == dt->kerr[kausi][i]) continue;
	dt->kerr[kausi][i] = 1;
	muutt[nmuutt++] = i;
    }
    nmuutt++; // vakiotermi

    gsl_matrix *xmatrix = gsl_matrix_alloc(dt->resol, nmuutt);
    gsl_vector *yvec = gsl_vector_alloc(dt->resol);
    gsl_vector *wvec = gsl_vector_alloc(dt->resol);
    gsl_vector *cvec = gsl_vector_alloc(nmuutt);
    gsl_multifit_linear_workspace *work = gsl_multifit_linear_alloc(dt->resol, nmuutt);
    gsl_matrix *covm = gsl_matrix_alloc(nmuutt, nmuutt);
    double chi2;
    for(size_t i=0; i<dt->resol; i++) {
	gsl_vector_set(yvec, i, dt->vuo[i]);
	gsl_vector_set(wvec, i, dt->alat[i]);
	gsl_matrix_set(xmatrix, i, 0, 1);
	for(int j=1; j<nmuutt; j++)
	    gsl_matrix_set(xmatrix, i, j, dt->wdata[j][i]);
    }
    
    gsl_multifit_wlinear(xmatrix, wvec, yvec, cvec, covm, &chi2, work);
    double r2 = 1 - (chi2 / gsl_stats_wtss(wvec->data, 1, yvec->data, 1, dt->resol));

    printf("r² = %.5lf\n", r2);
    gsl_multifit_linear_free(work);
    gsl_matrix_free(xmatrix);
    gsl_vector_free(yvec);
    gsl_vector_free(wvec);
    gsl_vector_free(cvec);
    gsl_matrix_free(covm);
}
#endif

void sovita(data_t* dt, int num, double* vakio, double* kulma, double* r2) {
    double chi2, cov00, cov01, cov11;
    gsl_fit_wlinear(dt->wdata[num], 1, dt->alat, 1, dt->vuo, 1, dt->pit, vakio, kulma, &cov00, &cov01, &cov11, &chi2);
    if(r2)
	*r2 = 1 - (chi2 / gsl_stats_wtss(dt->alat, 1, dt->vuo, 1, dt->pit));
}

int hae_alku(nct_var* v, struct tm* aika) {
    nct_anyd t = nct_mktime0(v, NULL);
    assert(t.d == nct_days);
    return (mktime(aika) - t.a.t) / 86400;
}

int main() {
    nct_vset wetlset = {0};
    nct_var *var;
    int ppnum = 1;
    data_t dt;
    int pit_;

    pit_ = ARRPIT(wetlnimet);
    nct_read_ncfile_gd(&wetlset, "BAWLD1x1.nc");
    for(int i=0; i<pit_; i++) {
	assert((var = nct_get_var(&wetlset, wetlnimet[i])));
	dt.wdata[i] = var->data;
    }

    dt.resol = nct_get_varlen(var);

    nct_vset *vuovs = nct_read_ncfile_info("flux1x1.nc");
    struct tm tm0 = {.tm_year=2012-1900, .tm_mon=8-1, .tm_mday=15};
    int alku = hae_alku(nct_get_var(vuovs, "time"), &tm0);
    dt.vuo = nct_load_var_with(nct_get_var(vuovs, pripost_sisään[ppnum]), -1, nc_get_var_double, sizeof(double))->data;
    assert((intptr_t)dt.vuo >= 0x800);
    dt.vuo += alku*dt.resol;

    struct tm tm1 = tm0;
    tm1.tm_year = 2014-1900;
    dt.aikaa = (mktime(&tm1) - mktime(&tm0)) / 86400;

    dt.alat = malloc(dt.resol*sizeof(double));
#define hila 1
#define ASTE 0.017453293
    int p1 = nct_get_varlen(nct_get_var(vuovs, "lon"));
    double *lat = nct_load_var_with(nct_get_var(vuovs, "lat"), -1, nc_get_var_double, sizeof(double))->data;
    int ind=0;
    do {
	double ala = sin(((double)lat[ind/p1]+hila*0.5) * ASTE) - sin(((double)lat[ind/p1]-hila*0.5) * ASTE); // suhteellinen pinta-ala
	for(int i=0; i<p1; i++)
	    dt.alat[ind++] = ala;
    } while(ind < dt.resol);

    /* Vuosta keskiarvo ajassa halutulta kaudelta ja jako kosteikon osuudella ja alueen valinta ja kaikki muukin. */
    nct_vset* vvv = nct_read_ncfile_info("kaudet2.nc");
    alku = hae_alku(nct_get_var(vvv, "time"), &tm0);
    var = nct_load_var(nct_next_truevar(vvv->vars[0], 0), -1);
    char* kausic = var->data + alku*dt.resol;
    dt.pit = 0;
    for(int r=0; r<dt.resol; r++) {
	if(!kausic[r]) continue;
	if(dt.wdata[0][r] < 0.1) continue;
	double summa=0;
	for(int i=1; i<ARRPIT(wetlnimet); i++)
	    summa += dt.wdata[i][r] / dt.wdata[0][r];
	if(summa < 0.97) continue;
	summa = 0;
	int nsumma = 0;
	if(kausi==whole_year_e) {
	    for(int t=0; t<dt.aikaa; t++)
		summa += dt.vuo[t*dt.resol + r];
	    nsumma = dt.aikaa;
	}
	else
	    for(int t=0; t<dt.aikaa; t++)
		if(kausic[t*dt.resol + r] == kausi) {
		    summa += dt.vuo[t*dt.resol + r];
		    nsumma++; }
		
	dt.vuo [dt.pit] = summa / nsumma / dt.wdata[0][r] * 1e9;
	dt.alat[dt.pit] = dt.alat[r];
	for(int i=1; i<ARRPIT(wetlnimet); i++)
	    dt.wdata[i][dt.pit] = dt.wdata[i][r] / dt.wdata[0][r];
	dt.pit++;
    }
    nct_free_vset(vvv);

    double vakio, kulma, r2;
    for(int i=1; i<ARRPIT(wetlnimet); i++) {
	sovita(&dt, i, &vakio, &kulma, &r2);
	printf("vakio = %7.4lf\tkulma = %8.4lf\tr² = %.5lf (%s)\n", vakio, kulma, r2, wetlnimet[i]);
    }

    nct_free_vset(&wetlset);
    nct_free_vset(vuovs);
    free(dt.alat);
}

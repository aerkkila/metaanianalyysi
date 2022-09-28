#if 0
'''
#endif
/* Tämä tiedosto on pätevää lähdekoodia sekä C:lle, että pythonille.
   Alussa on datan tuottava C-koodi, joka pythonin tapauksessa on kommentoitu ulos.
   Lopussa on data piirtävä python-koodi, jota kutsutaan tästä C-ohjelmasta, ja joka C:n tapauksessa on kommentoitu ulos.
   Pitää olla varovainen, ettei tekstimuokkain laita C-tilassa python-koodiin sarkainta ('\t').
*/

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
#define kausi 1
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

void luo_data(data_t* dt, char* kausic, double wraja) {
    dt->pit= 0;
    for(int r=0; r<dt->resol; r++) {
	if(!kausic[r]) continue;
	if(dt->wdata[0][r] < wraja) continue;
	double summa=0;
	for(int i=1; i<ARRPIT(wetlnimet); i++)
	    summa += dt->wdata[i][r] / dt->wdata[0][r];
	if(summa < 0.97) continue;
	summa = 0;
	int nsumma = 0;
	if(kausi==whole_year_e) {
	    for(int t=0; t<dt->aikaa; t++)
		summa += dt->vuo[t*dt->resol + r];
	    nsumma = dt->aikaa;
	}
	else
	    for(int t=0; t<dt->aikaa; t++)
		if(kausic[t*dt->resol + r] == kausi) {
		    summa += dt->vuo[t*dt->resol + r];
		    nsumma++; }

	if(!nsumma) continue;
	dt->vuo [dt->pit] = summa / nsumma / dt->wdata[0][r] * 1e9;
	dt->alat[dt->pit] = dt->alat[r];
	for(int i=1; i<ARRPIT(wetlnimet); i++)
	    dt->wdata[i][dt->pit] = dt->wdata[i][r] / dt->wdata[0][r];
	dt->pit++;
    }
}

#define sovita_monta(a,b,c) sovita_monta_(a,b,c,0)

void sovita_monta_(data_t* dt, double* kertoimet, double* r2, int nboot) {
    int nmuutt = ARRPIT(wetlnimet);
    gsl_matrix *xmatrix = gsl_matrix_alloc(dt->pit, nmuutt);
    gsl_vector *yvec = gsl_vector_alloc(dt->pit);
    gsl_vector *wvec = gsl_vector_alloc(dt->pit);
    gsl_vector *cvec = gsl_vector_alloc(nmuutt);
    gsl_multifit_linear_workspace *work = gsl_multifit_linear_alloc(dt->pit, nmuutt);
    gsl_matrix *covm = gsl_matrix_alloc(nmuutt, nmuutt);
    double sum2;

    for(int nb=0; nb<nboot; nb++) {
	for(size_t i=0; i<dt->pit; i++) {
	    int ind = rand() % dt->pit;
	    gsl_vector_set(yvec, i, dt->vuo[ind]);
	    gsl_vector_set(wvec, i, dt->alat[ind]);
	    gsl_matrix_set(xmatrix, i, 0, 1); // vakiotermi
	    for(int j=1; j<nmuutt; j++)
		gsl_matrix_set(xmatrix, i, j, dt->wdata[j][ind]);
	}
	gsl_multifit_wlinear(xmatrix, wvec, yvec, cvec, covm, &sum2, work);
	/* Tallennetaan vain haluttu lopullinen arvo. Alussa nmuutt+1 kpl on varattuja. */
	for(int i=0; i<nmuutt-1; i++)
	    kertoimet[i+nmuutt+1+nb*(nmuutt-1)] = cvec->data[i+1] + cvec->data[0];
    }

    for(size_t i=0; i<dt->pit; i++) {
	gsl_vector_set(yvec, i, dt->vuo[i]);
	gsl_vector_set(wvec, i, dt->alat[i]);
	gsl_matrix_set(xmatrix, i, 0, 1); // vakiotermi
	for(int j=1; j<nmuutt; j++)
	    gsl_matrix_set(xmatrix, i, j, dt->wdata[j][i]);
    }
    gsl_multifit_wlinear(xmatrix, wvec, yvec, cvec, covm, &sum2, work);
    *r2 = 1 - (sum2 / gsl_stats_wtss(wvec->data, 1, yvec->data, 1, dt->pit));
    for(int i=0; i<nmuutt; i++)
	kertoimet[i] = cvec->data[i];

    gsl_multifit_linear_free(work);
    gsl_matrix_free(xmatrix);
    gsl_vector_free(yvec);
    gsl_vector_free(wvec);
    gsl_vector_free(cvec);
    gsl_matrix_free(covm);
}

void sovittaminen_kerralla(data_t* dt, double kertoimet[]) {
    sovita_monta(dt, kertoimet, kertoimet+ARRPIT(wetlnimet));
    printf("r² = %.4lf\n", kertoimet[ARRPIT(wetlnimet)]);
    for(int i=0; i<ARRPIT(wetlnimet); i++)
	printf("%-12.4lf", kertoimet[i]);
    putchar('\n');
    for(int i=1; i<ARRPIT(wetlnimet); i++)
	printf("%-12.4lf", kertoimet[i]+kertoimet[0]);
    putchar('\n');
}

void sovita_1(data_t* dt, int num, double* vakio, double* kulma, double* r2) {
    double sum2, cov00, cov01, cov11;
    gsl_fit_wlinear(dt->wdata[num], 1, dt->alat, 1, dt->vuo, 1, dt->pit, vakio, kulma, &cov00, &cov01, &cov11, &sum2);
    *r2 = 1 - (sum2 / gsl_stats_wtss(dt->alat, 1, dt->vuo, 1, dt->pit));
}

void sovittaminen_erikseen(data_t* dt) {
    double vakio[ARRPIT(wetlnimet)], kulma[ARRPIT(wetlnimet)], r2;
    for(int i=1; i<ARRPIT(wetlnimet); i++) {
	sovita_1(dt, i, vakio+i, kulma+i, &r2);
	printf("vakio = %7.4lf\tkulma = %8.4lf\tyksi = %.4lf\tr² = %.5lf (%s)\n",
	       vakio[i], kulma[i], vakio[i]+kulma[i], r2, wetlnimet[i]);
    }
    double alat[ARRPIT(wetlnimet)] = {0};
    double summa = 0, ala = 0;
    for(int i=1; i<ARRPIT(wetlnimet); i++) {
	for(int r=0; r<dt->pit; r++)
	    alat[i] += dt->alat[r]*dt->wdata[i][r];
	summa += alat[i] * (vakio[i]+kulma[i]);
	ala += alat[i];
    }
    printf("keskiarvo = %.5lf\n", summa/ala);
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

    nct_read_ncfile_gd(&wetlset, "BAWLD1x1.nc");
    for(int i=0; i<ARRPIT(wetlnimet); i++) {
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
    tm1.tm_year = 2020-1900;
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

    nct_vset* vvv = nct_read_ncfile_info("kaudet2.nc");
    var = nct_load_var(nct_next_truevar(vvv->vars[0], 0), -1);
    alku = hae_alku(nct_get_var(vvv, "time"), &tm0);
    char* kausic = var->data + alku*dt.resol;

    int pit = ARRPIT(wetlnimet);
    int nboot = 500;
    FILE* f = popen("python ./wetlregressio_jatkuva.c", "w");
    assert(f);
    assert(fwrite(&pit, 4, 1, f) == 1);
    assert(fwrite(&nboot, 4, 1, f) == 1);

    double kertoimet[pit*(nboot+1) + 1];
    double kirj[pit + 1];
    for(double wraja=0.06; wraja<0.3; wraja+=0.01) {
	luo_data(&dt, kausic, wraja);
#if 0
	sovita_monta(&dt, kertoimet, kertoimet+pit);
	for(int i=1; i<pit; i++)
	    kirj[i-1] = kertoimet[i]+kertoimet[0];
	//kirj[pit-1] = kertoimet[pit]; // r²
	kirj[pit-1] = (double)dt.pit;
	kirj[pit] = wraja;
	assert(fwrite(kirj, sizeof(double), pit+1, f) == pit+1);
#endif
	sovita_monta_(&dt, kertoimet, kertoimet+pit, nboot);
	for(int i=1; i<pit; i++)
	    kirj[i-1] = kertoimet[i]+kertoimet[0];
	kirj[pit-1] = (double)dt.pit;
	kirj[pit] = wraja;
	assert(fwrite(kirj, sizeof(double), pit+1, f) == pit+1);

	assert(fwrite(kertoimet+pit+1, sizeof(double), (pit-1)*nboot, f) == (pit-1)*nboot);
    }
    pclose(f);

    nct_free_vset(vvv);
    nct_free_vset(&wetlset);
    nct_free_vset(vuovs);
    free(dt.alat);
}

#if 0
'''
from matplotlib.pyplot import *
import numpy as np
import sys, struct

def main():
    global tehtiin, datastot, rajastot, nimet
    rcParams.update({'figure.figsize':(12,10), 'font.size':13})
    raaka = sys.stdin.buffer.read(8)
    pit,nboot = struct.unpack("ii", raaka)
    ax = axes()
    #viivat, = ax.plot([], [])
    data = np.empty([0, pit+1], np.float64)
    alue = np.empty([0, pit-1, 2], np.float64)
    while(True):
        raaka = sys.stdin.buffer.read((pit+1)*8)
        if(len(raaka)==0):
            break
        dt = np.ndarray([1,pit+1], dtype=np.float64, buffer=raaka)
        data = np.concatenate([data, dt], axis=0)

        raaka = sys.stdin.buffer.read((pit-1)*nboot*8)
        dt = np.ndarray([nboot, pit-1], dtype=np.float64, buffer=raaka).T
        dt = np.percentile(dt, [5,95], axis=1).reshape([1,pit-1,2])
        alue = np.concatenate([alue, dt], axis=0)

    ax.plot(data[:,-1], data[:,:-2])
    ax.fill_between(data[:,-1], alue[:,0,0], alue[:,0,1], color='#ff000058')
    ax.fill_between(data[:,-1], alue[:,1,0], alue[:,1,1], color='#00ff0058')
    ax.fill_between(data[:,-1], alue[:,2,0], alue[:,2,1], color='#0000ff58')
    ax.twinx()
    plot(data[:,-1], data[:,-2], color='k')
    show()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

#endif

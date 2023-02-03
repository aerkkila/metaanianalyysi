#include <math.h>
#include <gsl/gsl_statistics.h>
#include <gsl/gsl_cdf.h>
#include <string.h>

#ifdef __cplusplus
#define restrict __restrict__
#endif

#define Int int
/* Muualla määriteltäköön mk_ytyyppi ja mk_xtyyppi. */

#define Var(n) ((n)*(n-1)*(2*n+5))
static double _mk_var(Int n, Int* määrät, Int n_määrät) {
    Int yhtsum = 0;
    for (Int i=0; i<n_määrät; i++)
	yhtsum += Var(määrät[i]);
    return (Var(n) - yhtsum) / 18.0;
}
#undef Var

/* Paras tapa laskea taulukosta yhtenevyydet riippuu datan tyypistä. 
   Käyttäjä voi määrittää, mitä menetelmää käytetään. */
#if defined mk_y0 && defined mk_y1
static double mk_var(const mk_ytyyppi* y, Int n) {
    Int määrät[mk_y1-mk_y0] = {0};
    for (Int i=0; i<n; i++)
	määrät[y[i]]++;
    return _mk_var(n, määrät, mk_y1-mk_y0);
}
#else
static double mk_var(const mk_ytyyppi* restrict y, Int n) {
    Int määrät[n];
    char ohi[n];
    memset(ohi, 0, n);
    Int määräind = 0;
    for (Int i=0; i<n; i++) {
	if (ohi[i])
	    continue;
	määrät[määräind] = 1;
	for (Int j=i+1; j<n; j++)
	    if (y[i] == y[j]) {
		ohi[j] = 1;
		määrät[määräind]++;
	    }
	määräind++;
    }
    return _mk_var(n, määrät, määräind);
}
#endif

static Int mk_score(const mk_ytyyppi* y, Int pit) {
    Int piste = 0;
    for (Int i=0; i<pit-1; i++)
	for (Int j=i+i; j<pit; j++)
	    piste += y[j] < y[i]? -1: y[j] > y[i]? 1: 0;
    return piste;
}

/* Pääfunktiot tästä eteenpäin. */

static float __attribute__((unused)) mannkendall(const mk_ytyyppi* y, Int pit) {
    Int s = mk_score(y, pit);
    if (s==0)
	return 1.0;
    double var_s = mk_var(y, pit);
    double s_ = s<0? s+1: s-1;
    s_ = s_ < 0? -s_: s_;
    return 2*(1-gsl_cdf_gaussian_P(s_, sqrt(var_s)));
}

/* X:n ei tarvitse olla tasavälinen, mutta pitää olla järjestyksessä. */
static float __attribute__((unused)) ts_kulmakerroin_yx(const mk_ytyyppi* y, const mk_xtyyppi* x, Int pit) {
    size_t n = (size_t)pit*(pit-1)/2;
    float* ker = malloc(n*sizeof(float));
    size_t ind = 0;
    for (Int i=0; i<pit-1; i++)
	for (Int j=i+1; j<pit; j++)
	    ker[ind++] = (double)(y[j] - y[i]) / (x[j] - x[i]);
    float ret = gsl_stats_float_median(ker, 1, ind);
    free(ker);
    return ret;
}

static float __attribute__((unused)) ts_vakiotermi_yx(float* y, const mk_xtyyppi* x, Int pit, float kulmakerroin) {
    float xmed = pit%2? x[pit/2]: (x[pit/2-1] + x[pit/2]) / 2.0;
    return gsl_stats_float_median(y, 1, pit) - xmed * kulmakerroin;
}

#ifdef __cplusplus
#undef restrict
#endif
#undef Int

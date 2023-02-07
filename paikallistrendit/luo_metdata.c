#include <nctietue2.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <err.h>

typedef double mk_ytyyppi;
typedef short mk_xtyyppi;
#include "mkts.c"

#define epäluku(a) (a==999)

static int hae_päivä(short vuosi, short päivä, time_t t0) {
    struct tm aikatm = {.tm_year=vuosi-1900, .tm_mday=1+päivä};
    time_t t1 = mktime(&aikatm);
    return (t1-t0) / 86400;
}

const char* kaudet[] = {"summer", "freezing", "winter"};
enum kausi_e           {summer_e,  freezing_e, winter_e};
const int kausia = sizeof(kaudet)/sizeof(*kaudet);

int main() {
    nct_vset* met_vs = nct_read_ncfile("../flux1x1.nc");
    time_t met_t0 = nct_mktime0(nct_get_var(met_vs, "time"), NULL).a.t;
    nct_var* met_v = nct_get_var(met_vs, "flux_bio_posterior");
    int resol = nct_get_varlen_from(met_v, 1);
    float* met = met_v->data;

    float kulma[2][resol];
    float mkulma[2][resol];

    nct_vset* kau_vs = nct_read_ncfile("/home/aerkkila/smos_uusi/kausien_päivät_int16.nc");
    nct_var* apu = &NCTDIM(*kau_vs, "vuosi");
    int vuosia = apu->len;
    int vuosi0 = nct_get_integer(apu, 0);

    for(int k=0; k<kausia; k++) {
	char nimi[32], *nptr;
	strcpy(nimi, kaudet[k]);
	nptr = nimi + strlen(nimi);
	strcpy(nptr, "_start");
	short* alut = nct_get_var(kau_vs, nimi)->data;
	strcpy(nptr, "_end");
	short* lopu = nct_get_var(kau_vs, nimi)->data;

	for(int r=0; r<resol; r++) {
	    short vuodet[vuosia];
	    double vuonyt[vuosia];
	    double vuomax[vuosia];
	    int vuosianyt = 0;
	    for(int v=0; v<vuosia; v++) {
		int a=alut[v*resol+r], b=lopu[v*resol+r];
		if(epäluku(a) || epäluku(b))
		    continue;
		int alku  = hae_päivä(vuosi0+v, a, met_t0);
		int loppu = hae_päivä(vuosi0+v, b, met_t0);

		/* tämän vuoden keski- ja huippuarvo */
		double x=0;
		double maxvuo = -1e9;
		for(int p=alku; p<loppu; p++) {
		    x += met[p*resol+r];
		    if(met[p*resol+r] > maxvuo)
			maxvuo = met[p*resol+r];
		}
		vuomax[vuosianyt] = maxvuo * 1e9;
		vuodet[vuosianyt] = v;
		vuonyt[vuosianyt++] = x / (loppu-alku) * 1e9;
	    }
	    if (vuosianyt < 3) {
		kulma[0][r] = 0/0.0;
		kulma[1][r] = 0/0.0;
		mkulma[0][r] = 0/0.0;
		mkulma[1][r] = 0/0.0;
		continue; }
	    kulma[0][r] = ts_kulmakerroin_yx(vuonyt, vuodet, vuosianyt) * 10;
	    float p     = mannkendall(vuonyt, vuosianyt);
	    kulma[1][r] = p < 0.05? kulma[0][r]: 0/0.0;

	    if(k == summer_e) {
		p = mannkendall(vuomax, vuosianyt);
		mkulma[0][r] = ts_kulmakerroin_yx(vuomax, vuodet, vuosianyt) * 10;
		mkulma[1][r] = p < 0.05? mkulma[0][r]: 0/0.0;
	    }
	}
	char ulos[] = "met_kau$.bin";
	*strchr(ulos, '$') = k + '0';
	int fd = open(ulos, O_WRONLY|O_CREAT|O_TRUNC, 0644);
	if(fd < 0) {
	    warn("open %i", k); continue; }
	if(write(fd, kulma, 2*resol*sizeof(*kulma)) < 0)
	    warn("write %i", k);
	close(fd);

	if(k == summer_e) {
	    fd = open("kesän_maxvuo.bin", O_WRONLY|O_CREAT|O_TRUNC, 0644);
	    if(write(fd, mkulma, 2*resol*sizeof(*kulma)) < 0)
		warn("write %i", k);
	    close(fd);
	}
    }
    nct_free_vset(kau_vs);
    nct_free_vset(met_vs);
}

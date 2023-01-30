#include <nctietue2.h>
#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

const double r2 = 6362.1320*6362.1320; // km, jotta luvut ovat maltillisempia
#define PINTAALA(lat, hila) ((hila) * r2 * (sin((lat)+0.5*(hila)) - sin((lat)-0.5*(hila))))
#define ASTE 0.017453293
#define Lat(i) (lat0+(i)/360)
#define Pintaala(i) PINTAALA(Lat(i)*ASTE, ASTE)

int montako_päivää(time_t aika0, int vuosi, short päivä) {
    struct tm aikatm = {
	.tm_year = vuosi-1900,
	.tm_mon  = 0,
	.tm_mday = 1+(int)päivä,
    };
    time_t kohdeaika = mktime(&aikatm);
    return (kohdeaika - aika0) / 86400;
}

const int ikirluokkia = 4;
typedef struct {
    short* s;
    int pit;
} spit;

spit lue_päivät() {
    static FILE* f;
    short data[20*ikirluokkia];
    int oli_f = !!f;
    if(!oli_f)
	f = fopen("kevät.csv", "r");
    while(fgetc(f) <= ' ');
    while(getc(f) != '\n'); // vuosirivi ohi
    int pit = 0, N=0, sanaind=0;
    char c;
    char sana[8];
    for(int i=0; i<ikirluokkia; i++) {
	while((c=fgetc(f)) != ',');
	sanaind = 0;
	do {
	    c=fgetc(f);
	    if(c == ',' || c == '\n') {
		sana[sanaind] = '\0';
		data[N++] = atoi(sana);
		sanaind=0;
	    }
	    else
		sana[sanaind++] = c;
	}
	while(c != '\n');
    }
    spit palaute;
    palaute.s = malloc(N*2);
    memcpy(palaute.s, data, 2*N);
    palaute.pit = N;
    if(oli_f)
	f = (fclose(f), NULL);
    return palaute;
}

int main() {
    int vuosi0 = 2011;
    int vuosia = 2021-vuosi0;
    spit alut_  = lue_päivät();
    spit loput_ = lue_päivät();
    assert(alut_.pit = ikirluokkia*vuosia);
    assert(loput_.pit = ikirluokkia*vuosia);
    short* alut = alut_.s;
    short* loput = loput_.s;
    nct_vset* ikirdata = nct_read_ncfile("../ikirdata.nc");
    char* ikir = nct_get_var(ikirdata, "luokka")->data;
    nct_var* ikirvuodet = nct_get_var(ikirdata, "vuosi");
    int ikirvuosi0 = nct_get_integer(ikirvuodet, 0);
    int ikirvuosia = nct_get_varlen(ikirvuodet);
    char* maski = nct_read_from_ncfile("../aluemaski.nc", "maski", NULL, -1);

    int ikir_v_ind[vuosia];
    for(int i=0; i<vuosia; i++) {
	ikir_v_ind[i] = vuosi0 - ikirvuosi0 + i;
	if(ikir_v_ind[i] >= ikirvuosia)
	    ikir_v_ind[i] = ikirvuosia-1;
    }

    nct_vset* vuovset = nct_read_ncfile("../flux1x1.nc");
    float* vuo = nct_get_var(vuovset, "flux_bio_posterior")->data;
    time_t aika0 = nct_mktime0(nct_get_var(vuovset, "time"), NULL).a.t;
    double lat0 = nct_get_floating(nct_get_var(vuovset, "lat"), 0);

    double summat[ikirluokkia][vuosia];
    memset(summat, 0, vuosia*ikirluokkia*sizeof(double));
    //double jakajat[vuosia];
    //memset(jakajat, 0, vuosia*sizeof(double));
    for(int r=0; r<19800; r++) {
	if(!maski[r])
	    continue;
	double ala = Pintaala(r);
	for(int v=0; v<vuosia; v++) {
	    int alku = alut[v];
	    int loppu = loput[v];
	    int päivä = montako_päivää(aika0, vuosi0+v, alku);
	    double summa = 0;
	    for(int i=alku; i<loppu; i++)
		summa += vuo[(päivä+i)*19800+r];
	    summat[ikir[19800*ikir_v_ind[v]+r]][v] += summa * ala * 86400 * (1.0079*4 + 12.01);
	    //jakajat[v] += ala * (loppu-alku);
	}
    }

    for(int ik=0; ik<ikirluokkia; ik++) {
	printf("\033[92mikirouta %i\033[0m\n", ik);
	for(int i=0; i<vuosia; i++)
	    printf("%.4lf\n", summat[ik][i]*1e-6);
    }

    nct_free_vset(vuovset);
    nct_free_vset(ikirdata);
    free(alut);
    free(loput);
}

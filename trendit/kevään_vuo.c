#include <nctietue2.h>
#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>
#include <err.h>

#ifdef KAUDET
typedef short mk_ytyyppi;
typedef double mk_xtyyppi;
#else
typedef double mk_ytyyppi;
typedef double mk_xtyyppi;
#endif
#include "mkts.c"

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
    intptr_t oli_f = (intptr_t)f;
    if(!oli_f)
	f = fopen("kevät.csv", "r");
    while(getc(f) <= ' ');
    while(getc(f) != '\n'); // vuosirivi ohi
    int N=0, sanaind=0;
    char c;
    char sana[8];
    for(int i=0; i<ikirluokkia; i++) {
	while((c=getc(f)) != ',');
	sanaind = 0;
	do {
	    c=getc(f);
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

#ifdef KAUDET
#define kopioi_y(y) float y[pit]; for(int i=0; i<pit; i++) y[i] = (*ptr)[i]
static void mkts_kaudet(float* kohde, const short* alku, short* loppu, const double* vuodet, int pit) {
    {
	const short** ptr = &alku;
	kopioi_y(y);
	kohde[0] = mannkendall(*ptr, pit);
	kohde[1] = ts_kulmakerroin_yx(*ptr, vuodet, pit);
	kohde[2] = ts_vakiotermi_yx(y, vuodet, pit, kohde[1]);
	kohde += 3;
    } {
	short** ptr = &loppu;
	kopioi_y(y);
	kohde[0] = mannkendall(*ptr, pit);
	kohde[1] = ts_kulmakerroin_yx(*ptr, vuodet, pit);
	kohde[2] = ts_vakiotermi_yx(y, vuodet, pit, kohde[1]);
	kohde += 3;
    } {
	short** ptr = &loppu;
	kopioi_y(y);
	for(int i=0; i<pit; i++) loppu[i]-=alku[i];
	kohde[0] = mannkendall(*ptr, pit);
	kohde[1] = ts_kulmakerroin_yx(*ptr, vuodet, pit);
	kohde[2] = ts_vakiotermi_yx(y, vuodet, pit, kohde[1]);
    }
}
#else
static void mkts(float* kohde, const double* summat, const double* jakajat, const double* vuodet, int vuosia) {
    float y[vuosia];
    /* emissiot */
    for(int i=0; i<vuosia; i++)
	y[i] = summat[i]; // vakiotermi määritetään muutettavasta float-taulukosta
    kohde[0] = mannkendall(summat, vuosia);
    kohde[1] = ts_kulmakerroin_yx(summat, vuodet, vuosia);
    kohde[2] = ts_vakiotermi_yx(y, vuodet, vuosia, kohde[1]);

    printf("\033[93m");
    for(int i=0; i<3; i++)
	printf(", %.4lf", kohde[i]);
    printf("\033[0m\n");

    /* vuot */
    for(int i=0; i<vuosia; i++)
	y[i] = jakajat[i]; // vakiotermi määritetään muutettavasta float-taulukosta
    kohde += 3*(ikirluokkia+1);
    kohde[0] = mannkendall(jakajat, vuosia);
    kohde[1] = ts_kulmakerroin_yx(jakajat, vuodet, vuosia);
    kohde[2] = ts_vakiotermi_yx(y, vuodet, vuosia, kohde[1]);

    for(int i=0; i<3; i++)
	printf(", %.4lf", kohde[i]);
    putchar('\n');
}
#endif

int main() {
    int vuosi0 = 2011;
    int vuosia = 2021-vuosi0;
    spit alut_  = lue_päivät();
    spit loput_ = lue_päivät();
    assert(alut_.pit == ikirluokkia*vuosia);
    assert(loput_.pit == ikirluokkia*vuosia);
    short* alut = alut_.s;
    short* loput = loput_.s;

    double vuodet[vuosia];
    for(int i=0; i<vuosia; i++)
	vuodet[i] = vuosi0+i;

#ifdef KAUDET
    float tulokset[3*ikirluokkia];
    for(int i=0; i<ikirluokkia; i++)
	mkts_kaudet(tulokset+3*3*i, alut, loput, vuodet, alut_.pit/ikirluokkia);

    int fd = open("kevään_päivät.bin", O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if(write(fd, tulokset, 3*3*ikirluokkia*sizeof(float)) != 3*3*ikirluokkia*sizeof(float))
	warn("write");
    close(fd);

#else
    char* maski = nct_read_from_ncfile("../aluemaski.nc", "maski", NULL, -1);
    nct_vset* vuovset = nct_read_ncfile("../flux1x1.nc");
    float* vuo = nct_get_var(vuovset, "flux_bio_posterior")->data;
    time_t aika0 = nct_mktime0(nct_get_var(vuovset, "time"), NULL).a.t;
    nct_vset* ikirdata = nct_read_ncfile("../ikirdata.nc");
    char* ikir = nct_get_var(ikirdata, "luokka")->data;
    nct_var* ikirvuodet = nct_get_var(ikirdata, "vuosi");
    int ikirvuosi0 = nct_get_integer(ikirvuodet, 0);
    int ikirvuosia = nct_get_varlen(ikirvuodet);
    double lat0 = nct_get_floating(nct_get_var(ikirdata, "lat"), 0);

    int ikir_v_ind[vuosia];
    for(int i=0; i<vuosia; i++) {
	ikir_v_ind[i] = vuosi0 - ikirvuosi0 + i;
	if(ikir_v_ind[i] >= ikirvuosia)
	    ikir_v_ind[i] = ikirvuosia-1;
	vuodet[i] = vuosi0+i;
    }


    double summat[ikirluokkia][vuosia];
    memset(summat, 0, vuosia*ikirluokkia*sizeof(double));
    double jakajat[ikirluokkia][vuosia];
    memset(jakajat, 0, vuosia*ikirluokkia*sizeof(double));
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
	    int ind = ikir[19800*ikir_v_ind[v]+r];
	    summat[ind][v] += summa * ala;// * 86400 * (1.0079*4 + 12.01);
	    jakajat[ind][v] += ala * (loppu-alku);
	}
    }
    free(maski);
    nct_free_vset(ikirdata);

    double s_emiss[vuosia];
    double s_vuo[vuosia];
    for(int i=0; i<vuosia; i++) {
	s_emiss[i] = 0;
	s_vuo[i] = 0;
	for(int j=0; j<ikirluokkia; j++) {
	    s_emiss[i] += summat[j][i];
	    s_vuo[i] += jakajat[j][i];
	}
	s_vuo[i] = s_emiss[i] / s_vuo[i] * 1e9;
	s_emiss[i] *= 1e-6 * 86400 * (1.0079*4 + 12.01);
    }

    for(int ik=0; ik<ikirluokkia; ik++) {
	for(int i=0; i<vuosia; i++) {
	    jakajat[ik][i] = summat[ik][i] / jakajat[ik][i] * 1e9; // jakaja on vastedes vuo
	    summat[ik][i] *= 1e-6 * 86400 * (1.0079*4 + 12.01);    // summa on vastedes emissio
	}
    }

    float tulokset[3*(ikirluokkia+1)*2];

    for(int i=0; i<ikirluokkia; i++)
	mkts(tulokset+3*i, summat[i], jakajat[i], vuodet, vuosia);
    mkts(tulokset+3*ikirluokkia, s_emiss, s_vuo, vuodet, vuosia);

    nct_free_vset(vuovset);

    int fd = open("kevät.bin", O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if(write(fd, tulokset, 3*(ikirluokkia+1)*sizeof(float)*2) < 0)
	warn("write");
    close(fd);

#endif
    free(alut);
    free(loput);
}

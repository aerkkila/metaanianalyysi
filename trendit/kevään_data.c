#include <nctietue2.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>
#include <err.h>
#include "../pintaalat.h"

#define lonpit 360

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

#define K(a,b) if(write(fd, a, b) != (b)) warn("write rivillä %i", __LINE__)

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

    /* Kirjoitetaan päivät. */
    int fd = open("kevään_päivät.bin", O_WRONLY|O_CREAT|O_TRUNC, 0644);
    if(fd < 0)
	warn("open rivillä %i\n", __LINE__);
    int ik = ikirluokkia;
    K(&vuosia,  1);
    K(&ik,      1);
    K(alut_.s,  alut_.pit*sizeof(short));
    K(loput_.s, alut_.pit*sizeof(short));
    close(fd);

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
	double ala = pintaalat[r/lonpit];
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

    fd = open("kevään_met.bin", O_WRONLY | O_CREAT | O_TRUNC, 0644);
    int pit = (ikirluokkia+1)*vuosia;
    K(&vuosia, 1);
    K(&ik, 1);
    K(vuodet,  vuosia * sizeof(double));
    K(summat,  pit    * sizeof(double));
    K(s_emiss, vuosia * sizeof(double));
    K(jakajat, pit    * sizeof(double));
    K(s_vuo,   vuosia * sizeof(double));
    close(fd);

    nct_free_vset(vuovset);
    free(alut);
    free(loput);
}

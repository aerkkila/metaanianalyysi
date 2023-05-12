#include <lz4.h>
#include <lz4frame.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <err.h>
#include <stdlib.h>
#include <stdio.h>
#include <nctietue3.h>
#include <string.h>
#include "muunnosalue.h"
#include <regex.h>
#include <assert.h>

#define kansio "raaka/"

typedef char mtyyppi;			// nämä kaksi riviä kuuluvat yhteen
const nc_type osuus_nctyyppi = NC_BYTE;	// nämä kaksi riviä kuuluvat yhteen

typedef char ptyyppi;

#if 0
static void pura(const void* pakattu_sis, size_t kokosis0, void* pakkaamaton_ulos, size_t kokoulos) {
    LZ4F_dctx* yhteys;
    if (LZ4F_isError(LZ4F_createDecompressionContext(&yhteys, LZ4F_VERSION))) {
	LZ4F_freeDecompressionContext(yhteys);
	puts("virhe");
	return; }

    LZ4F_decompressOptions_t valinnat = {.skipChecksums = 1};
    size_t kokosis = kokosis0;
    size_t kokoulosnyt = kokoulos;

    int tulos = kokosis;
    size_t tehtyä = 0;
    size_t luettua = 0;
    do {
	while ((tulos = LZ4F_decompress(yhteys,
			pakkaamaton_ulos+tehtyä, &kokoulosnyt,
			pakattu_sis+luettua, &kokosis, &valinnat)))
	{
	    if (LZ4F_isError(tulos))
		err(1, "decompress epäonnistui %i", tulos);
	    tehtyä += kokoulosnyt;
	    kokoulosnyt = kokoulos - tehtyä;
	    luettua += kokosis;
	    kokosis = tulos; // Tulos on vihje siitä, mikä on paras määrä antaa seuraavaksi.
	}
	tehtyä += kokoulosnyt;
	kokoulosnyt = kokoulos - tehtyä;
	luettua += kokosis;
	kokosis = kokosis0 - luettua;
    } while(tehtyä < kokoulos);

    LZ4F_freeDecompressionContext(yhteys);
}
#endif

/* 
 * purettu:
 *	koko = easex*easey;
 *	luetaan indeksillä (indeksit[jotain] + jotain_muuta)
 * muunnettu:
 *	koko = latpit*lonpit;
 *	kirjoitetaan indeksillä muunn_ind
 * indeksit:
 *	kertoo mistä kohdista purettua luetaan missäkin lat-lon-kohdassa
 *	koko = latpit*lonpit*vnta_maxpit;
 *	luetaan indeksillä indind0 + jotain
 */
static void muunna(ptyyppi* purettu, mtyyppi* muunnettu, size_t muunnettukoko, int *indeksit) {
    int muunn_ind = 0;
    int indind0   = 0;
    for(int j=0; j<alue.latpit; j++) {
	for(int i=0; i<alue.lonpit; i++) {
	    double summa = 0;
	    unsigned k, jakaja=0;
	    for(k=0; indeksit[indind0+k] >= 0; k++) {
		summa += purettu[indeksit[indind0+k]];
		jakaja += !!purettu[indeksit[indind0+k]]; // 0 on määrittelemätön
	    }
	    /* Vaaditaan puolet pisteistä määritellyn. */
	    muunnettu[muunn_ind++] = (jakaja >= k/2) * (summa / jakaja);
	    indind0 += vnta_maxpit;
	}
    }
}

void ota_vuosi(const char* restrict tied, int nmatch, regmatch_t* match, void* ulos) {
    ((int*)ulos)[nmatch] = atoi(tied+match[1].rm_so);
}

const char* regex = "raaka/.*-\\([0-9]\\{4\\}\\).*\\.nc$";

int main() {
    float lat[alue.latpit]; for(int i=0; i<alue.latpit; i++) lat[i] = alue.lat0+0.5*alue.väli + i*alue.väli;
    float lon[alue.lonpit]; for(int i=0; i<alue.lonpit; i++) lon[i] = alue.lon0+0.5*alue.väli + i*alue.väli;

    int* vuodet;
    nct_readflags = nct_rcoord;
    nct_set* set = nct_read_mfnc_regex_(regex, 0, "time", ota_vuosi, sizeof(int), 2, (void**)&vuodet);
    nct_var* var = nct_get_var(set, "PFR");
    nct_var* tvar = nct_get_dim(set, "time");
    int vuosia = tvar->len;

    int latlonres = alue.latpit*alue.lonpit;
    mtyyppi* muunnettu = malloc(latlonres*vuosia*sizeof(mtyyppi));
    mtyyppi* muunnettuptr = muunnettu;
    if(!muunnettu) err(1, "malloc muunnettu");

    int fd = open("muunnosindeksit.bin", O_RDONLY);
    if (fd < 0)
	err(1, "open muunnosindeksit.bin");
    struct stat st;
    fstat(fd, &st);
    int indpit = st.st_size;
    int* indeksit = mmap(NULL, indpit, PROT_READ, MAP_PRIVATE, fd, 0);
    close(fd);
    if (!indeksit) err(1, "mmap");

    for (int v=0; v<vuosia; v++) {
	printf("%i: %i / %i  \r", vuodet[v], v+1, vuosia), fflush(stdout);
	assert(vuodet[v] == vuodet[0] + v);
	nct_set_start(tvar, v);
	nct_set_length(tvar, 1);
	ptyyppi* alkup = nct_load(var)->data;
	muunna(alkup, muunnettuptr, latlonres, indeksit);
	muunnettuptr += latlonres;
    }
    printf("\033[K");
    nct_free1(set);

    /* Tallennetaan netcdf */
    int ncid, dimid[3], varid;
    if(nc_create("ikirdata.nc", NC_NETCDF4|NC_CLOBBER, &ncid) < 0)
	warn("epäonnistui");
    nc_set_fill(ncid, NC_NOFILL, NULL);
    /* aika */
    nc_def_dim(ncid, "vuosi", vuosia, dimid+0);
    nc_def_var(ncid, "vuosi", NC_INT, 1, dimid+0, &varid);
    nc_put_var(ncid, varid, vuodet);
    /* lat, lon */
    nc_def_dim(ncid, "lat", alue.latpit, dimid+1);
    nc_def_var(ncid, "lat", NC_FLOAT, 1, dimid+1, &varid);
    nc_put_var(ncid, varid, lat);
    nc_def_dim(ncid, "lon", alue.lonpit, dimid+2);
    nc_def_var(ncid, "lon", NC_FLOAT, 1, dimid+2, &varid);
    nc_put_var(ncid, varid, lon);
    /* data */
    nc_def_var(ncid, "luokka", NC_BYTE, 3, dimid, &varid);
    int osuusid;
    nc_def_var(ncid, "osuus", osuus_nctyyppi, 3, dimid, &osuusid);
    //nc_def_var_deflate(ncid, varid, 0, 1, 1); // pakataan, mutta nopeimalla tasolla
    nc_put_var(ncid, osuusid, muunnettu);
    for(int i=0; i<latlonres*vuosia; i++)
	muunnettu[i] =
	    muunnettu[i] < 10 ? 0 :
	    muunnettu[i] < 50 ? 1 :
	    muunnettu[i] < 90 ? 2 :
	    3;
    nc_put_var(ncid, varid, muunnettu);

    nc_close(ncid);

    munmap(indeksit, indpit);
    free(muunnettu);
    free(vuodet);
}

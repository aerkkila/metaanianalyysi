#include <unistd.h>
#include <fcntl.h>
#include <err.h>
#include <stdlib.h>
#include <stdio.h>
#include <proj.h>
#include <nctietue3.h>
#include "muunnosalue.h"

double x0, y0, xväli, yväli;
int xpit, ypit;
const char* easecoord = "+proj=laea +lat_0=90 +lon_0=0";

static void* muunnos() {
    int resol1 = xpit*ypit;
    float* lat = malloc(resol1*sizeof(float)*2);
    float* lon = lat+resol1;
    if (!lat)
	err(1, "malloc %li", resol1*sizeof(float)*2);

    PJ_CONTEXT* ctx = proj_context_create();
    PJ* pj = proj_create_crs_to_crs(ctx, easecoord, "+proj=longlat", NULL);
    if (!pj)
	errx(1, "proj_create_crs_to_crs");

    for(int j=0; j<ypit; j++) {
	printf("Luodaan muunnosta %i / %i\033[K\r", j+1, ypit), fflush(stdout);
	PJ_COORD pjc = {.xy.y = y0+yväli*0.5 + j*yväli}; // hilaruudun keskipiste
	for(int i=0; i<xpit; i++) {
	    pjc.xy.x = x0+xväli*0.5 + i*xväli; // hilaruudun keskipiste
	    PJ_LP lp = proj_trans(pj, 1, pjc).lp;
	    lat[j*xpit+i] = lp.phi;
	    lon[j*xpit+i] = lp.lam;
	}
    }

#if 0
    nct_set* set = nct_create_simple(lat, NC_FLOAT, ypit, xpit);
    nct_rename(nct_firstvar(set), "lat", 0);
    nct_add_var_alldims(set, lon, NC_FLOAT, "lon");
    nct_write_nc(set, "latlon.nc");
    nct_foreach(set, var)
	var->not_freeable = 1;
    nct_free1(set);
#endif

    proj_destroy(pj);
    proj_context_destroy(ctx);
    return lat;
}

static void lue_hila() {
    char* nimi = nct__get_filenames("raaka/.*\\.nc$", 0);
    nct_readm_ncf(set, nimi, nct_rlazy);
    free(nimi);

    nct_var* var = nct_loadg_as(&set, "x", NC_DOUBLE);
    xpit = var->len;
    x0 = ((double*)var->data)[0];
    double apu = ((double*)var->data)[1];
    xväli = apu-x0;

    /* Onhan hila tasavälinen. */
    long lväli = (long)(xväli*1000000);
    for (int i=2; i<xpit; i++) {
	double apu2 = ((double*)var->data)[i];
	if ((long)((apu2-apu)*1000000) != lväli)
	    printf("x: %li ≠ %li\n", (long)((apu2-apu)*1000000), lväli);
	apu = apu2;
    }

    var = nct_loadg_as(&set, "y", NC_DOUBLE);
    ypit = var->len;
    y0 = ((double*)var->data)[0];
    apu = ((double*)var->data)[1];
    yväli = apu-y0;

    lväli = (long)(yväli*1000000);
    for (int i=2; i<ypit; i++) {
	double apu2 = ((double*)var->data)[i];
	if ((long)((apu2-apu)*1000000) != lväli)
	    printf("y: %li ≠ %li\n", (long)((apu2-apu)*1000000), lväli);
	apu = apu2;
    }

    nct_free1(&set);
}

static int* tee_valintaindeksit(const char* maski) {
    int resol0 = alue.latpit*alue.lonpit;
    float* e2lat = muunnos();
    long xypit = xpit*ypit;
    float* e2lon = e2lat + xypit;

    /* Tämä muunnos selittyy kohdassa Muunnossilmukka. */
    PJ_CONTEXT* ctx = proj_context_create();
    PJ* pj = proj_create_crs_to_crs(ctx, "+proj=longlat", easecoord, NULL);

    float väli = alue.väli,
	  lat0 = alue.lat0,
	  lon0 = alue.lon0;
    int lonpit = alue.lonpit;

    int* indeksit = malloc(resol0*vnta_maxpit*sizeof(int));
    int juoksu=0;
    for(int j=0; j<alue.latpit; j++) {
	float latnyt = lat0 + j*väli;
	PJ_COORD pjc = {.lp.phi = latnyt};
	for(int i=0; i<alue.lonpit; i++) {
	    printf("%i / %i\033[K\r", ++juoksu, resol0), fflush(stdout);
	    float lonnyt = lon0 + i*väli;
	    pjc.lp.lam = lonnyt;
	    int valintapit = 0;
	    int* valinta = indeksit + (j*lonpit+i)*vnta_maxpit;

	    /* Muunnossilmukka:
	       Voitaisiin käydä läpi koko e2lat ja e2lon -taulukko
	       niiden kohtien löytämiseksi, joissa ease2-ruudun keskikohta on lat-lon-ruudun sisäpuolella.
	       Tässä kuitenkin on optimoitu hakemalla koordinaatin käänteismuunnoksella
	       kys. taulukoista lat-lon-ruudun alanurkkaa vastaava kohta.
	       Sitten kys. taulukoista (e2lat, e2lon) käydään läpi vain kyseisen kohdan lähellä olevat pisteet. */
	    PJ_XY xy = proj_trans(pj, 1, pjc).xy;
	    int ky0 = (xy.y-y0) / yväli, // xy sisältää ease2-koordinaatit, mutta halutaan indeksit
		kx0 = (xy.x-x0) / xväli;

	    /* Indeksit pitää tarkistaa yllättävän laajalta alueelta. */
	    int ytaakse = ky0 > 300 ? 300 : ky0;
	    int xtaakse = kx0 > 300 ? 300 : kx0;
	    int yeteen  = ky0 < ypit-400 ? 400 : ypit-ky0;
	    int xeteen  = kx0 < xpit-400 ? 400 : xpit-kx0;
	    for(int ky=ky0-ytaakse; ky<ky0+yeteen; ky++) {
		for(int kx=kx0-xtaakse; kx<kx0+xeteen; kx++) {
		    int k = ky*xpit+kx;
		    if (k < 0 || k>=xypit || e2lon[k]<lonnyt || e2lon[k]>lonnyt+väli || e2lat[k]<latnyt || e2lat[k]>latnyt+väli)
			continue;
		    if (!maski[k])
			continue;
		    valinta[valintapit++] = k;
#ifdef DEBUG
		    if (valintapit >= vnta_maxpit)
			err(1, "vnta_maxpit-arvoa (%i) pitää kasvattaa\n\n", vnta_maxpit);
#endif
		}
	    }
	    valinta[valintapit] = -1;
	}
    }

    proj_destroy(pj);
    proj_context_destroy(ctx);

    free(e2lat);
    return indeksit;
}

int main() {
    lue_hila();
    char* maski = nct_read_from_nc("create_landmask/landmask.nc", "data");
    int* indeksit = tee_valintaindeksit(maski);
    int resol0 = alue.latpit * alue.lonpit;

    int* dt = indeksit;
    int* pisteitä = malloc(resol0*sizeof(int));
    for(int i=0; i<resol0; i++) {
	int n = -1;
	while(dt[++n] >= 0);
	dt += vnta_maxpit;
	pisteitä[i] = n;
    }
    nct_set* set = nct_create_simple(pisteitä, NC_INT, alue.latpit, alue.lonpit);
    nct_write_nc(set, "pisteitä.nc");
    nct_free1(set);

    int fd = open("muunnosindeksit.bin", O_WRONLY|O_CREAT, 0644);
    if(write(fd, indeksit, resol0*vnta_maxpit*sizeof(int)) < 0)
	warn("write");
    close(fd);

    free(maski);
    free(indeksit);
}

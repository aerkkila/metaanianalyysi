#include <shapefil.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <netcdf.h>
#include <math.h>
#include <proj.h>
#include <err.h>
#include <nctietue3.h>

#define Printf(...) do { if(verbose) printf(__VA_ARGS__); } while(0)
#define NCVIRHE(arg) printf("\033[1;31mNetcdf-virhe (%s: %i):\033[0m %s\n", __FILE__, __LINE__, nc_strerror(arg))
#define NCFUNK(fun, ...)			\
    do {					\
	if((ncpalaute = fun(__VA_ARGS__))) {	\
	    NCVIRHE(ncpalaute);			\
	    exit(1);				\
	}					\
    } while(0)

typedef struct{ double a[2]; } piste;
typedef struct{ int alku; int loppu; int nro; } Arg;

static void kirjoita();
static void kirjoita_netcdf(const char*);
static void muunna_olio(SHPObject*, PJ*, int);
static int sign(double);

static const char* tiednimet[]	 = {"ne_10m_land/ne_10m_land", "ne_10m_lakes/ne_10m_lakes"};
static const char* nc_kirj_nimi	 = "landmask.nc";
static const char* nc_luett_nimi = "../raaka/ESACCI-PERMAFROST-L4-PFR-MODISLST_CRYOGRID-AREA4_PP-2018-fv03.0.nc";
static const char* shp_coord	 = "+proj=longlat";
static const char* nc_coord	 = "+proj=laea +lat_0=90 +lon_0=0";

static const int tiedostoja = sizeof(tiednimet)/sizeof(tiednimet[0]);

static int nEnt, shptype, verbose, ncpalaute, ncid;
SHPObject** shpoliot;
size_t xpit, ypit, xypit;
double *x, *y;

char* muutosmaski;
char* ymuutokset;

int main(int argc, char** argv) {
    int id;

    for(int i=1; i<argc; i++)
	if (!strcmp(argv[i], "--verbose") || !strcmp(argv[i], "-v"))
	    verbose = 1;

    /* luetaan netcdf-tiedostosta koordinaatit */
    Printf("Luetaan %s\n", nc_luett_nimi);
    NCFUNK(nc_open, nc_luett_nimi, NC_NOWRITE, &ncid);
    NCFUNK(nc_inq_dimid, ncid, "x", &id);		// x
    NCFUNK(nc_inq_dim, ncid, id, NULL, &xpit);
    x = malloc(xpit*sizeof(double));
    NCFUNK(nc_inq_varid, ncid, "x", &id);
    NCFUNK(nc_get_var_double, ncid, id, x);
    NCFUNK(nc_inq_dimid, ncid, "y", &id);		// y
    NCFUNK(nc_inq_dim, ncid, id, NULL, &ypit);
    y = malloc(xpit*sizeof(double));
    NCFUNK(nc_inq_varid, ncid, "y", &id);
    NCFUNK(nc_get_var_double, ncid, id, y);
    NCFUNK(nc_close, ncid);

    /*
    x += xpit / 3 + xpit / 8 + xpit / 20;
    xpit /= 20;
    y += ypit / 2 + ypit / 7 + ypit / 30;
    ypit /= 10;*/

    xypit = xpit*ypit;
    muutosmaski = calloc(xypit, 1);
    ymuutokset = calloc(ypit, 1);
    PJ_CONTEXT* ctx = proj_context_create();
    PJ* pj = proj_create_crs_to_crs(ctx, shp_coord, nc_coord, NULL);

    for(int tiedosto=0; tiedosto<tiedostoja; tiedosto++) {
	Printf("Luetaan %s\n", tiednimet[tiedosto]);
	SHPHandle shpkahva = SHPOpen(tiednimet[tiedosto], "r");
	double shpmin[4], shpmax[4];
	SHPGetInfo(shpkahva, &nEnt, &shptype, shpmin, shpmax);
	if(shptype != SHPT_POLYGON) {
	    fprintf(stderr, "\033[31mVirhe:\033[0m Shapefilen-tyyppi ei ole SHPT_POLYGON\n");
	    SHPClose(shpkahva);
	    return 1;
	}
	Printf("nEnt = %i\n", nEnt);
	shpoliot = malloc(nEnt*sizeof(void*));
	if (!pj)
	    errx(1, "proj_create_crs_to_crs");
	for(int i=0; i<nEnt; i++) {
	    shpoliot[i] = SHPReadObject(shpkahva,i);
	    for(int j=0; j<shpoliot[i]->nParts; j++)
		if (shpoliot[i]->panPartType[j] != SHPP_RING)
		    fprintf(stderr, "\033[31mVirhe:\033[0m Shapeolion-tyyppi ei ole SHPP_RING\n");
	    muunna_olio(shpoliot[i], pj, i);
	}
	for(int i=0; i<nEnt; i++)
	    SHPDestroyObject(shpoliot[i]);
	SHPClose(shpkahva);
	free(shpoliot); shpoliot = NULL;
    }

    kirjoita();
    proj_destroy(pj);
    proj_context_destroy(ctx);
    free(muutosmaski);
    free(ymuutokset);
    free(x);
    free(y);
    return 0;
}

#define vaihda(a, b) do {typeof(a) __apu=a; a=b; b=__apu;} while(0)

static void kirjoita() {
    char* maski = malloc(xpit*ypit);
    char arvo0 = 0;
    for(int j=0; j<ypit; j++) {
	if (ymuutokset[j]%2)
	    arvo0 = !arvo0;
	char arvo = arvo0;
	int y = j*xpit;
	maski[y] = arvo; // ensimmainen otetaan y-maskista ja sitten x-maskista
	for(int i=1; i<xpit; i++) {
	    if (muutosmaski[y+i]%2)
		arvo = !arvo;
	    maski[y+i] = arvo;
	}
    }
    kirjoita_netcdf(maski);
    free(maski);
}

static void muutosmaskiin(double x0, double y0, double x1, double y1) {
    double xväli = x[1] - x[0];
    double yväli = y[1] - y[0];
    double xind0 = (x0 - x[0]) / xväli;
    double xind1 = (x1 - x[0]) / xväli;
    double yind0 = (y0 - y[0]) / yväli;
    double yind1 = (y1 - y[0]) / yväli;
    double kulma = (xind1 - xind0) / (yind1 - yind0);
    if (!(-1e20 < kulma && kulma < 1e20))
	return;
    double vakio = xind0 - kulma*yind0;
    int rivi1 = round(yind1);
    double suunta = sign(yind1-yind0);
    for (int rivi = round(yind0); ; rivi+=suunta) {
	if (!(0 <= rivi && rivi < ypit))
	    goto Continue;
	if ((yind0 < rivi || yind1 < rivi) &&
		(yind0 > rivi || yind1 > rivi)) {
	    int xind = round(kulma*rivi + vakio);
	    if (xind < 0 || xpit <= xind)
		goto Continue;
	    int ind = (int)rivi*xpit + xind;
	    muutosmaski[ind]++;
	}
Continue:
	if (rivi==rivi1)
	    break;
    }
    if ((round(xind0) <= 0 && round(xind1) > 0) || (round(xind0) >= 0 && round(xind1) < 0)) {
	int rivi = round(yind0 - 1/kulma * xind0);
	if (0 <= rivi && rivi < ypit)
	    ymuutokset[rivi]++;
    }
}

static void muunna_olio(SHPObject* olio, PJ* pj, int olionum) {
    for(int ring=0; ring<olio->nParts; ring++) {
	int loppu = ring == olio->nParts-1 ? olio->nVertices : olio->panPartStart[ring+1];
	double ymax, xmax, ymin, xmin;
	ymax = xmax = -1e20;
	ymin = xmin = 1e20;
	int eialku = 0;
	for(int i=olio->panPartStart[ring]; i<loppu; i++) {
	    printf("%i: %i / %i\r", olionum, i, olio->nVertices), fflush(stdout);
	    PJ_COORD projpiste = {.xy = {.x=olio->padfX[i], .y=olio->padfY[i]}};
	    PJ_XY uusi = proj_trans(pj, 1, projpiste).xy;
	    olio->padfX[i] = uusi.x;
	    olio->padfY[i] = uusi.y;
	    if (eialku)
		muutosmaskiin(olio->padfX[i-1], olio->padfY[i-1], olio->padfX[i], olio->padfY[i]);
	    eialku = 1;
	    if (uusi.x > xmax)
		xmax = uusi.x;
	    if (uusi.x < xmin)
		xmin = uusi.x;
	    if (uusi.y > ymax)
		ymax = uusi.y;
	    if (uusi.y < ymin)
		ymin = uusi.y;
	}
    }
}

void kirjoita_netcdf(const char* maski) {
    int ncid, yid, xid, varid;
    NCFUNK(nc_create, nc_kirj_nimi, NC_CLOBBER|NC_NETCDF4, &ncid);
    NCFUNK(nc_set_fill, ncid, NC_NOFILL, NULL);
    NCFUNK(nc_def_dim, ncid, "y", ypit, &yid);
    NCFUNK(nc_def_var, ncid, "y", NC_DOUBLE, 1, &yid, &varid);
    NCFUNK(nc_put_var, ncid, varid, y);
    NCFUNK(nc_def_dim, ncid, "x", xpit, &xid);
    NCFUNK(nc_def_var, ncid, "x", NC_DOUBLE, 1, &xid, &varid);
    NCFUNK(nc_put_var, ncid, varid, x);
    int xyid[] = {yid, xid};
    NCFUNK(nc_def_var, ncid, "data", NC_BYTE, 2, xyid, &varid);
    NCFUNK(nc_put_var, ncid, varid, maski);
    NCFUNK(nc_close, ncid);
}

long käytyjä = 0;

static int sign(double a) {
    return (a<0)? -1: 1;
}

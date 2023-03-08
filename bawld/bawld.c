/* Kääntäjä tarvitsee argumentit -lm -lnetcdf -lshp -lproj -pthread */

#include <shapefil.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>
#include <netcdf.h>
#include <proj.h>
#include <math.h>
#include <err.h>
#include <assert.h>

#define Printf(...) do { if(verbose) printf(__VA_ARGS__); } while(0)
#define NCVIRHE(arg) printf("\033[1;31mNetcdf-virhe:\033[0m %s\n", nc_strerror(arg))
#define NCFUNK(fun, ...)			\
    do {					\
	if((ncpalaute = fun(__VA_ARGS__))) {	\
	    NCVIRHE(ncpalaute);			\
	    exit(1);				\
	}					\
    } while(0)

/*näistä yhtä muutettaessa pitää tarkistaa muutkin kentät*/
typedef double dbftyyppi;
#define DBFTYYPPI_ENUM FTDouble //tämä vaikuttaa myös seuraavaan riviin
#define DBFRead_tyyppi_Attribute(...) DBFReadDoubleAttribute(__VA_ARGS__)
typedef double nc_kirj_tyyppi; //tämä vaikuttaa myös seuraavaan riviin
#define NC_KIRJTYYPPI_ENUM NC_DOUBLE
typedef struct {
    double a[2];
} piste;
typedef struct {
    int alku, loppu, nro, *indeksit;
} Arg;

void* selaa_oliot(void*);
int piste_polygonissa(double x, double y, SHPObject* olio);
double kulma(piste keha1, piste keha2, piste kanta);
double ristitulo(piste p0, piste p1);
int sign(double);
piste suuntavektori(piste p0, piste p1);
double vektpituus(piste p);
double pistetulo(piste a, piste b);

static const char* tiednimi = "data/BAWLD_V1";
static const char* nc_luett_nimi = "aluemaski.nc";
static const char* nc_kirj_nimi = "bawld.nc";

static int nEnt, shptype, verbose, njobs=1, ncpalaute, arg_luettu, ncid, luokkia;
SHPObject** shpoliot;
size_t pit_lat, pit_lon, pit_latlon;
double *lat, *lon;

struct {
    char *a, *b;
} tunnisteet[] =
{
#include "bawldtunnisteet.h"
};

const double rad = 3.14159265358979/180;
const double lat0=90*rad, lon0=0*rad;
double sinlon0=NAN, coslon0=NAN;

#if 0
piste lambert(double lat, double lon) { // -> x,y
    lat *= rad;
    lon *= rad;
    double sinlat_ = sin(lat-lat0);
    double coslat_ = cos(lat-lat0);
    double sinlon = sin(lon);
    double coslon = cos(lon);
    double k = sqrt(2/(1 + sinlon0*sinlon + coslon0*coslon*coslat_));
    return (piste){{
	k*coslon*sinlat_,
	k*(coslon0*sinlon - sinlon0*coslon*coslat_),
    }};
}
#endif

int lue_dbf(DBFHandle dbfkahva, const char* dbfnimi, dbftyyppi* dbfdata) {
    int id = DBFGetFieldIndex(dbfkahva, dbfnimi);
    if (id < 0) {
	fprintf(stderr, "\033[31mVirhe:\033[0m .dbf-tiedostosta ei löytynyt kenttää %s.\n", dbfnimi);
	DBFClose(dbfkahva);
	return 1;
    }
    if (DBFGetFieldInfo(dbfkahva, id, NULL, NULL, NULL) != DBFTYYPPI_ENUM) {
	fprintf(stderr, "\033[31mVirhe:\033[0m kentän %s tyyppi oli väärä.\n", dbfnimi);
	DBFClose(dbfkahva);
	return 1;
    }
    int apu;
    if ((apu=DBFGetRecordCount(dbfkahva)) != nEnt) {
	fprintf(stderr, "\033[31mVirhe:\033[0m RecordCount(dbf) = %i, nEnt(shp) = %i\n", apu, nEnt);
	DBFClose(dbfkahva);
	return 1;
    }
    for(int i=0; i<nEnt; i++)
	dbfdata[i] = DBFRead_tyyppi_Attribute(dbfkahva, i, id) * 0.01;
    return 0;
}

int alusta_netcdf() {
    int ncid, latid, lonid, varid;
    NCFUNK(nc_create, nc_kirj_nimi, NC_CLOBBER|NC_NETCDF4, &ncid);
    NCFUNK(nc_def_dim, ncid, "lat", pit_lat, &latid);
    NCFUNK(nc_def_var, ncid, "lat", NC_DOUBLE, 1, &latid, &varid);
    NCFUNK(nc_put_var, ncid, varid, lat);
    NCFUNK(nc_def_dim, ncid, "lon", pit_lon, &lonid);
    NCFUNK(nc_def_var, ncid, "lon", NC_DOUBLE, 1, &lonid, &varid);
    NCFUNK(nc_put_var, ncid, varid, lon);
    assert(latid == 0 && lonid == 1); // ei jakseta palauttaa näitä, vaan oletetaan arvo
    return ncid;
}

void kirjoita_netcdf(int ncid, void* data, const char* nimi) {
    int latlonid[] = {0,1}, varid;
    NCFUNK(nc_def_var, ncid, nimi, NC_KIRJTYYPPI_ENUM, 2, latlonid, &varid);
    NCFUNK(nc_put_var, ncid, varid, data);
}

int main(int argc, char** argv) {
    int id;
#define Switch(a) do { char* _switchc = a; if(0)
#define Case(a,b) else if(!strcmp(_switchc, a) || !strcmp(_switchc, b))
#define End } while(0)
    for(int i=1; i<argc; i++) {
	Switch(argv[i]);
	Case("-v", "--verbose")
	    verbose = 1;
	Case("-j", "--njobs")
	    sscanf(argv[++i], "%i", &njobs);
	Case("-o", "--out")
	    nc_kirj_nimi = argv[++i];
	Case("-i", "--in")
	    tiednimi = argv[++i];
	End;
    }
#undef Switch
#undef Case
#undef End

    coslon0 = cos(lon0);
    sinlon0 = sin(lon0);

    /* Luetaan nEnt, shpmin, shpmax
     * ja tarkistetaan shptype. */
    Printf("Luetaan %s\n", tiednimi);
    SHPHandle shpkahva = SHPOpen(tiednimi, "r");
    double shpmin[4], shpmax[4];
    SHPGetInfo(shpkahva, &nEnt, &shptype, shpmin, shpmax);
    if(shptype != SHPT_POLYGON) {
	fprintf(stderr, "\033[31mVirhe:\033[0m Shapefilen-tyyppi ei ole SHPT_POLYGON\n");
	SHPClose(shpkahva);
	return 1;
    }
    /* Luetaan shpoliot. */
    Printf("nEnt = %i\n", nEnt);
    shpoliot = malloc(nEnt*sizeof(void*));
    for(int i=0; i<nEnt; i++) {
	shpoliot[i] = SHPReadObject(shpkahva,i);
	for(int j=0; j<shpoliot[i]->nParts; j++)
	    if(shpoliot[i]->panPartType[j] != SHPP_RING)
		fprintf(stderr, "\033[31mVirhe:\033[0m Shapeolion-tyyppi ei ole SHPP_RING\n");
    }
    SHPClose(shpkahva);
  
    /* Vastaava .dbf-tiedosto sisältää shapefilen geometriaan kuuluvan datan. */
    dbftyyppi* dbfdata = malloc((nEnt+1)*sizeof(dbftyyppi));
    dbfdata[nEnt] = NAN;
    DBFHandle dbfkahva = DBFOpen(tiednimi, "r");
    if(!dbfkahva)
	err(1, "rivi %i, DBFOpen", __LINE__);

    /* luetaan netcdf:stä hila */
    Printf("Luetaan %s\n", nc_luett_nimi);
    NCFUNK(nc_open, nc_luett_nimi, NC_NOWRITE, &ncid);

    NCFUNK(nc_inq_dimid, ncid, "lat", &id);            //lat
    NCFUNK(nc_inq_dim, ncid, id, NULL, &pit_lat);
    lat = malloc(pit_lat*sizeof(double));
    NCFUNK(nc_inq_varid, ncid, "lat", &id);
    NCFUNK(nc_get_var_double, ncid, id, lat);

    NCFUNK(nc_inq_dimid, ncid, "lon", &id);            //lon
    NCFUNK(nc_inq_dim, ncid, id, NULL, &pit_lon);
    lon = malloc(pit_lon*sizeof(double));
    NCFUNK(nc_inq_varid, ncid, "lon", &id);
    NCFUNK(nc_get_var_double, ncid, id, lon);

    NCFUNK(nc_close, ncid);
    pit_latlon = pit_lat*pit_lon;
    Printf("pit_lat = %zu\t pit_lon = %zu\t pit_latlon = %zu\n", pit_lat, pit_lon, pit_latlon);
    luokkia = sizeof(tunnisteet)/sizeof(*tunnisteet);

    /* Luodaan säikeet, joilla haetaan indeksit. */
    int* indeksit = malloc(pit_latlon*5*sizeof(unsigned));
    pthread_t saikeet[njobs-1];
    Arg arg = {.loppu=pit_lon/njobs, .indeksit=indeksit};
    for(int i=0; i<njobs-1; i++) {
	pthread_create(saikeet+i, NULL, selaa_oliot, &arg);
	while(!arg_luettu)
	    usleep(10);
	arg_luettu = 0;
	arg.alku = arg.loppu;
	arg.loppu += pit_lon/njobs;
	arg.nro++;
    }
    arg.loppu = pit_lon;
    selaa_oliot(&arg);
    for(int i=0; i<njobs-1; i++)
	pthread_join(saikeet[i], NULL);

    int nckahva = alusta_netcdf();
    nc_kirj_tyyppi* ncdata = malloc(pit_latlon * sizeof(nc_kirj_tyyppi));
    for(int luokka=0; luokka<luokkia; luokka++) {
	if(lue_dbf(dbfkahva, tunnisteet[luokka].a, dbfdata)) {
	    printf("lue_dbf %s (%s) epäonnistui\n", tunnisteet[luokka].a, tunnisteet[luokka].b);
	    continue; }
	for(int i=0; i<pit_latlon; i++) {
	    ncdata[i] = 0;
	    int j;
	    for(j=0; indeksit[i*5+j]>=0; j++)
		ncdata[i] += dbfdata[indeksit[i*5+j]];
	    assert(j<5);
	    if(ncdata[i] > 0)
		ncdata[i] /= j;
	}
	kirjoita_netcdf(nckahva, ncdata, tunnisteet[luokka].b);
    }
    NCFUNK(nc_close, nckahva);
    DBFClose(dbfkahva);
    free(dbfdata);
    free(ncdata);
    free(lat);
    free(lon);
    free(indeksit);
    for(int i=0; i<nEnt; i++)
	SHPDestroyObject(shpoliot[i]);
    free(shpoliot); shpoliot = NULL;
}

/* Aivan liikaa argumentteja. Pitäisi olla viite tietueeseen. */
int hae_piste(PJ* pj, double la, double lo, int* taul, int alku, int ind) {
    PJ_XY xy = proj_trans(pj, 1, (PJ_COORD){.lp={lo, la}}).xy;
    int i;
    for(i=alku; i<nEnt; i++)
	if (piste_polygonissa(xy.x, xy.y, shpoliot[i])) {
	    taul[ind] = i;
	    return 1; }
    for(i=0; i<alku; i++)
	if (piste_polygonissa(xy.x, xy.y, shpoliot[i])) {
	    taul[ind] = i;
	    return 1; }
    return 0;
}

/* Tällä haetaan kullekin luotavalle hilaruudulle ne alkuperäisen datan indeksit,
   jotka huomioidaan kyseisessä hilaruudussa. */
void* selaa_oliot(void *restrict varg) {
    int alku  = ((Arg*)varg)->alku;
    int loppu = ((Arg*)varg)->loppu;
    int nro   = ((Arg*)varg)->nro;
    int* taul = ((Arg*)varg)->indeksit;
    arg_luettu = 1;

    /* lat-lon -> Lambert Azimuthal Equal area */
    PJ_CONTEXT* ctx = proj_context_create();
    PJ* pj = proj_create_crs_to_crs(ctx, "+proj=longlat", "+proj=laea +lat_0=90", NULL);
    if(!pj)
	errx(1, "proj_create_crs_to_crs");

    double hilaväli_05 = (lon[1]-lon[0]) * 0.5;
    putchar('\n');
    if(nro==1)
	putchar('\n');
    for(int yi=0; yi<pit_lat; yi++) {
	printf("\033[%iA%i/%zu\033[%iB\r", nro+1, yi+1, pit_lat, nro+1);
	fflush(stdout);
	int yi_pitlon = yi*pit_lon;
	/* Käydään läpi neljä pistettä kustakin ruudusta.
	   Jos piste on jonkin alueen sisällä, otetaan indeksi talteen
	   ja kasvatetaan muuttujaa luku,
	   joka kertoo montako näistä neljästä oli määrittelyalueella. */
	for(int xi=alku; xi<loppu; xi++) {
	    double lo = lon[xi]-hilaväli_05/2;
	    double la = lat[yi]-hilaväli_05/2;
	    int luku = 0, ind = (yi_pitlon + xi)*5, aloitus=0;

	    if(hae_piste(pj, la, lo, taul, aloitus, ind+luku)) {
		aloitus = taul[ind+luku]-3;
		if(aloitus < 0) aloitus = 0;
		luku++;
	    }
	    lo += hilaväli_05;

	    if(hae_piste(pj, la, lo, taul, aloitus, ind+luku)) {
		aloitus = taul[ind+luku]-3;
		if(aloitus < 0) aloitus = 0;
		luku++;
	    }
	    la += hilaväli_05;

	    if(hae_piste(pj, la, lo, taul, aloitus, ind+luku)) {
		aloitus = taul[ind+luku]-3;
		if(aloitus < 0) aloitus = 0;
		luku++;
	    }
	    lo -= hilaväli_05;

	    if(hae_piste(pj, la, lo, taul, aloitus, ind+luku)) {
		aloitus = taul[ind+luku]-3;
		if(aloitus < 0) aloitus = 0;
		luku++;
	    }
	    taul[ind+luku] = -1;
	}
    }
    proj_context_destroy(ctx);
    proj_destroy(pj);
    return NULL;
}

int piste_polygonissa(double x, double y, SHPObject* olio) {
    //x += 0.09;
    //y += 0.09;
    if (x < olio->dfXMin || x >= olio->dfXMax || y < olio->dfYMin || y >= olio->dfYMax)
	return 0;
    /* Tämä ei riitä, koska alueet eivät välttämättä ole suorakulmioita.
     * Kierroslukumenetelmä (ks. wikipedia) toimii kaiken muotoisille alueille.
     * Yllä oleva on vain nopeuttamassa, ettei kierroslukua tarvitse laskea kaikille polygoneille. */
    double kierrosluku = 0;
    for(int ring=0; ring<olio->nParts; ring++) {
	int i = olio->panPartStart[ring];
	piste reuna1={{olio->padfX[i], olio->padfY[i]}}, reuna2;
	int loppu = ring == olio->nParts-1 ? olio->nVertices : olio->panPartStart[ring+1];
	while(++i < loppu) {
	    reuna2 = (piste){{ olio->padfX[i], olio->padfY[i] }};
	    kierrosluku += kulma( reuna1, reuna2, (piste){{x,y}} );
	    reuna1 = reuna2;
	}
    }
    kierrosluku /= 2*3.14159265358979;
    return (int)round(kierrosluku); // Tämä on 1 tai 0 sen mukaan onko piste alueella.
}

double kulma(piste keha1, piste keha2, piste p) {
    piste sv1 = suuntavektori(p, keha1);
    piste sv2 = suuntavektori(p, keha2);
    double abs_kulma = acos(pistetulo(sv1,sv2) / (vektpituus(sv1)*vektpituus(sv2)));
    return abs_kulma * sign(ristitulo(sv1,sv2));
}

piste suuntavektori(piste p0, piste p1) { 
    return (piste){{ p1.a[0] - p0.a[0], p1.a[1] - p0.a[1] }};
}

double pistetulo(piste a, piste b) {
    return a.a[0]*b.a[0] + a.a[1]*b.a[1];
}

double ristitulo(piste p0, piste p1) {
    return p0.a[0]*p1.a[1] - p0.a[1]*p1.a[0];
}

double vektpituus(piste p) {
    return sqrt(p.a[0]*p.a[0] + p.a[1]*p.a[1]);
}

int sign(double a) {
    return (a<0)? -1: 1;
}

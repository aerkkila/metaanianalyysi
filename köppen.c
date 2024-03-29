/*
   Kääntäjä tarvitsee argumentit -lm -lnetcdf -lshp -pthread
   Shapelib (shapefil.h) ja netcdf pitää olla asennettuina.
*/

#include <shapefil.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <time.h>
#include <unistd.h>
#include <netcdf.h>
#include <math.h>

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
typedef char nc_kirj_tyyppi; //tämä vaikuttaa myös seuraavaan riviin
#define NC_KIRJTYYPPI_ENUM NC_BYTE
typedef struct{ double a[2]; } piste;
typedef struct{ int alku; int loppu; int nro; } Arg;

void* selaa_oliot(void*);
void kirjoita_netcdf();
int piste_polygonissa(double x, double y, SHPObject* olio);
double kulma(piste kehä1, piste kehä2, piste kanta);
double ristitulo(piste p0, piste p1);
int sign(double);
piste suuntavektori(piste p0, piste p1);
double vektpituus(piste p);
double pistetulo(piste a, piste b);

static const char* tiednimi      = "köppen_shp/1976-2000";
static const char* nc_luett_nimi = "aluemaski.nc";
static const char* nc_kirj_nimi  = "köppen1x1maski.nc";
static const char* dbfnimi       = "GRIDCODE";

static int nEnt, shptype, verbose, njobs=1, ncpalaute, arg_luettu, ncid;
static int lukeva_säie = -1, i_köpp = 0;
static char* lmaskit;
SHPObject** shpoliot;
size_t pit_lat, pit_lon, pit_latlon;
int köppluokkia;
float *lat, *lon;
nc_kirj_tyyppi* nc_kirj_data;
dbftyyppi* dbfdata;

struct {
    int id;
    char* str;
}
köpptunnisteet[] = {
#include "köppentunnisteet.h"
};

int main(int argc, char** argv) {
    clock_t kello = clock();
    int id;
#define Switch(a) do { char* _switchc = a; if(0)
#define Case(a,b) else if(!strcmp(_switchc, a) || !strcmp(_switchc, b))
#define End } while(0)
    for(int i=1; i<argc; i++) {
	Switch(argv[i]);
	Case("-v", "--verbose") {
	    verbose = 1;
	    continue; }
	Case("-j", "--njobs") {
	    sscanf(argv[++i], "%i", &njobs);
	    continue; }
	Case("-o", "-o") {
	    nc_kirj_nimi = argv[++i];
	    continue; }
	End;
    }
#undef Switch
#undef Case
#undef End

    /* Luetaan ja tarkistetaan shapefilen tiedot. */
    Printf("Luetaan %s\n", tiednimi);
    SHPHandle shpkahva = SHPOpen(tiednimi, "rb");
    double shpmin[4], shpmax[4];
    SHPGetInfo(shpkahva, &nEnt, &shptype, shpmin, shpmax);
    if(shptype != SHPT_POLYGON) {
	fprintf(stderr, "\033[31mVirhe:\033[0m Shapefilen-tyyppi ei ole SHPT_POLYGON\n");
	SHPClose(shpkahva);
	return 1;
    }
    Printf("nEnt = %i\n", nEnt);
    shpoliot = malloc(nEnt*sizeof(void*));
    for(int i=0; i<nEnt; i++) {
	shpoliot[i] = SHPReadObject(shpkahva,i);
	for(int j=0; j<shpoliot[i]->nParts; j++)
	    if(shpoliot[i]->panPartType[j] != SHPP_RING)
		fprintf(stderr, "\033[31mVirhe:\033[0m Shapeolion-tyyppi ei ole SHPP_RING\n");
    }
    SHPClose(shpkahva);
  
    /* luetaan vastaava .dbf-tiedosto, joka sisältää shapefilen geometriaan kuuluvan datan */
    DBFHandle dbfkahva = DBFOpen( tiednimi, "rb" );
    id = DBFGetFieldIndex( dbfkahva, dbfnimi );
    if(id < 0) {
	fprintf( stderr, "\033[31mVirhe:\033[0m .dbf-tiedostosta ei löytynyt kenttää %s.\n", dbfnimi );
	DBFClose(dbfkahva);
	return 1;
    }
    if( DBFGetFieldInfo( dbfkahva, id, NULL, NULL, NULL ) != DBFTYYPPI_ENUM ) {
	fprintf( stderr, "\033[31mVirhe:\033[0m kentän %s tyyppi oli väärä.\n", dbfnimi );
	DBFClose(dbfkahva);
	return 1;
    }
    int apu;
    if( (apu=DBFGetRecordCount(dbfkahva)) != nEnt ) {
	fprintf( stderr, "\033[31mVirhe:\033[0m RecordCount(dbf) = %i, nEnt(shp) = %i\n", apu, nEnt );
	DBFClose(dbfkahva);
	return 1;
    }
    dbfdata = malloc(nEnt*sizeof(dbftyyppi));
    for(int i=0; i<nEnt; i++)
	dbfdata[i] = DBFRead_tyyppi_Attribute( dbfkahva, i, id );
    DBFClose(dbfkahva);

    /* luetaan netcdf-tiedostosta koordinaatit */
    Printf("Luetaan %s\n", nc_luett_nimi);
    NCFUNK(nc_open, nc_luett_nimi, NC_NOWRITE, &ncid);
    NCFUNK(nc_inq_dimid, ncid, "lat", &id);            // lat
    NCFUNK(nc_inq_dim, ncid, id, NULL, &pit_lat);
    lat = malloc(pit_lat*sizeof(float));
    NCFUNK(nc_inq_varid, ncid, "lat", &id);
    NCFUNK(nc_get_var_float, ncid, id, lat);
    NCFUNK(nc_inq_dimid, ncid, "lon", &id);            // lon
    NCFUNK(nc_inq_dim, ncid, id, NULL, &pit_lon);
    lon = malloc(pit_lon*sizeof(float));
    NCFUNK(nc_inq_varid, ncid, "lon", &id);
    NCFUNK(nc_get_var_float, ncid, id, lon);
    NCFUNK(nc_close, ncid);

    pit_latlon = pit_lat*pit_lon;
    Printf("pit_lat = %zu\t pit_lon = %zu\t pit_latlon = %zu\n", pit_lat, pit_lon, pit_latlon);
    nc_kirj_data = calloc(pit_latlon, sizeof(nc_kirj_tyyppi));
    köppluokkia = sizeof(köpptunnisteet)/sizeof(*köpptunnisteet);
    lmaskit = malloc(pit_latlon*köppluokkia);

    /* Luodaan säikeet */
    pthread_t saikeet[njobs-1];
    for(int i=0; i<njobs-1; i++) {
	Arg arg = {
	    .alku  = pit_lon*i     / njobs,
	    .loppu = pit_lon*(i+1) / njobs,
	    .nro   = i,
	};
	pthread_create(saikeet+i, NULL, selaa_oliot, &arg);
	while(!arg_luettu)
	    usleep(10);
	arg_luettu = 0;
    }
    Arg arg = {
	.alku  = pit_lon*(njobs-1) / njobs,
	.loppu = pit_lon,
	.nro   = njobs-1,
    };
    selaa_oliot(&arg);
    for(int i=0; i<njobs-1; i++)
	pthread_join(saikeet[i], NULL);
  
    for(int i=0; i<nEnt; i++)
	SHPDestroyObject(shpoliot[i]);
    free(shpoliot); shpoliot = NULL;
    kirjoita_netcdf();
    free(dbfdata);
    free(nc_kirj_data);
    free(lmaskit);
    free(lat);
    free(lon);
    double aika = (double)(clock()-kello) / CLOCKS_PER_SEC;
    if(aika < 1)
	Printf("CPU-aika %.2lf ms\n", aika*1000);
    else
	Printf("CPU-aika %.3lf s\n", aika);
    return 0;
}

void luo_netcdf_maski(int monesko) {
    size_t pit = pit_latlon;
    char* lmaski = lmaskit+pit*monesko;
    nc_kirj_tyyppi tunniste = köpptunnisteet[monesko].id;
    for(int i=0; i<pit; i++)
	lmaski[i] = nc_kirj_data[i]==tunniste;
}

/* Ei ole mitään objektiivista perustetta,
   miksi goto olisi tässä tapauksessa epäselvempi kuin while(1). */
void* tee_maskit(void* arg) {
    int säie = *(int*)arg;
    arg_luettu = 1;
    int monesko;
loop:
    while(1) {
	while(lukeva_säie >= 0)
	    usleep(1);
	lukeva_säie = säie;
	usleep(3);
	if(lukeva_säie==säie) {
	    monesko = i_köpp++;
	    lukeva_säie = -1;
	    break;
	}
	else
	    Printf("Säie %i ei saanut lukuvuoroa\n", säie);
    }
    if(monesko >= köppluokkia)
	return NULL;
    luo_netcdf_maski(monesko);
    goto loop;
}

void kirjoita_netcdf_maski(int ncid, int latid, int lonid) {
    pthread_t saikeet[njobs];
    for(int i=0; i<njobs; i++) {
	pthread_create(saikeet+i, NULL, tee_maskit, &i);
	while(!arg_luettu)
	    usleep(5);
	arg_luettu = 0;
    }
    int latlonid[] = {latid,lonid}, varid;
    for(int i=0; i<njobs; i++)
	pthread_join(saikeet[i],NULL);
    for(int i=0; i<köppluokkia; i++) {
	NCFUNK(nc_def_var, ncid, köpptunnisteet[i].str, NC_BYTE, 2, latlonid, &varid);
	NCFUNK(nc_put_var, ncid, varid, lmaskit+pit_latlon*i);
    }
}

void kirjoita_netcdf() {
    int ncid, latid, lonid, varid;
    NCFUNK(nc_create, nc_kirj_nimi, NC_CLOBBER|NC_NETCDF4, &ncid);
    NCFUNK(nc_def_dim, ncid, "lat", pit_lat, &latid);
    NCFUNK(nc_def_var, ncid, "lat", NC_FLOAT, 1, &latid, &varid);
    NCFUNK(nc_put_var, ncid, varid, lat);
    NCFUNK(nc_def_dim, ncid, "lon", pit_lon, &lonid);
    NCFUNK(nc_def_var, ncid, "lon", NC_FLOAT, 1, &lonid, &varid);
    NCFUNK(nc_put_var, ncid, varid, lon);
    int latlonid[] = {latid,lonid};
    NCFUNK(nc_def_var, ncid, "luokka", NC_KIRJTYYPPI_ENUM, 2, latlonid, &varid);
    NCFUNK(nc_put_var, ncid, varid, nc_kirj_data);
    kirjoita_netcdf_maski(ncid, latid, lonid);
    NCFUNK(nc_close, ncid);
}

void* selaa_oliot(void *restrict varg) {
    struct timespec alkuaika, loppuaika;
    clock_gettime(CLOCK_REALTIME, &alkuaika);
    int alku  = ((Arg*)varg)->alku;
    int loppu = ((Arg*)varg)->loppu;
    int nro   = ((Arg*)varg)->nro;
    arg_luettu = 1;
    for(int yi=0; yi<pit_lat; yi++)
	for(int xi=alku; xi<loppu; xi++)
	    for(int i=0; i<nEnt; i++)
		if (piste_polygonissa(lon[xi],lat[yi],shpoliot[i])) {
		    nc_kirj_data[ yi*pit_lon + xi ] = (nc_kirj_tyyppi)dbfdata[i];
		    break;
		}
    Printf("Säie %3i, %4i –%4i, %4i kpl: ", nro, alku, loppu-1, loppu-alku);
    clock_gettime(CLOCK_REALTIME, &loppuaika);
    double aika = loppuaika.tv_sec - alkuaika.tv_sec;
    aika += (loppuaika.tv_nsec - alkuaika.tv_nsec) * 1.0e-9;
    if (aika < 1)
	Printf("%.2lf ms\n", aika*1000);
    else
	Printf("%.3lf s\n", aika);
    return NULL;
}

int piste_polygonissa(double x, double y, SHPObject* olio) {
    x += 0.09;
    y += 0.09;
    if (x < olio->dfXMin || x >= olio->dfXMax || y < olio->dfYMin || y >= olio->dfYMax)
	return 0;
    // return 1; // Tämä riittää, jos alueitten tiedetään olevan suorakulmioita
    /* Tämä taas toimii minkä tahansa muotoiselle alueelle */
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
    kierrosluku /= 2*3.14159265358979; // periaatteessa turha
    return (int)round(kierrosluku); // tämä on 1 tai 0 sen mukaan onko piste alueella
}

double kulma(piste kehä1, piste kehä2, piste p) {
    piste sv1 = suuntavektori(p, kehä1);
    piste sv2 = suuntavektori(p, kehä2);
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

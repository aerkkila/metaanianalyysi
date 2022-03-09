/*Pitää asentaa:
  . https://github.com/OSGeo/shapelib.git (shapefil.h) (./autogen.sh; ./configure; make install)
  . libnetcdf-dev (netcdf.h)
  shapelib (eri kuin tuo github) tarjoaa hyödyllisiä apuvälineitä komentoriville kuten shpinfo ja dbfinfo
  Kääntäjä tarvitsee argumentit -lm -lnetcdf -lshp -pthread
  -j n ajaa n:llä säikeellä
  -v on argumentti, jota ilman ohjelma on mykkä
  -g määrittää hilan tarkkuuden. Ilman sitä luetaan netcdf-tiedosto ja tehdään sen mukainen hila.
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
#define NCVIRHE(arg) printf("\033[31mNetcdf-virhe:\033[0m %s\n", nc_strerror(arg))
#define NCFUNK(fun, ...)			\
  do {						\
    if((ncpalaute = fun(__VA_ARGS__)))		\
      NCVIRHE(ncpalaute);			\
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
double kulma(piste keha1, piste keha2, piste kanta);
double ristitulo(piste p0, piste p1);
int sign(double);
piste suuntavektori(piste p0, piste p1);
double vektpituus(piste p);
double pistetulo(piste a, piste b);

static const char* tiednimi = "köppen_shp/1976-2000";
static const char* nc_luett_nimi = "../../FT_implementointi/FT_percents_pixel_ease_flag/DOY/winter_start_doy_2010.nc";
static const char* nc_kirj_nimi0 = "köppen1x1.nc";
static const char* dbfnimi = "GRIDCODE";

static int nEnt, shptype, verbose, njobs=1, ncpalaute, arg_luettu, ncid;
static double hila, hila_lon, hila_lat;
char* nc_kirj_nimi;
SHPObject** shpoliot;
size_t pit_lat, pit_lon;
double *lat, *lon;
nc_kirj_tyyppi* nc_kirj_data;
dbftyyppi* dbfdata;

int main(int argc, char** argv) {
  clock_t kello = clock();
  int id;
  for(int i=1; i<argc; i++) {
    if( !strcmp(argv[i],"-v") || !strcmp(argv[i],"--verbose") )
      verbose = 1;
    if( !strcmp(argv[i],"-j") || !strcmp(argv[i],"--njobs") )
      sscanf( argv[++i], "%i", &njobs );
    if( !strcmp(argv[i],"-g") || !strcmp(argv[i],"--grid") )
      sscanf( argv[++i], "%lf", &hila );
    if( !strcmp(argv[i],"-o") )
      nc_kirj_nimi = strdup(argv[++i]);
  }
  if(!nc_kirj_nimi)
    nc_kirj_nimi = strdup(nc_kirj_nimi0);

  /*luetaan shapefilen tiedot*/
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
  for(int i=0; i<nEnt; i++)
    shpoliot[i] = SHPReadObject(shpkahva,i);
  SHPClose(shpkahva);
  
  /*luetaan vastaava .dbf-tiedosto, joka sisältää shapefilen geometriaan kuuluvan datan*/
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

  /*luetaan netcdf ellei hilaa ole annettu*/
  if(!hila) {
    Printf("Luetaan %s\n", nc_luett_nimi);
    NCFUNK(nc_open, nc_luett_nimi, NC_NOWRITE, &ncid);
    NCFUNK(nc_inq_dimid, ncid, "lat", &id);            //lat
    NCFUNK(nc_inq_dim, ncid, id, NULL, &pit_lat);
    lat = malloc(pit_lat*sizeof(double));
    NCFUNK(nc_inq_varid, ncid, "lat", &id);
    NCFUNK(nc_get_var, ncid, id, lat);
    NCFUNK(nc_inq_dimid, ncid, "lon", &id);            //lon
    NCFUNK(nc_inq_dim, ncid, id, NULL, &pit_lon);
    lon = malloc(pit_lon*sizeof(double));
    NCFUNK(nc_inq_varid, ncid, "lon", &id);
    NCFUNK(nc_get_var, ncid, id, lon);
    NCFUNK(nc_close, ncid);
  } else {
    pit_lon = (shpmax[0]-shpmin[0]) / hila;
    hila_lon = (shpmax[0]-shpmin[0]) / pit_lon; //muutetaan niin, että rajat osuvat, vaikka pit_lon on kokonaisluku
    lon = malloc(pit_lon*sizeof(double));
    for(size_t i=0; i<pit_lon; i++)
      lon[i] = shpmin[0] + i*hila_lon;
    pit_lat = (shpmax[1]-shpmin[1]) / hila;
    hila_lat = (shpmax[1]-shpmin[1]) / pit_lat; //muutetaan niin, että rajat osuvat, vaikka pit_lat on kokonaisluku
    lat = malloc(pit_lat*sizeof(double));
    for(size_t i=0; i<pit_lat; i++)
      lat[i] = shpmin[1] + i*hila_lat;
  }
  Printf("pit_lat = %zu\t pit_lon = %zu\n", pit_lat, pit_lon);
  nc_kirj_data = malloc(pit_lat*pit_lon*sizeof(nc_kirj_tyyppi));
  memset( nc_kirj_data, 0, pit_lat*pit_lon*sizeof(nc_kirj_tyyppi) );

  /*Luodaan säikeet*/
  pthread_t saikeet[njobs];
  for(int i=0; i<njobs; i++) {
    Arg arg = { .alku=pit_lon*i/njobs, .loppu=pit_lon*(i+1)/njobs, .nro=i };
    pthread_create(saikeet+i, NULL, selaa_oliot, &arg);
    while(!arg_luettu)
      usleep(10);
    arg_luettu = 0;
  }
  for(int i=0; i<njobs; i++)
    pthread_join(saikeet[i], NULL);
  
  for(int i=0; i<nEnt; i++)
    SHPDestroyObject(shpoliot[i]);
  free(shpoliot); shpoliot = NULL;
  kirjoita_netcdf();
  free(dbfdata);
  free(nc_kirj_data);
  free(nc_kirj_nimi);
  free(lat);
  free(lon);
  double aika = (double)(clock()-kello) / CLOCKS_PER_SEC;
  if(aika < 1)
    Printf("CPU-aika %.2lf ms\n", aika*1000);
  else
    Printf("CPU-aika %.3lf s\n", aika);
  return 0;
}

void kirjoita_netcdf_str(int ncid, int latid, int lonid) {
  int latlonid[] = {latid, lonid};
  int varid;
  int nc_pit = pit_lat*pit_lon;
  char **nimet = malloc(nc_pit*sizeof(char*));
  struct {
    int id;
    char* str;
  } tunnisteet[] = {
#include "köppentunnisteet.c"
  };
  int j_edel = 0;
  for(int nc_id=0; nc_id<nc_pit; nc_id++) {
    if( nc_kirj_data[nc_id] == tunnisteet[j_edel].id ) { //luultavimmin seuraava on sama kuin edellinen
      nimet[nc_id] = strdup( tunnisteet[j_edel].str );
      continue;
    }
    for(int j=0; j<sizeof(tunnisteet)/sizeof(*tunnisteet); j++)
      if( nc_kirj_data[nc_id] == tunnisteet[j].id ) {
	nimet[nc_id] = strdup( tunnisteet[j].str );
	j_edel = j;
	goto FOR_NC_PIT;
      }
    nimet[nc_id] = strdup("");
    j_edel = 0;
  FOR_NC_PIT:
    ;
  }
  size_t alkuptr[]  = { 0, 0 };
  size_t loppuptr[] = { pit_lat, pit_lon };
  NCFUNK( nc_def_var, ncid, "sluokka", NC_STRING, 2, latlonid, &varid );
  NCFUNK( nc_put_vara, ncid, varid, alkuptr, loppuptr, nimet );
  for(int i=0; i<nc_pit; i++)
    free(nimet[i]);
  free(nimet);
}

void kirjoita_netcdf() {
  int ncid, latid, lonid, varid;
  NCFUNK( nc_create, nc_kirj_nimi, NC_CLOBBER|NC_NETCDF4, &ncid );
  NCFUNK( nc_def_dim, ncid, "lat", pit_lat, &latid );
  NCFUNK( nc_def_var, ncid, "lat", NC_DOUBLE, 1, &latid, &varid );
  NCFUNK( nc_put_var, ncid, varid, lat );
  NCFUNK( nc_def_dim, ncid, "lon", pit_lon, &lonid );
  NCFUNK( nc_def_var, ncid, "lon", NC_DOUBLE, 1, &lonid, &varid );
  NCFUNK( nc_put_var, ncid, varid, lon );
  int latlonid[] = {latid,lonid};
  NCFUNK( nc_def_var, ncid, "luokka", NC_KIRJTYYPPI_ENUM, 2, latlonid, &varid );
  NCFUNK( nc_put_var, ncid, varid, nc_kirj_data );
  kirjoita_netcdf_str( ncid, latid, lonid );
  NCFUNK( nc_close, ncid );
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
      for(int i=0; i<nEnt; i++) //tätä voisi optimoida lämpimällä aloituksella
	if( piste_polygonissa(lon[xi],lat[yi],shpoliot[i]) ) {
	  nc_kirj_data[ yi*pit_lon + xi ] = (nc_kirj_tyyppi)dbfdata[i];
	  break;
	}
  Printf("Säie %3i, %4i –%4i, %4i kpl: ", nro, alku, loppu-1, loppu-alku);
  clock_gettime(CLOCK_REALTIME, &loppuaika);
  double aika = loppuaika.tv_sec - alkuaika.tv_sec;
  aika += (loppuaika.tv_nsec - alkuaika.tv_nsec) * 1.0e-9;
  if(aika < 1)
    Printf("%.2lf ms\n", aika*1000);
  else
    Printf("%.3lf s\n", aika);
  return NULL;
}

int piste_polygonissa(double x, double y, SHPObject* olio) {
  if( x < olio->dfXMin || x >= olio->dfXMax || y < olio->dfYMin || y >= olio->dfYMax )
    return 0;
  //return 1; //Tämä riittää, jos alueitten tiedetään olevan suorakulmioita
  /*Tämä taas toimii minkä tahansa muotoiselle alueelle*/
  piste reuna1={{olio->padfX[0], olio->padfY[0]}}, reuna2;
  double kierrosluku = 0;
  for(int i=1; i<olio->nVertices; i++) {
    reuna2 = (piste){{ olio->padfX[i], olio->padfY[i] }};
    kierrosluku += kulma( reuna1, reuna2, (piste){{x,y}} );
    reuna1 = reuna2;
  }
  return (int)round(kierrosluku); //tämä on 1 tai 0 sen mukaan onko piste alueella
}

double kulma(piste keha1, piste keha2, piste p) {
  piste sv1 = suuntavektori(p, keha1);
  piste sv2 = suuntavektori(p, keha2);
  double abs_kulma = acos( pistetulo(sv1,sv2) / (vektpituus(sv1)*vektpituus(sv2)) );
  return abs_kulma * sign( ristitulo(sv1,sv2) );
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
  return sqrt( pow(p.a[0],2) + pow(p.a[1],2) );
}

int sign(double a) {
  return (a<0)? -1: 1;
}

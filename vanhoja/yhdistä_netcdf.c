#include <netcdf.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

int ncvirhe;
const char* virhev = "\033[1;31m";
const char* perusv = "\033[0m";
float *lat, *lon;
size_t pit_lat, pit_lon;

#define NCFUNK(funk,...) do						\
    if((ncvirhe=funk(__VA_ARGS__)))					\
      {									\
	fprintf(stderr,"%s%s:%s %s\n",virhev,#funk,perusv,nc_strerror(ncvirhe)); \
	exit(1);							\
      }									\
  while(0)

void lue_koordinaatit(char* tnimi) {
  int ncid,id;
  NCFUNK(nc_open,tnimi,NC_NOWRITE,&ncid);

  NCFUNK(nc_inq_dimid, ncid, "lat", &id);            //lat
  NCFUNK(nc_inq_dim, ncid, id, NULL, &pit_lat);
  lat = malloc(pit_lat*sizeof(float));
  NCFUNK(nc_inq_varid, ncid, "lat", &id);
  NCFUNK(nc_get_var, ncid, id, lat);

  NCFUNK(nc_inq_dimid, ncid, "lon", &id);            //lon
  NCFUNK(nc_inq_dim, ncid, id, NULL, &pit_lon);
  lon = malloc(pit_lon*sizeof(float));
  NCFUNK(nc_inq_varid, ncid, "lon", &id);
  NCFUNK(nc_get_var, ncid, id, lon);

  NCFUNK(nc_close, ncid);
}

int main(int argc, char** argv) {
  int ncid,dimid,varid;
  int* aika;
  char apustr[100];
  lue_koordinaatit(argv[1]);
  NCFUNK(nc_create,"a.nc",NC_CLOBBER|NC_NETCDF4,&ncid);
  /*lat*/
  NCFUNK( nc_def_dim, ncid, "lat",  pit_lat, &dimid );
  NCFUNK( nc_def_var, ncid, "lat",  NC_FLOAT, 1, &dimid, &varid );
  NCFUNK( nc_put_var, ncid, varid,  lat );
  /*lon*/
  NCFUNK( nc_def_dim, ncid, "lon",  pit_lon, &dimid );
  NCFUNK( nc_def_var, ncid, "lon",  NC_FLOAT, 1, &dimid, &varid );
  NCFUNK( nc_put_var, ncid, varid,  lon );
  /*aika*/
  nc_type nctyyppi;
  size_t pit;
  NCFUNK( nc_inq_att, ncid, NC_GLOBAL, apustr, &nctyyppi, &pit );
  puts(apustr);
  //NCFUNK( nc_def_var, ncid, "time", argc-1, &dimid );
  //NCFUNK( nc_def_var, ncid, "time", NC_INT,   1, &dimid, &varid );
  //NCFUNK( nc_put_var, ncid, varid,  aika );
  //NCFUNK( nc_close, ncid );
}

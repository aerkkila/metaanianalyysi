#include <netcdf.h>
#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>

int main() {
  int ncid;
  char tiednimi[50];
  char komento[60];
  for(int y=2010; y<=2021; y++)
    for(int m=1; m<=12; m++)
      for(int d=1; d<=31; d++) {
	sprintf(tiednimi, "FT_%i%02i%02i.nc", y, m, d);
	if(access(tiednimi, F_OK))
	  continue;
	if(!nc_open(tiednimi, NC_NOWRITE, &ncid))
	  goto SULJE;
	sprintf(komento, "rm %s", tiednimi);
	puts(tiednimi);
	if(system(komento))
	  printf("Jotain omituista %s\n", komento);
      SULJE:
	nc_close(ncid);
      }
}

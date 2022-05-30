#include <nctietue/nctietue.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

// gcc wetlandsumma.c -lnctietue -lSDL2 -lpng -lnetcdf -lm -O3
// nctietue-kirjaston saa githubista https://github.com/aerkkila/nctietue.git

const double r2 = 40592558970441; //(6371229 m)^2;
#define PINTAALA(lat, hila) ((hila)*r2*(sin((lat)+(hila))-sin(lat))*1.0e-6)
#define ASTE 0.017453293

char* vars[] = {"wetland", "bog", "fen", "marsh", "tundra_wetland", "permafrost_bog"};
#define ARRPIT(a) sizeof(a)/sizeof(*(a))

int main(int argc, char** argv) {
  nct_vset* baw = nct_read_ncfile("./BAWLD05x05.nc");
  for(int k=0; k<ARRPIT(vars); k++) {
    nct_var* var = baw->vars + nct_get_varid(baw, vars[k]);
    int xpit = var->dimlens[1];
    double pintaala = 0;
    double* lat = baw->vars[nct_get_varid(baw, "lat")].data;
    for(int j=0; j<var->dimlens[0]; j++) {
      double ala = PINTAALA(ASTE*lat[j], ASTE*0.5);
      for(int i=0; i<xpit; i++)
	pintaala += ((float*)var->data)[j*xpit+i]*ala;
    }
    printf("%s\t%.4lf Mkm²\t\n", vars[k], pintaala*1e-6);
  }
  nct_write_ncfile(baw, "testi.nc");
  nct_free_vset(baw);
  free(baw);
  return 0;
}

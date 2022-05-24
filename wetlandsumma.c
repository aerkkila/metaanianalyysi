#include "../nctietue/nctietue.c"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

const double r2 = 40592558970441; //(6371229 m)^2;
#define PINTAALA(lat, hila) ((hila)*r2*(sinf((lat)+hila)-sinf(lat))*1.0e-6)
#define ASTE 0.017453293

int main(int argc, char** argv) {
  nct_vset* baw = nct_read_ncfile("./BAWLD05x05.nc");
  nct_var* wetl = baw->vars + nct_get_varid(baw, "wetland");
  double pintaala = 0;
  double* lat = baw->vars[nct_get_varid(baw, "lat")].data;
  for(int j=0; j<wetl->dimlens[0]; j++) {
    double ala = PINTAALA(ASTE*lat[j], ASTE*0.5);
    for(int i=0; i<wetl->dimlens[1]; i++)
      pintaala += ((float*)wetl->data)[i]*ala;
  }
  printf("%.0lf\n", pintaala);
  nct_free_vset(baw);
  free(baw);
  return 0;
}

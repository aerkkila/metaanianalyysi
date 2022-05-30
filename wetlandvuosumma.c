#include <nctietue/nctietue.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

// gcc wetlandvuosumma.c -lnctietue -lSDL2 -lpng -lnetcdf -lm
// nctietue-kirjaston saa gittinä osoitteesta https://github.com/aerkkila/nctietue.git

const double r2 = 40592558970441; //(6371229 m)^2;
#define PINTAALA(lat, hila) ((hila)*r2*(sin((lat)+(hila))-sin(lat)))//*1.0e-6)
#define ASTE 0.017453293

char* vars[] = {"wetland", "bog", "fen", "marsh", "tundra_wetland", "permafrost_bog"};
#define ARRPIT(a) sizeof(a)/sizeof(*(a))

int main(int argc, char** argv) {
  nct_vset* baw = nct_read_ncfile("./BAWLD1x1.nc");
  nct_vset* vuo = nct_read_ncfile("./flux1x1_whole_year.nc");
  nct_var* vuovar = vuo->vars + nct_get_varid(vuo, "flux_bio_posterior");
  nct_varmean0(vuovar);
  nct_var* wetl = baw->vars + nct_get_varid(baw, "wetland");
  char* tmpc[] = {"lat", "lon"};
  FILE* ulos = fopen("wetlandvuosumma.csv", "w");
  for(int k=0; k<ARRPIT(vars); k++) {
    nct_var* wlaji = baw->vars + nct_get_varid(baw, vars[k]);
    int xpit = wlaji->dimlens[1];
    double vuosumma = 0;
    double* lat = baw->vars[nct_get_varid(baw, "lat")].data;
    int count = 0;
    for(int j=0; j<wlaji->dimlens[0]; j++) {
      double ala = PINTAALA(ASTE*lat[j], ASTE);
      for(int i=0; i<xpit; i++) {
	int ind = j*xpit+i;
	double lisa = ((double*)wlaji->data)[ind] / ((double*)wetl->data)[ind] * ((float*)vuovar->data)[ind] * ala;
	//if(((double*)wetl->data)[ind] < 0.03) continue;
	count++;
	if(lisa==lisa)
	  vuosumma += lisa;
      }
    }
    fprintf(ulos, "%s,%.4lf mol/s,%.4lf Tg,%i\n", vars[k], vuosumma, vuosumma*1e-12*31536000*16.0416, count);
  }
  fclose(ulos);
  nct_free_vset(baw);
  free(baw);
  nct_free_vset(vuo);
  free(vuo);
  return 0;
}

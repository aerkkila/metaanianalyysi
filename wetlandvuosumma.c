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
  nct_vset* vuo = nct_read_ncfile("./flux1x1_%s.nc", argc>1? argv[1]: "whole_year");
  nct_var* vuovar = vuo->vars + nct_get_varid(vuo, "flux_bio_posterior");
  nct_varnanmean0(vuovar);
  nct_var* wetl = baw->vars + nct_get_varid(baw, "wetland");
  FILE* ulos = fopen("wetlandvuosumma.csv", "w");
  fprintf(ulos, ",mol/s,Tg,nmol/s/m²\n");
  for(int k=0; k<ARRPIT(vars); k++) {
    nct_var* wlaji = baw->vars + nct_get_varid(baw, vars[k]);
    int xpit = wlaji->dimlens[1];
    double* lat = baw->vars[nct_get_varid(baw, "lat")].data;
    double vuosumma = 0;
    double pintaala = 0;
    int    lasku    = 0;
    for(int j=0; j<wlaji->dimlens[0]; j++) {
      if(lat[j]<49.5)
	continue;
      double ala = PINTAALA(ASTE*lat[j], ASTE);
      for(int i=0; i<xpit; i++) {
	int ind = j*xpit+i;
	if(((double*)wetl->data)[ind] < 0.03) continue;
	double ala1 = ((double*)wlaji->data)[ind] * ala;
	double vuo1 = ((float*)vuovar->data)[ind] * ala1 / ((double*)wetl->data)[ind];
	if(vuo1 == vuo1) {
	  vuosumma += vuo1;
	  pintaala += ala1;
	  lasku++;
	}
      }
    }
    fprintf(ulos, "%s,%.4lf,%.4lf,%.5lf\n", vars[k], vuosumma, vuosumma*1e-12*31536000*16.0416, vuosumma/pintaala*1e9);
  }
  fclose(ulos);
  nct_free_vset(baw);
  free(baw);
  nct_free_vset(vuo);
  free(vuo);
  return 0;
}

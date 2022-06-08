#include <nctietue/nctietue.h>
#include <stdlib.h>
#include <stdio.h>

double ero2(double a, double b) {
  return (a-b)*(a-b);
}

int main() {
  nct_vset* vset = nct_read_ncfile("purettu/FT_20140101.nc");
  int varid = nct_get_varid(vset, "L3FT");

  double* restrict lat = nct_range_NC_DOUBLE(29.5, 84, 1);
  double* restrict lon = nct_range_NC_DOUBLE(-179.5, 180, 1);
  int* restrict koordind = malloc(55*360*sizeof(int));
  double* restrict lat0 = vset->vars[nct_get_varid(vset, "lat")].data;
  double* restrict lon0 = vset->vars[nct_get_varid(vset, "lon")].data;

  /*Pituuspiirit ovat tiedostossa väärin, mutta korjataan ne oikeiksi*/
  for(int i=0; i<720*720; i++) {
    lon0[i] = -lon0[i]+180;
    if(lon0[i] > 180)
      lon0[i] -= 360;
  }
  int ind=0;
  int minind;
  double matka;
  for(int j=0; j<55; j++)
    for(int i=0; i<360; i++) {
      double minmatka = 9999999999;
      for(int ind0=0; ind0<720*720; ind0++)
	if((matka=ero2(lat0[ind0],lat[j]) + ero2(lon0[ind0],lon[i])) < minmatka) {
	  minmatka = matka;
	  minind = ind0;
	}
      koordind[ind++] = minind;
      printf("\r%i", ind);
    }
  printf("\n");

  FILE* f = fopen("koordind.bin", "w");
  if(fwrite(koordind, sizeof(int), 55*360, f) != 55*360)
    printf("Kirjoittaminen epäonnistui\n");
  fclose(f);
  free(lat);
  free(lon);
  free(koordind);
  nct_free_vset(vset);
  free(vset);
  return 0;
}

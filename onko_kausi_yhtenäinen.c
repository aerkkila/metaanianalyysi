#include <nctietue.h>
#include <stdlib.h>
#include <string.h>

//gcc onko_kausi_yhtenäinen.c -o oky.out -g -Og -lnctietue -lnetcdf -lpng -lSDL2

int resol, maxind;

int seuraava_kausi(char* data, int ind) {
  if(ind>=maxind)
    return -1;
  char arvo = data[ind];
  while((ind+=resol) < maxind)
    if(data[ind] != arvo)
      return ind;
  return -1;
}

int main() {
  nct_vset vset;
  nct_read_ncfile_gd(&vset, "kaudet1.nc");
  int timelen = NCTDIM(vset,"time").len;
  int varid = nct_get_noncoord_varid(&vset);
  if(varid < 0)
    return 1;
  maxind = nct_getlen(&vset, varid);
  resol = maxind / timelen;
  int minimivali = 40;
  char* data = vset.vars[varid].data;
  short epayht[resol];
  memset(epayht, 0, resol*2);
  for(int i=0; i<resol; i++) {
    int ind=i + resol*minimivali, uusi_ind;
    while((uusi_ind = seuraava_kausi(data, ind+=resol)) >= 0)
      if(data[ind-resol] == data[uusi_ind] && // edellinen == seuraava
	 (uusi_ind-ind)/resol < minimivali && // lyhyellä aikavälillä
	 data[uusi_ind])                      // kyse on määritellystä kaudesta
	epayht[i]++;
  }
  int dimids[] = {1,2};
  vset.vars = realloc(vset.vars, (vset.nvars+1)*sizeof(nct_var));
  nct_simply_add_var(&vset, epayht, NC_SHORT, 2, dimids, "epäyht");
  nct_print_vset(&vset);
  nct_plot_var(&vset, vset.nvars-1);
  nct_write_ncfile(&vset, "testi.nc");
  vset.vars[vset.nvars-1].data = NULL; // tämä on pinomuistissa
  nct_free_vset(&vset);
  return 0;
}

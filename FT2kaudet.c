#include <nctietue/nctietue.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

const int resol = 19800;
const int paivaaika = 86400;
#define KESA 1
#define SYKSY 2
#define TALVI 3

/* jäässä -> talvi: 3 -> 3
 * sula -> kesä: 1 -> 1
 * osittain jäässä (2) -> jäätyminen (2) || kevät_eli_kesä (1): edellinen_eri==sula? jäätyminen: kevät_eli_kesä
 */

time_t unixaika(int vuosi, int kuukausi, int paiva) {
  struct tm aikatm = {.tm_year=vuosi, .tm_mon=kuukausi-1, .tm_mday=paiva};
  return mktime(&aikatm);
}

char edellinen_eri(char* ptr, int ind) {
  char luku = ptr[ind];
  while(ind >= resol)
    if(ptr[ind-=resol] != luku)
      return ptr[ind];
  return -1;
}

int main(int argc, char** argv) {
  nct_vset vset;
  time_t alkuaika, loppuaika, aika0, aika1, paivia;
  int varid, vuosi, kk, paiva, tyhjaa_alussa, tyhjaa_lopussa;
  char* str;
  if(argc < 2) {
    puts("Ei luettavan nimeä");
    return 1;
  }
  if(argc < 3) {
    puts("Ei tallennusnimeä");
    return 1;
  }
  nct_read_ncfile_gd(&vset, argv[1]);
  varid = nct_get_varid(&vset, "time");
  str = nct_get_att_text(&vset, varid, "units");
  if(!str)
    return 1;
  if(!(str = strstr(str, "days since ")))
    return 2;
  str += strlen("days since ");
  sscanf(str, "%d-%d-%d", &vuosi, &kk, &paiva);

  alkuaika = unixaika(vuosi, kk, paiva);
  aika0 = unixaika(vuosi, 8, 1);
  if((tyhjaa_alussa = (aika0-alkuaika)/paivaaika) < 0)
    return 3;

  loppuaika = alkuaika + nct_getlen(&vset,nct_get_varid(&vset,"time")) * paivaaika;
  vuosi += NCTVAR(vset,"time").len / 365; //loppuvuosi
  aika1 = unixaika(vuosi, 8, 1);
  if((tyhjaa_lopussa = (loppuaika-aika1)/paivaaika) < 0) {
    aika1 = unixaika(vuosi-1, 8, 1);
    if((tyhjaa_lopussa = (loppuaika-aika1)/paivaaika) < 0)
      return 4;
  }

  paivia = (aika1 - aika0) / paivaaika;

  for(varid=0; varid<vset.nvars; varid++)
    if(!(vset.vars[varid].iscoordinate))
      break;
  char* ptr = vset.vars[varid].data + tyhjaa_alussa * resol;
  for(int i=0; i<resol; i++)
    for(int t=0; t<paivia; t++) {
      int ind = i + t*resol;
      if(ptr[ind] == 2) {
	char ee = edellinen_eri(ptr, ind);
	if(ee < 0)
	  return 5;
	if(ee == TALVI)
	  ptr[ind] = KESA;
      }
    }
  varid = nct_get_dimid(&vset, "time");
  nct_vset_isel(&vset, varid, tyhjaa_alussa, vset.dims[varid].len-tyhjaa_lopussa);
  nct_write_ncfile(&vset, argv[2]);
  nct_free_vset(&vset);
  return 0;
}

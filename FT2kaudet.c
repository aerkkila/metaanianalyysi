#include <nctietue.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

const int resol = 19800;
const int paivaaika = 86400;
#define KESA 1
#define TAITE 2
#define TALVI 3
time_t aika1_ulos;

time_t unixaika(int vuosi, int kuukausi, int paiva) {
  struct tm aikatm = {.tm_year=vuosi-1900, .tm_mon=kuukausi-1, .tm_mday=paiva};
  return mktime(&aikatm);
}

/* Tätä voidaan säätää, onko suure sula vai sula|osasula
 * laittamalla viimeiseen if-lauseeseen joko x != KESA tai x == TALVI */
int suuretta_elokuuhun_asti(char* ptr, int ind, time_t hetki) {
  struct tm *aikatm = gmtime(&hetki);
  aikatm->tm_year += aikatm->tm_mon >= 7;
  aikatm->tm_mon = 7;
  aikatm->tm_mday = 10;
  time_t hetki1 = mktime(aikatm);
  if(hetki1 >= aika1_ulos)
    return -1; //data loppuu
  int paivia = (hetki1 - hetki) / paivaaika;
  for(int i=0; i<paivia; i++)
    if(ptr[ind+=resol] != KESA)
      return 0;
  return 1;
}

/*Kesästä vaihtuu seuraavaan kauteen, kun kesä katkeaa.
 *Taitteesta talveen, kun tulee ensimmäinen talvipäivä.
 *Talvesta (tai talvettomana vuonna taitteesta) kesään, kun tulee kesä, josta on kesää elokuuhun.
 *Funktio olettaa edellisen päivän olevan oikein ja saatavilla. */
int tama_kausi(char* ptr, int ind, time_t hetki) {
  if(ptr[ind] == ptr[ind-resol])
    return ptr[ind];
  switch(ptr[ind]) {
  case KESA:;
    int asti = suuretta_elokuuhun_asti(ptr, ind, hetki);
    if(asti < 0) return 0;
    return asti? KESA: ptr[ind-resol];
  case TAITE:
    if(ptr[ind-resol] == KESA) {
      int asti = suuretta_elokuuhun_asti(ptr, ind, hetki);
      if(asti < 0) return 0;
      return asti? KESA: TAITE;
    }
    return TALVI; // edellinenkin on talvi
  default:
    return ptr[ind];
  }
}

int main(int argc, char** argv) {
  nct_vset vset, vsetmaski;
  time_t aika0_sis, aika1_sis, aika0_ulos;
  int varid, vuosi, kk, paiva, tyhjaa_alussa, tyhjaa_lopussa, paivia;
  char *str, *maski;
  if(argc < 2) {
    puts("Ei luettavan nimeä");
    return 1;
  }
  if(argc < 3) {
    puts("Ei tallennusnimeä");
    return 1;
  }
  nct_read_ncfile_gd(&vsetmaski, "aluemaski.nc");
  maski = vsetmaski.vars[2].data;
  nct_read_ncfile_gd(&vset, argv[1]);
  varid = nct_get_varid(&vset, "time");
  str = nct_get_att_text(&vset, varid, "units");
  if(!str)
    return 1;
  if(!(str = strstr(str, "days since ")))
    return 2;
  str += strlen("days since ");
  sscanf(str, "%d-%d-%d", &vuosi, &kk, &paiva);

  aika0_sis = unixaika(vuosi, kk, paiva);
  aika0_ulos = unixaika(vuosi, 8, 1);
  if((tyhjaa_alussa = (aika0_ulos-aika0_sis)/paivaaika) < 0)
    return 3;

  aika1_sis = aika0_sis + NCTDIM(vset,"time").len * paivaaika;
  vuosi += NCTVAR(vset,"time").len / 365; //loppuvuosi
  aika1_ulos = unixaika(vuosi+1, 1, 1);
  if((tyhjaa_lopussa = (aika1_sis-aika1_ulos)/paivaaika) < 0) {
    aika1_ulos = unixaika(vuosi, 1, 1);
    if((tyhjaa_lopussa = (aika1_sis-aika1_ulos)/paivaaika) < 0)
      return 4;
  }
  paivia = (aika1_ulos-aika0_ulos)/paivaaika;
  
  varid = nct_get_noncoord_varid(&vset);
  char* ptr = vset.vars[varid].data + tyhjaa_alussa * resol;
  for(int i=0; i<resol; i++) {
    if(!maski[i])
      for(int t=0; t<paivia; t++)
	ptr[t*resol+i] = 0;
    else
      for(int t=1; t<paivia; t++) {
	int ind = t*resol+i;
	ptr[ind] = tama_kausi(ptr, ind, aika0_ulos+t*paivaaika);
      }
  }
  nct_free_vset(&vsetmaski);
  nct_add_att_text(&vset, varid, "numerointi", "1=kesä; 2=jäätyminen; 3=talvi", 0);
  varid = nct_get_dimid(&vset, "time");
  nct_vset_isel(&vset, varid, tyhjaa_alussa, vset.dims[varid].len-tyhjaa_lopussa);
  nct_write_ncfile(&vset, argv[2]);
  nct_free_vset(&vset);
  return 0;
}

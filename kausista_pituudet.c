#include <nctietue/nctietue.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

int resol;
#define KESA 1
#define TALVI 3

int paivia_tata(char* ptr, int ind, int maxind) {
  int paivia = 1;
  if(ind>=maxind)
    return -1;
  char arvo = ptr[ind];
  while((ind+=resol) < maxind) {
    if(ptr[ind] != arvo)
      return paivia;
    paivia++;
  }
  return -1;
}

/* Vuosi vaihtuu elokuun alussa seuraavaan, koska syksy luetaan seuraavaan vuoteen,
 * koska jäätyminen voi myös alkaa vasta vuoden vaihduttua
 * ja sulaminen ei ala elokuun alun jälkeen.
 */
int hae_vuosi(int vuosi0, int paivia) {
  return vuosi0 + paivia/365 + 1; //toimii, koska tällä aikavälillä on riittävän vähän karkausvuosia
}

int main(int argc, char** argv) {
  nct_vset vset;
  int paivia_yht, varid, vuosi, kk, paiva;
  if(argc < 2) {
    puts("Ei luettavan nimeä");
    return 1;
  }
  if(argc < 3) {
    puts("Ei tallennusnimeä");
    return 1;
  }
  nct_read_ncfile_gd(&vset, argv[1]);
  resol = NCTDIM(vset,"lat").len * NCTDIM(vset,"lon").len;
  varid = nct_get_varid(&vset, "time");
  char* str = nct_get_att_text(&vset, varid, "units");
  if(!str)
    return 1;
  if(!(str = strstr(str, "days since ")))
    return 2;
  str += strlen("days since ");
  if(sscanf(str, "%d-%d-%d", &vuosi, &kk, &paiva)!=3)
    return 3;
  paivia_yht = NCTDIM(vset,"time").len;
  int pituuspituus = resol*(paivia_yht/365+1);
  short* pituudet1[3];
  for(int i=0; i<3; i++)
    pituudet1[i] = calloc(pituuspituus,2);
  for(varid=0; varid<vset.nvars; varid++)
    if(!(vset.vars[varid].iscoordinate))
      break;
  
  int vuosi0=vuosi, maxind=paivia_yht*resol;
  if(maxind != nct_getlen(&vset, varid)) {
    printf("saatiin maxind = %i, mutta pitäisi olla %li\n", maxind, nct_getlen(&vset, varid));
    return 5;
  }

  for(int i=0; i<resol; i++) {
    char* ptr = vset.vars[varid].data;
    int ind=i, paivia;
    while(ptr[ind+=resol] == KESA); // Siirrytään seuraavan kauden alkuun.
    while((paivia = paivia_tata(ptr, ind, maxind)) >= 0) { // montako päivää on tätä kautta
      int kausi = ptr[ind]; // mikä on tämä kausi
      if(!kausi)
	goto SEURAAVA;
      if(kausi>TALVI || kausi < 0)
	return 4;
      if(paivia > 365)
	paivia = 365; // Jos kausi kestää monta vuotta, laitetaan joka vuodelle 365.
      vuosi = hae_vuosi(vuosi0, ind/resol);
      pituudet1[kausi-1][(vuosi-vuosi0-1)*resol+i] = paivia; //alkuvuosi ohitettiin
    SEURAAVA:
      ind += paivia*resol; // seuraavan kauden alkuun
    }
  }
  nct_vset tallenn = {0};
  nct_add_coord(&tallenn, nct_range_NC_INT(vuosi0+1,vuosi+1,1), vuosi-vuosi0, NC_INT, "vuosi");
  nct_add_coord(&tallenn, NCTVAR(vset,"lat").data, NCTDIM(vset,"lat").len, NCTVAR(vset,"lat").xtype, "lat");
  nct_add_coord(&tallenn, NCTVAR(vset,"lon").data, NCTDIM(vset,"lon").len, NCTVAR(vset,"lon").xtype, "lon");
  NCTVAR(vset,"lat").data = NULL; // nämä               muuten           molemmista             
  NCTVAR(vset,"lon").data = NULL; //      yritettäisiin        vapauttaa            dataseteistä
  
  tallenn.vars = realloc(tallenn.vars, (tallenn.nvars+3)*sizeof(nct_var));
  int dimids[] = {0,1,2};
  char* nimet[] = {"summer","freezing","winter"};
  for(int i=0; i<3; i++)
    nct_simply_add_var(&tallenn, pituudet1[i], NC_SHORT, 3, dimids, nimet[i]);
  nct_write_ncfile(&tallenn, argv[2]);
  nct_free_vset(&tallenn);
  nct_free_vset(&vset);
  return 0;
}

#include <nctietue.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <math.h>

int resol;
time_t hetki0;
const int paivan_pituus = 86400;
#define KESA 1
#define TALVI 3

void alusta_hetki0(int vuosi, int kk, int p) {
  struct tm tma = {.tm_year=vuosi-1900, .tm_mon=kk-1, .tm_mday=p};
  hetki0 = mktime(&tma);
}

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

int laske_alkupaiva() {
  struct tm tma = {.tm_year=2011-1900, .tm_mon=7, .tm_mday=1};
  time_t hetki = mktime(&tma);
  return (hetki-hetki0)/paivan_pituus;
}

int vuoden_paiva(int paiva) {
  time_t hetki = hetki0 + paiva*paivan_pituus;
  struct tm *tma = gmtime(&hetki);
  tma->tm_year += tma->tm_mon>=7; //elokuusta alkaen lasketaan seuraavaan vuoteen
  tma->tm_mday = 1;
  tma->tm_mon = 0;
  time_t nollahetki = mktime(tma);
  return (hetki - nollahetki) / 86400;
}

/* Vuosi vaihtuu elokuun alussa seuraavaan, koska syksy luetaan seuraavaan vuoteen,
 * koska jäätyminen voi myös alkaa vasta vuoden vaihduttua.
 */
int hae_vuosi(int vuosi0_sis, int paivia) {
  return vuosi0_sis + paivia/365 + 1; //Karkausvuosia on riittävän vähän.
}

int main(int argc, char** argv) {
  nct_vset vset;
  int paivia_yht, varid, vuosi, vuosi0_ulos, vuosi0_sis, kk0, paiva0, maxind;
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
  if(sscanf(str, "%d-%d-%d", &vuosi, &kk0, &paiva0)!=3)
    return 3;
  alusta_hetki0(vuosi, kk0, paiva0);

  paivia_yht = NCTDIM(vset,"time").len;
  int pit = resol*(paivia_yht/365+1);
  float* pituudet1[3];
  for(int i=0; i<3; i++) {
    pituudet1[i] = malloc(pit*4);
    for(int j=0; j<pit; j++)
      pituudet1[i][j] = NAN;
  }
  for(varid=0; varid<vset.nvars; varid++)
    if(!(vset.vars[varid].iscoordinate))
      break;
  
  maxind = paivia_yht*resol;
  if(maxind != nct_getlen(&vset, varid)) {
    printf("saatiin maxind = %i, mutta pitäisi olla %li\n", maxind, nct_getlen(&vset, varid));
    return 5;
  }

  /*talven alku- ja loppupäivät*/
  float *talven_alku  = malloc(pit*2 * 4);
  float *talven_loppu = talven_alku + pit;
  for(int i=0; i<pit*2; i++)
    talven_alku[i] = NAN;

  int alkupaiva = laske_alkupaiva();
  vuosi0_sis = vuosi;
  vuosi0_ulos = vuosi + alkupaiva/365 + 1; //vuosi vaihtuu heti päivän ylityttyä
  int pituusind_alku = alkupaiva/365, pituusind;

  for(int i=0; i<resol; i++) {
    char* ptr = vset.vars[varid].data;
    int ind=i+alkupaiva*resol, paivia;
    while(ptr[ind+=resol] == KESA); // Siirrytään seuraavan kauden alkuun.
    while((paivia = paivia_tata(ptr, ind, maxind)) >= 0) { // montako päivää on tätä kautta
      int kausi = ptr[ind]; // mikä on tämä kausi
      if(!kausi)
	goto SEURAAVA;
      if(kausi>3 || kausi < 0)
	return 4;
      if(paivia > 365)
	paivia = 365; // Jos kausi kestää monta vuotta, laitetaan joka vuodelle 365.
      vuosi = hae_vuosi(vuosi0_sis, ind/resol);
      pituusind = (vuosi-vuosi0_ulos)*resol+i - pituusind_alku;
      pituudet1[kausi-1][pituusind] = paivia;
      if(ptr[ind] == TALVI && ptr[ind-resol] != TALVI)
	talven_alku[pituusind] = vuoden_paiva(ind/resol);
      else if(ptr[ind] != TALVI && ptr[ind-resol] == TALVI)
	talven_loppu[pituusind] = vuoden_paiva(ind/resol);
    SEURAAVA:
      ind += paivia*resol; // seuraavan kauden alkuun
    }
  }
  nct_vset tallenn = {0};
  int vuosi1 = paivia_yht/365 + vuosi0_sis;
  nct_add_coord(&tallenn, nct_range_NC_INT(vuosi0_ulos,vuosi1+1,1), vuosi1-vuosi0_ulos+1, NC_INT, "vuosi");
  nct_add_coord(&tallenn, NCTVAR(vset,"lat").data, NCTDIM(vset,"lat").len, NCTVAR(vset,"lat").xtype, "lat");
  nct_add_coord(&tallenn, NCTVAR(vset,"lon").data, NCTDIM(vset,"lon").len, NCTVAR(vset,"lon").xtype, "lon");
  NCTVAR(vset,"lat").data = NULL; // nämä               muuten           molemmista             
  NCTVAR(vset,"lon").data = NULL; //      yritettäisiin        vapauttaa            dataseteistä
  
  tallenn.vars = realloc(tallenn.vars, (tallenn.nvars+5)*sizeof(nct_var));
  int dimids[] = {0,1,2};
  char* nimet[] = {"summer","freezing","winter"};
  for(int i=0; i<3; i++)
    nct_simply_add_var(&tallenn, pituudet1[i], NC_FLOAT, 3, dimids, nimet[i]);
  nct_simply_add_var(&tallenn, talven_alku, NC_FLOAT, 3, dimids, "talven_alku");
  nct_simply_add_var(&tallenn, talven_loppu, NC_FLOAT, 3, dimids, "talven_loppu");
  nct_add_att_text(&tallenn, tallenn.nvars-2, "numerointi", "vuosi n on talvi vuosina n-1 – n", 0);
  nct_write_ncfile(&tallenn, argv[2]);
  tallenn.vars[tallenn.nvars-1].data = NULL; //yhteinen malloc edellisen muuttujan kanssa
  nct_free_vset(&tallenn);
  nct_free_vset(&vset);
  return 0;
}

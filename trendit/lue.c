#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <string.h>
#include <err.h>
#include <unistd.h>

/* Käyttö:
   Pythonilta kutsuttavat funktiot ovat tiedoston lopussa.
   Valinnaisesti, jos halutaan valikoida kausia, käytetään funktiota poista_kausi(num)
   Valinnaisesti, jos halutaan ennalta asettaa muuttujat vuosia ja vuodet, voidaan kutsua aloita_luenta()
   Sitten esimerkiksi:
   *    for muuttuja in ["emissio", "vuo"]
   *        while(!lue_seuraava(muuttuja))
   *            foo(kohde_$jotain)

   lue_seuraava() pitää aina kutsua kunnes se palauttaa toden, koska silloin resurssit vapautetaan.
   Vapauttamiselle ei ole erillistä funktiota.
   */

#define KAUSIA_KAU 3
#define KAUSIA_VUO 4
#define str const char* restrict
#define ARRPIT(a) sizeof(a) / sizeof(*(a))
static int kausia_kau = KAUSIA_KAU;
static int kausia_vuo = KAUSIA_VUO;
static int vuosia;
static int vuodet[15];
char kohde_lajinimi[40];
char kohde_kausinimet[KAUSIA_VUO][16];
double kohde_data[KAUSIA_VUO][15];

/* Bittimaski, jonka jäseniä voidaan asettaa pythonilla funktioilla luenta_olkoon() ja luenta_ei() */
static unsigned valinnat;
enum {antro_e, kausi_e, valintoja};
str valintanimet[] = {"antro", "kausi"};

static char ckaudet[] = {1,1,1,1,1,1,1};

typedef struct {
    char muuttuja[40];
    int lajinum;
} määrite;

enum palaute {kelpaa, ei_löytynyt_ensinkään, ei_löytynyt_enää, aikainen_eof};

int lue_vuodet(str tied) {
    vuosia = 0;
    str ptr = tied;
    int apu;
    while(*ptr++ != '\n');
    /* lasketaan vuodet, ptr ei saa muuttua vielä */
    for(const char* p=ptr; *p!='\n'; vuosia += *p++==',');
    /* Luetaan vuodet. Nyt ptr saa muuttua. */
    for(int i=0; i<vuosia; i++)
	sscanf(ptr, ",%i%n", vuodet+i, &apu), ptr+=apu;
}

static enum palaute lue(str tied, int tiedpit, määrite* määr) {
    int apu, ret = kelpaa;
    str ptr;

    /* Haetaan oikea kohta. */
    char haku[64];
    sprintf(haku, "#%s_", määr->muuttuja);
    ptr = strstr(tied, haku);
    if(!ptr) {
	ret = ei_löytynyt_ensinkään; goto palaa; }
    for(int i=0; i<määr->lajinum; i++) {
	ptr += strlen(haku);
	ptr = strstr(ptr, haku);
	if(!ptr) {
	    ret = ei_löytynyt_enää; goto palaa; }
    }
    str loppu = tied+tiedpit;
    if(ptr < tied)
	printf("Virhe %s: %i\n", __FILE__, __LINE__);
    if(ptr >= loppu)
	printf("Virhe %s: %i\n", __FILE__, __LINE__);

    /* Luetaan lajinimi siirtyen vuosirivin alkuun. */
    apu = 0;
    *ptr++; // ohitetaan alusta '#'-merkki
    while((kohde_lajinimi[apu++]=*ptr++) != '\n');
    kohde_lajinimi[apu-1] = '\0';

    while(*ptr++ != '\n'); // ohitetaan vuosirivi

    /* Luetaan data. */
    int k_ind=0;
    for(int kausi=0; ; kausi++) {
	if(!ckaudet[kausi]) {
	    while(*ptr++ != '\n');
	    continue; }
	while(*ptr <= ' ') ptr++;
	if(*ptr == '#')
	    break;
	if(!('a'<=*ptr && *ptr <= 'z'))
	    asm("int $3");
	sscanf(ptr, "%[^,],%n", kohde_kausinimet[k_ind], &apu), ptr+=apu;
	if(ptr >= loppu) {
	    ret = aikainen_eof; goto palaa; }
	for(int i=0; i<vuosia; i++) {
	    if(sscanf(ptr, "%lf%n", kohde_data[k_ind]+i, &apu) != 1) {
		kohde_data[k_ind][i] = 0.0/0.0;
		ptr += *ptr==',';
	    }
	    else
		ptr += apu+1;
	}
	if(ptr >= loppu)
	    goto palaa;
	k_ind++;
    }

palaa:
    return ret;
}

#define vuodirmakro "../vuodata2301/vuosittain/"
#define kausidirmakro "../kausidata2301/"
static char* tiedosto;
static int tiedpit;
static char* nimet_vuo[] = {"ikir.csv", "köppen.csv", "wetland.csv", "total.csv", NULL};
enum                       {ikircsv_e,  köppencsv_e,   wetlandcsv_e,  totalcsv_e, vuotiedostoja};
static char* nimet_kausi[] = {"data.csv", NULL};
static char** ptr;

int seuraava_tiedosto(int *määr_lajinum) {
    /* Poistetaan vanha. */
    if(tiedosto)
	munmap(tiedosto, tiedpit);
    tiedosto = NULL;

    if(!*ptr)
	return 1;

    /* Luetaan tiedosto muistiin. */
    char nimi[128];
    int fd;

    if(valinnat & 1<<kausi_e)
	sprintf(nimi, kausidirmakro"%s", *ptr);
    else
	sprintf(nimi, vuodirmakro"%s%s", valinnat&1<<antro_e? "antro/": "", *ptr);
    puts(nimi);
    if((fd = open(nimi, O_RDONLY)) < 0)
	err(1, "open %s", *ptr);
    struct stat stat;
    fstat(fd, &stat);
    tiedpit = stat.st_size;
    tiedosto = mmap(NULL, tiedpit, PROT_READ, MAP_PRIVATE, fd, 0);
    close(fd);
    if(!tiedosto)
	err(1, "mmap");

    ptr++;
    *määr_lajinum = 0;
    return 0;
}

static määrite määr;

/* Vain alla olevia kutsuttakoon toisesta ohjelmasta. */

static int aloita_luenta();

static int lue_seuraava(str muuttuja) {
    if(strcmp(määr.muuttuja, muuttuja)) // eri kuin ennen
	if(aloita_luenta()) {
	    fprintf(stderr, "Jotain on vialla, ei päästy edes alkuun %s: %i\n", __FILE__, __LINE__);
	    return 1; }
    strcpy(määr.muuttuja, muuttuja);
    while(1) {
	switch(lue(tiedosto, tiedpit, &määr)) {
	    case kelpaa:
		goto onnistui;
	    case ei_löytynyt_enää:
		if(seuraava_tiedosto(&määr.lajinum))
		    return 1;
		break;
	    case ei_löytynyt_ensinkään:
		printf("Muuttujaa %s ei löytynyt\n", muuttuja);
		return 1;
	    case aikainen_eof:
		printf("Tiedosto loppui kesken muuttujalla %s\n", muuttuja);
		return 1;
	}
    }
onnistui:
    määr.lajinum++;
    return 0;
}

#if 0
static char* anna_kausinimi(int kausi) {
    return kohde_kausinimet[kausi];
}

static char* anna_lajinimi() {
    return kohde_lajinimi;
}
#endif

static double* anna_data(int kausi) {
    return kohde_data[kausi];
}

static void poista_kausi(int kausi) {
    if(valinnat & 1<<kausi_e)
	kausia_kau -= !ckaudet[kausi];
    else
	kausia_vuo -= !ckaudet[kausi];
    ckaudet[kausi] = 0;
}

static void palauta_kausi(int kausi) {
    if(valinnat & 1<<kausi_e)
	kausia_kau += !ckaudet[kausi];
    else
	kausia_vuo += !ckaudet[kausi];
    ckaudet[kausi] = 1;
}

static int aloita_luenta() {
    if(valinnat & 1<<kausi_e)
	ptr = nimet_kausi;
    else if(valinnat & 1<<antro_e)
	ptr = nimet_vuo+totalcsv_e; // antrolle ainoastaan total
    else
	ptr = nimet_vuo;
    määr = (määrite){0};
    if(seuraava_tiedosto(&määr.lajinum))
	return 1;
    lue_vuodet(tiedosto);
    return 0;
}

static void luenta_olkoon(str nimi) {
    for(int i=0; i<valintoja; i++)
	if(!strcmp(valintanimet[i], nimi)) {
	    valinnat |= 1<<i;
	    return;
	}
    printf("\033[93mVaroitus:\033[0m tuntematon valinta %s\n", nimi);
}

static void luenta_ei(str nimi) {
    for(int i=0; i<valintoja; i++)
	if(!strcmp(valintanimet[i], nimi)) {
	    valinnat &= ~(1<<i);
	    return;
	}
    printf("\033[93mVaroitus:\033[0m tuntematon valinta %s\n", nimi);
}

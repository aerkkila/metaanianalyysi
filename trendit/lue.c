#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <string.h>
#include <err.h>

static const char* luokitus[] = {"köppen", "ikir", "wetland"};
enum luokitus_e                 {köpp_e,   ikir_e, wetl_e, luokituksia_e};

#define KAUSIA 4
#define str const char* restrict
static int kausia = KAUSIA;
static int vuosia;
static int monesko_laji = 0;

struct taul {
    int vuodet[15];
    char lajinimi[40];
    char kausinimet[KAUSIA][32];
    double data[KAUSIA][15];
};

enum palaute {kelpaa, ei_löytynyt_ensinkään, ei_löytynyt_enää, aikainen_eof};

#define dir "../vuotaulukot/vuosittain/"

static enum palaute _lue(str nimi, str muuttuja, struct taul* dest) {
    int apu, fd, ret = kelpaa;
    str ptr;

    /* Luetaan tiedosto muistiin. */
    if((fd = open(nimi, O_RDONLY)) < 0)
	err(1, "open %s", nimi);
    struct stat stat;
    fstat(fd, &stat);
    const int pit = stat.st_size;
    char* tied;
    tied = mmap(NULL, pit, PROT_READ, MAP_PRIVATE, fd, 0);
    close(fd);
    if(!tied)
	err(1, "mmap");

    /* Haetaan oikea kohta. */
    monesko_laji++;
    char haku[64];
    sprintf(haku, "#%s_", muuttuja);
    ptr = strstr(tied, haku);
    if(!ptr) {
	ret = ei_löytynyt_ensinkään; goto palaa; }
    for(int i=0; i<monesko_laji; i++) {
	ptr = strstr(ptr, haku);
	if(!ptr) {
	    ret = ei_löytynyt_enää; goto palaa; }
	ptr += strlen(haku);
    }
    str loppu = tied+pit;

    /* Luetaan lajinimi siirtyen vuosirivin alkuun. */
    apu = 0;
    while((dest->lajinimi[apu++]=*ptr++) != '\n');
    dest->lajinimi[apu-1] = '\0';

    vuosia = 0;
    for(const char* p=ptr; *p!='\n'; vuosia += *p++==','); // lasketaan vuodet, ptr ei saa muuttua vielä

    /* Luetaan vuodet. Nyt ptr saa muuttua. */
    for(int i=0; i<vuosia; i++)
	sscanf(ptr, ",%i%n", dest->vuodet+i, &apu), ptr+=apu;

    /* Luetaan data. */
    for(int kausi=0; kausi<kausia; kausi++) {
	while(*ptr <= ' ') ptr++;
	sscanf(ptr, "%[^,]%n", dest->kausinimet[kausi], &apu), ptr+=apu;
	if(ptr >= loppu) {
	    ret = aikainen_eof; goto palaa; }
	for(int i=0; i<vuosia; i++) {
	    sscanf(ptr, ",%lf%n", dest->data[kausi]+i, &apu), ptr+=apu;
	    if(ptr >= loppu) {
		ret = aikainen_eof; goto palaa; }
	}
    }

palaa:
    munmap((void*)tied, pit);
    return ret;
}

static char tmpnimi[128];
static char* _palauta_nimi(enum luokitus_e luok, int kosteikko) {
    sprintf(tmpnimi, dir"%s%s.csv", luokitus[luok], kosteikko?"W":"");
    return tmpnimi;
}

static int lue_tahan(str muuttuja, enum luokitus_e luok, int kosteikko, struct taul* dest) {
    switch(_lue(_palauta_nimi(luok, kosteikko), muuttuja, dest)) {
	case kelpaa:
	    return 0;
	case ei_löytynyt_enää:
	    break;
	case ei_löytynyt_ensinkään:
	    printf("Muuttujaa %s ei löytynyt\n", muuttuja);
	    break;
	case aikainen_eof:
	    printf("Tiedosto loppui kesken %s : %s.\n", tmpnimi, muuttuja);
	    break;
    }
    return 1;
}

static void alusta_luenta() {
    struct taul a;
    lue_tahan("vuo", 0, 0, &a); // asettaa tarvittavat globaalit muuttujat
    monesko_laji = 0;
}

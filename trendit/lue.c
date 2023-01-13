#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <string.h>
#include <err.h>

static const char* luokitus[] = {"köppen", "ikir", "wetland"};
enum luokitus_e          {köpp_e,   ikir_e, wetl_e, luokituksia};

#define KAUSIA 4
#define str const char* restrict
static int kausia = KAUSIA;
static int vuosia;

struct taul {
    int vuodet[15];
    char lajinimi[40];
    char kausinimet[KAUSIA][32];
    double data[KAUSIA][15];
};

enum palaute {kelpaa, ei_löytynyt, eof};

#define dir "/home/aerkkila/koodit/vuotaulukot/vuosittain/"

static enum palaute _lue(str nimi, str muuttuja, struct taul* dest) {
    int apu, fd, ret = kelpaa;
    if((fd = open(nimi, O_RDONLY)) < 0)
	err(1, "open %s", nimi);
    struct stat stat;
    fstat(fd, &stat);
    const int pit = stat.st_size;
    str tied;
    tied = mmap(NULL, pit, PROT_READ, MAP_PRIVATE, fd, 0);
    close(fd);
    if(!tied)
	err(1, "mmap");
    char haku[64];
    sprintf(haku, "#%s_", muuttuja);
    str ptr = strstr(tied, haku);
    if(!ptr) {
	ret = ei_löytynyt; goto palaa; }
    str loppu = tied+pit;

    /* Luetaan lajinimi siirtyen vuosirivin alkuun. */
    ptr += strlen(haku);
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
	    ret = eof; goto palaa; }
	for(int i=0; i<vuosia; i++) {
	    sscanf(ptr, ",%lf%n", dest->data[kausi]+i, &apu), ptr+=apu;
	    if(ptr >= loppu) {
		ret = eof; goto palaa; }
	}
    }

palaa:
    munmap((void*)tied, pit);
    return ret;
}

static char tmpnimi[128];
static char* _palauta_nimi(enum luokitus_e luok, int kosteikko) {
    sprintf(tmpnimi, dir"%s%s.csv", luokitus[luok], kosteikko?"_kosteikko":"");
    return tmpnimi;
}

static void lue_tahan(str muuttuja, enum luokitus_e luok, int kosteikko, struct taul* dest) {
    switch(_lue(_palauta_nimi(luok, kosteikko), muuttuja, dest)) {
	case kelpaa:
	    break;
	case ei_löytynyt:
	    printf("Muuttujaa %s ei löytynyt (%s).\n", muuttuja, tmpnimi);
	    break;
	case eof:
	    printf("Tiedosto loppui kesken %s : %s.\n", tmpnimi, muuttuja);
	    break;
    }
}

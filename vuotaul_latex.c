#include <stdio.h>
#include <aprintf.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#define ARRPIT(a) sizeof(a)/sizeof(*(a))
#ifndef KOSTEIKKO
#define KOSTEIKKO 0
#endif
#ifndef KOST_KAHTIA
#define KOST_KAHTIA 0
#endif

#if KOST_KAHTIA == 0
#define kansio "vuotaulukot"
#elif KOST_KAHTIA == 1
#define kansio "vuotaulukot/kahtia"
#elif KOST_KAHTIA == 2
#define kansio "vuotaulukot/kahtia_keskiosa"
#endif

const char* pripost[] = {"post", "pri"};
const char* kaudet[] = {"summer", "freezing", "winter"};
const char* ylänimet[] = {"wetland", "köppen", "ikir"};
const char* wetlnimet[] = {"bog", "fen", "marsh", "permafrost_bog", "tundra_wetland", "wetland", "non-wetland"};
const char* ikirnimet[] = {"non_permafrost", "sporadic", "discontinuous", "continuous"};
const char* köppnimet[] = {"D.b", "D.c", "D.d", "ET"};
int 
    pit_kaudet=ARRPIT(kaudet),
    pit_wetl=ARRPIT(wetlnimet),
    pit_köpp=ARRPIT(köppnimet),
    pit_ikir=ARRPIT(ikirnimet),
    ind_jää;

#define _STR(s) #s
#define STR2(s1,s2) (_STR(s1) _STR(s2))

void pituudet() {
    for(int i=0; i<pit_kaudet; i++)
	if(!strcmp(kaudet[i], "freezing")) {
	    ind_jää = 1;
	    break;
	}
}

int hae_ind(FILE* f, char* str) {
    char a[256];
    int sij0 = ftell(f);
    assert(fgets(a, 256, f));
    fseek(f, sij0, SEEK_SET);
    char* s;
    if(!(s=strstr(a, str))) return -1;
    int i=0, pilkkuja=0;
    while(a+i < s)
	pilkkuja += a[i++]==',';
    return pilkkuja;
}

/* Lukee kohdalla olevan rivin ja siltä riviltä ottaa taulukkoon taul luvut indekseillä tg_ind ja vuo_ind. */
int ota_rivi(FILE* f, float* taul, int tg_ind, int vuo_ind, const char** nimet, int pit) {
    char a[256];
    assert(fgets(a, 256, f));
    int nimi_ind;
    for(nimi_ind=0; nimi_ind<pit; nimi_ind++)
	if(!strncmp(nimet[nimi_ind], a, strlen(nimet[nimi_ind]))) goto kelpaa;
    return -1;
kelpaa:
    int ind[] = {tg_ind, vuo_ind};
    int pienempi = tg_ind>vuo_ind;
    int pilkkuja=0;
    int i=0;
    taul += nimi_ind*pit_kaudet*2;
    while(pilkkuja<ind[pienempi])
	pilkkuja += a[i++]==',';
    assert(sscanf(a+i, "%f", taul++) == 1);
    while(pilkkuja<ind[!pienempi])
	pilkkuja += a[i++]==',';
    assert(sscanf(a+i, "%f", taul) == 1);
    return nimi_ind;
}

int lue_data(int ppnum, const char* ylänimi, const char** nimet, int pit, float* taul) {
    static int vuo_ind=-1, tg_ind=-1;
    for(int k=0; k<pit_kaudet; k++) {
	FILE* f = fopen(aprintf(kansio "/%svuo_%s_%s_k%i.csv",
				ylänimi, pripost[ppnum], kaudet[k], KOSTEIKKO*(!!strcmp(ylänimi,"wetland"))), "r");
	if(!f) return 1;
	while(fgetc(f) != '\n'); // 1. rivi on kommentti

	if(vuo_ind < 0)
	    if((vuo_ind = hae_ind(f, "nmol/s/m²")) < 0)
		puts("ei löytynyt vuo_ind");
	if(tg_ind < 0)
	    if((tg_ind = hae_ind(f, "Tg")) < 0)
		puts("ei löytynyt tg_ind");

	while(fgetc(f) != '\n'); // 2. rivi on otsikkorivi

	unsigned maski = 0;
	/* Maskin ensimmäinen bitti jätetään käyttämättä, koska funktio palauttaa -1:n,
	   kun riviltä ei löytynyt haluttua nimeä ja tällöin maski |= 1<<(-1+1) */
	do
	    maski |= 1<<(1+ota_rivi(f, taul+k*2, tg_ind, vuo_ind, nimet, pit));
	while(maski>>1 != (1<<pit)-1 && !feof(f));
	if(maski>>1 != (1<<pit)-1)
	    puts("kaikkia rivejä ei löytynyt");
	fclose(f);
    }
    return 0;
}

char korvaa_apu[64];
char* korvaa(const char* str, int a, int b) {
    char* s;
    strncpy(korvaa_apu, str, 63);
    while((s=strchr(korvaa_apu, a)))
	*s = b;
    return korvaa_apu;
}

float jäätymisarvo(float* taul) {
    float talvi = taul[2*2+1];
    float syksy = taul[1*2+1] - talvi;
    float kesä  = taul[0*2+1] - talvi;
    return syksy/kesä;
}

#define K(...) fprintf(f, __VA_ARGS__)
#define A K(" & %.4f", taul[k*2])
#define B K(" & %.0f & %.3f", taul[k*2]/summa*1000, taul[k*2+1])
void kirjoita_rivi(FILE* f, float* taul) {
    float jä = jäätymisarvo(taul);
    float r = (jä-0.5)*2 * (jä>0.5);
    float b = (1-jä*2) * (jä<0.5);
    float summa = 0;
    int k;
    for(int k=0; k<pit_kaudet; k++) summa+=taul[k*2];
    for(k=0; k<ind_jää; k++) { A; B; }
    A;
    K(" & %.0f & \\colorbox[rgb]{%.2f, %.2f, %.2f}{%.3f}",
      taul[k*2]/summa*1000, 1-b, 1-r-b, 1-r, taul[k*2+1]);
    for(int k=ind_jää+1; k<pit_kaudet; k++) { A; B; }
    K(" \\\\\n");
}
#undef A
#undef B

void kirjoita_data(int ppnum, float* taul) {
#if KOST_KAHTIA==1
    FILE *f = fopen("vuosummat_kahtia.tex", "w");
#elif KOST_KAHTIA==2
    FILE *f = fopen("vuosummat_sekoitus.tex", "w");
#else
    FILE *f = fopen(aprintf("vuosummat_%s%s.tex",
			    pripost[ppnum], KOSTEIKKO? STR2(_k,KOSTEIKKO): ""), "w");
#endif
    K("\\begin{tabular}{l");
    for(int i=0; i<pit_kaudet; i++) K("|rrr");
    K("}\n");
    for(int i=0; i<pit_kaudet; i++) K(" & \\multicolumn{3}{r}{%s}", kaudet[i]);
    K(" \\\\\n");
    for(int i=0; i<pit_kaudet; i++) K(" & {Tg} & {‰} & {nmol/m$^2$/s}");
    K(" \\\\\n\\midrule\n");

#if !KOST_KAHTIA
    for(int i=0; i<pit_ikir; i++) {
	K("%s", korvaa(ikirnimet[i], '_', ' '));
	kirjoita_rivi(f, taul);
	taul += pit_kaudet*2;
    }
    for(int i=0; i<pit_köpp; i++) {
	K("%s", köppnimet[i]);
	kirjoita_rivi(f, taul);
	taul += pit_kaudet*2;
    }
#endif
#if !KOSTEIKKO
#if !KOST_KAHTIA
    K("\\\\\n");
#endif
    for(int i=0; i<pit_wetl; i++) {
	K("%s", korvaa(wetlnimet[i], '_', ' '));
	kirjoita_rivi(f, taul);
	taul += pit_kaudet*2;
    }
#endif
    K("\\end{tabular}\n");
}
#undef K

#if KOST_KAHTIA
int main() {
    pituudet();
    pit_wetl -= 2;
    float* taul = malloc(pit_wetl * pit_kaudet * 2 * sizeof(float));
    if(lue_data(0, "wetland", wetlnimet, pit_wetl, taul))
	puts("virhe lue_data");
    else
	kirjoita_data(0, taul);
    free(taul);
}
#else
int main() {
    pituudet();
    float* taul = malloc((pit_wetl+pit_köpp+pit_ikir)*pit_kaudet*2*sizeof(float));
    int toistot = 1 + (KOSTEIKKO==0 && KOST_KAHTIA==0);
    for(int ppnum=0; ppnum<toistot; ppnum++) {
	float* taul1 = taul;
	if(lue_data(ppnum, "ikir", ikirnimet, pit_ikir, taul1))
	    puts("virhe lue_data");
	taul1 += pit_ikir*pit_kaudet*2;
	if(lue_data(ppnum, "köppen", köppnimet, pit_köpp, taul1))
	    puts("virhe lue_data");
	taul1 += pit_köpp*pit_kaudet*2;
	if(lue_data(ppnum, "wetland", wetlnimet, pit_wetl, taul1))
	    puts("virhe lue_data");

	kirjoita_data(ppnum, taul);
    }
    free(taul);
}
#endif

#include <stdio.h>
#include <aprintf.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

const char* pripost[] = {"pri", "post"};
const char* kaudet[] = {"summer", "freezing", "winter"};
const char* ylänimet[] = {"wetland", "köppen", "ikir"};
const char* wetlnimet[] = {"bog", "fen", "marsh", "permafrost_bog", "tundra_wetland", "dryland"};
const char* ikirnimet[] = {"non_permafrost", "sporadic", "discontinuous", "continuous"};
const char* köppnimet[] = {"D.b", "D.c", "D.d", "ET"};
int pit_pripost, pit_kaudet, pit_wetl, pit_köpp, pit_ikir, ind_jää;

#define ARRPIT(a) sizeof(a)/sizeof(*(a))

void pituudet() {
    pit_pripost = ARRPIT(pripost);
    pit_kaudet = ARRPIT(kaudet);
    pit_wetl = ARRPIT(wetlnimet);
    pit_köpp = ARRPIT(köppnimet);
    pit_ikir = ARRPIT(ikirnimet);
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

int ota_rivi(FILE* f, float* taul, int tg_ind, int vuo_ind, const char** nimet, int pit) {
    char a[256];
    assert(fgets(a, 256, f));
    int nimi_ind;
    for(nimi_ind=0; nimi_ind<pit; nimi_ind++)
	if(!strncmp(nimet[nimi_ind], a, strlen(nimet[nimi_ind]))) goto kelpaa;
    return 0;
kelpaa:
    int ind[] = {tg_ind, vuo_ind};
    int ensin = tg_ind>vuo_ind; // vuo eli ind(1) ensin
    int pilkkuja=0;
    int i=0;
    taul += nimi_ind*pit_kaudet*2;
    while(pilkkuja<ind[ensin])
	pilkkuja += a[i++]==',';
    assert(sscanf(a+i, "%f", taul++) == 1);
    while(pilkkuja<ind[!ensin])
	pilkkuja += a[i++]==',';
    assert(sscanf(a+i, "%f", taul) == 1);
    return nimi_ind;
}

int lue_data(int ppnum, const char* ylänimi, const char** nimet, int pit, float* taul) {
    static int vuo_ind=-1, tg_ind=-1;
    for(int k=0; k<pit_kaudet; k++) {
	FILE* f = fopen(aprintf("vuotaulukot/%svuo_%s_%s_ft2.csv", ylänimi, pripost[ppnum], kaudet[k]), "r");
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
	while(maski != (1<<pit)-1)
	    maski |= 1<<ota_rivi(f, taul+k*2, tg_ind, vuo_ind, nimet, pit);
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
void laita_arvot(FILE* f, float* taul) {
    float jä = jäätymisarvo(taul);
    float r = (jä-0.5)*2 * (jä>0.5);
    float b = (1-jä*2) * (jä<0.5);
    float summa = 0;
    int k;
    for(int k=0; k<pit_kaudet; k++) summa+=taul[k*2];
    for(k=0; k<ind_jää; k++) K(" & %.0f & %.3f", taul[k*2]/summa*1000, taul[k*2+1]);
    K(" & %.0f & \\colorbox[rgb]{%.2f, %.2f, %.2f}{%.3f}",
      taul[k*2]/summa*1000, 1-b, 1-r-b, 1-r, taul[k*2+1]);
    for(int k=ind_jää+1; k<pit_kaudet; k++) K(" & %.0f & %.3f", taul[k*2]/summa*1000, taul[k*2+1]);
    K(" \\\\\n");
}

void kirjoita_data(int ppnum, float* taul) {
    FILE *f = fopen(aprintf("vuosummat_tiivistelmä_%s.tex", pripost[ppnum]), "w");
    K("\\begin{tabular}{l");
    for(int i=0; i<pit_kaudet; i++) K("|rr");
    K("}\n");
    for(int i=0; i<pit_kaudet; i++) K(" & \\multicolumn{2}{r}{%s}", kaudet[i]);
    K(" \\\\\n");
    for(int i=0; i<pit_kaudet; i++) K(" & {‰} & {nmol/m$^2$/s}");
    K(" \\\\\n\\midrule\n");
    for(int i=0; i<pit_ikir; i++) {
	K("%s", korvaa(ikirnimet[i], '_', ' '));
	laita_arvot(f, taul);
	taul += pit_kaudet*2;
    }
    for(int i=0; i<pit_köpp; i++) {
	K("%s", köppnimet[i]);
	laita_arvot(f, taul);
	taul += pit_kaudet*2;
    }
    K("\\\\\n");
    for(int i=0; i<pit_wetl; i++) {
	K("%s", korvaa(wetlnimet[i], '_', ' '));
	laita_arvot(f, taul);
	taul += pit_kaudet*2;
    }
    K("\\end{tabular}\n");
}
#undef K

int main() {
    pituudet();
    float* taul = malloc((pit_wetl+pit_köpp+pit_ikir)*pit_kaudet*2*sizeof(float));
    for(int ppnum=0; ppnum<pit_pripost; ppnum++) {
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

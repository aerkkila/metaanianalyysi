#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <err.h>
#include <assert.h>

#define K(...) fprintf(f, __VA_ARGS__)
#define arrpit(a) ((sizeof(a)) / sizeof(*(a)))
const char* wetlnimet[] = {"bog", "fen", "marsh", "permafrost_bog", "tundra_wetland", "wetland", "nonwetland"};
const char* ikirnimet[] = {"nonpermafrost", "sporadic", "discontinuous", "continuous"};
const char* köppnimet[] = {"D.b", "D.c", "D.d", "ET"};
int pit_wetl = arrpit(wetlnimet),
    pit_ikir = arrpit(ikirnimet),
    pit_köpp = arrpit(köppnimet);

char korvaa_apu[64] = { [63]=0 };
char* korvaa(const char* str, int a, int b) {
    char* s;
    strncpy(korvaa_apu, str, 63);
    while((s=strchr(korvaa_apu, a)))
	*s = b;
    return korvaa_apu;
}

typedef float taul_t[16][3];
taul_t itaul, wtaul, ktaul;

#define kirjoita_osio(f, t, n, s) _kirjoita_osio(f, t, n, s, (int)arrpit(n))
void _kirjoita_osio(FILE* f, taul_t taul, const char** nimet, int sarakkeita, int pit) {
    for(int i=0; i<pit; i++) {
	K("%s", korvaa(nimet[i], '_', ' '));
	for(int j=0; j<sarakkeita; j++)
	    K(" & %.3f", taul[i][j]);
	K(" \\\\\n");
    }
}

void kirjoita_data(FILE* f) {
    const char** kaikkinimet[] = {wetlnimet, ikirnimet, köppnimet};
    int pitdet[] = {pit_wetl, pit_ikir, pit_köpp};
    K("\\begin{tabular}{l|rrr}\n");
    K(" & °N all area & °N area 1");
    K(" \\\\\n\\midrule\n");
    kirjoita_osio(f, itaul, ikirnimet, 2); K("\\midrule\n");
    kirjoita_osio(f, ktaul, köppnimet, 2); K("\\midrule\n");
    _kirjoita_osio(f, wtaul, wetlnimet, 2, arrpit(wetlnimet)-1);
    K("nonwetland & %.3f \\\\\n", wtaul[arrpit(wetlnimet)-1][0]);
    K("\\end{tabular}\n");
}

/* Lukee tiedostoa alusta kunnes on luettu nimi, */
void löydä(FILE *f, const char* nimi) {
    fseek(f, 0, SEEK_SET);
    char sana[256];
    char* ptr = sana;

toista:
    while((*ptr = fgetc(f)) != '\n' && *ptr !=',' && !feof(f)) ptr++;
    assert(!feof(f));
    *ptr = '\0'; // kirjoitetaan luetun erotinmerkin päälle
    if(!strcmp(nimi, sana)) return;
    ptr = sana;
    goto toista;
}

void lue_tiedosto(const char* nimi, float taul[][3], int ind_taul, const char** nimet, int pitnimet) {
    FILE* f = fopen(nimi, "r");
    if(!f) err(1, "lue_tiedosto %s rivi %i", nimi, __LINE__);
    while(fgetc(f) != '\n'); // ohitetaan ensimmäinen rivi
    int rivi=0;

    char sana[256];
    if(!fgets(sana, 256, f))
	err(1, "fgets");
    char* tok = strtok(sana, ",");
    int pilkkuja = 0;
    do {
	if(!strcmp(tok, "lat")) goto kelpaa;
	pilkkuja++;
    } while((tok=strtok(NULL, ",\n")));
    errx(2, "lat-indeksiä ei löytynyt");

kelpaa:
    löydä(f, nimet[rivi]);
    int ind=0; // oikeasti 1, mutta pilkkuja laskettiin 1 liian vähän
    while(ind != pilkkuja) {
	while(fgetc(f) != ',' && !feof(f));
	if(feof(f)) return;
	ind++;
    }
    assert(fscanf(f, "%f", taul[rivi]+ind_taul)==1);
    if(++rivi == pitnimet) return;
    goto kelpaa;
}

#define kansio0 "./"

int main() {
    lue_tiedosto(kansio0"vuotaulukot/wetlandvuo_post_whole_year_k0.csv", wtaul, 0, wetlnimet, pit_wetl);
    lue_tiedosto(kansio0"vuotaulukot/kahtia/wetlandvuo_post_whole_year_k0.csv", wtaul, 1, wetlnimet, pit_wetl);
    //lue_tiedosto(kansio0"vuotaulukot/kahtia_keskiosa/wetlandvuo_post_whole_year_k0.csv", wtaul, 2, wetlnimet, pit_wetl);
    
    lue_tiedosto(kansio0"vuotaulukot/ikirvuo_post_whole_year_k0.csv", itaul, 0, ikirnimet, pit_ikir);
    lue_tiedosto(kansio0"vuotaulukot/ikirvuo_post_whole_year_k1.csv", itaul, 1, ikirnimet, pit_ikir);
    
    lue_tiedosto(kansio0"vuotaulukot/köppenvuo_post_whole_year_k0.csv", ktaul, 0, köppnimet, pit_köpp);
    lue_tiedosto(kansio0"vuotaulukot/köppenvuo_post_whole_year_k1.csv", ktaul, 1, köppnimet, pit_köpp);

    FILE* f = fopen(kansio0"lattaul.tex", "w");
    kirjoita_data(f);
    fclose(f);
}

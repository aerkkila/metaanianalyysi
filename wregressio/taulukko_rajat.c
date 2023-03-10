#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <assert.h>

/* Luettavassa tiedostossa pitää olla peräkkäin samalta kaudelta ensin lämpimän ja sitten kylmän alueen tulokset,
   mutta muuten tässä ei tehdä oletuksia tiedoston järjestyksestä. */

#define arrpit(a) (sizeof(a)/sizeof(*(a)))

const char* kaudet[] = {"summer", "freezing", "winter"};
const char* suureet[] = {"rajat:", "pisteistä:", "r²:"};
int kausia = arrpit(kaudet);
int suureita = arrpit(suureet);
#define kausia_m arrpit(kaudet)

#define dir "../"

#define lukeos_tällainen(...) _lukeos_tällainen(__VA_ARGS__, 0)
void _lukeos_tällainen(const char* nimi, FILE* f, ...) {
    char sana[128];
    int sij = ftell(f);
    while(fscanf(f, "%127s", sana) == 1)
	if(!strcmp(nimi, sana)) goto kelpaa;
    assert(0);
kelpaa:
    va_list ls;
    va_start(ls, f);
    float *viite;
    while((viite = va_arg(ls, float*)))
	assert(fscanf(f, "%f", viite) == 1);
    va_end(ls);
    fseek(f, sij, SEEK_SET);
}

void löydä_kohta(const char* nimi, FILE* f, int mistä) {
    char sana[128];
    fseek(f, 0, mistä);
    while(fscanf(f, "%s", sana) == 1)
	if(strstr(sana, nimi)) return;
    assert(0);
}

void kirjoita(FILE* f, const char* nimi, float* arvo, int tarkk) {
    fprintf(f, "%s", nimi);
    for(int k=0; k<kausia*2; k++)
	fprintf(f, " & %.*f", tarkk, arvo[k]);
    fprintf(f,  " \\\\\n");
}

float ylä[kausia_m*2], ala[kausia_m*2], osuus[kausia_m*2], r²[kausia_m*2], osuma[kausia_m*2];

void lue_kausi(int k, FILE* f, int ikirko) {
    char sana[128];
    int sij = ftell(f);
    int ind = k*2+ikirko;
    lukeos_tällainen("rajat:",       f, ylä+ind, ala+ind);
    lukeos_tällainen("hyväksyttyä:", f, osuus+ind);
    lukeos_tällainen("r²:",          f, r²+ind);
    lukeos_tällainen("osuma:",       f, osuma+ind);
}

int main() {
    FILE *f = fopen("sovitteet.txt", "r");
    char sana[128];
    for(int k=0; k<kausia; k++) {
	löydä_kohta(kaudet[k], f, SEEK_SET); // lämmin
	lue_kausi(k, f, 0);
	löydä_kohta(kaudet[k], f, SEEK_CUR); // kylmä
	lue_kausi(k, f, 1);
    }

    f = freopen(dir"wregr_rajat.tex", "w", f);
    fprintf(f, "\\begin{tabular}{l");
    for(int k=0; k<kausia; k++)
	fprintf(f, "|rr");
    fprintf(f, "}\n");
    for(int k=0; k<kausia; k++)
	fprintf(f, " & \\multicolumn{2}{c}{%s}", kaudet[k]);
    fprintf(f, " \\\\\n");
    for(int k=0; k<kausia; k++)
	fprintf(f, " & {warm} & {cold}");
    fprintf(f, " \\\\\n\\midrule\n");

    kirjoita(f, "upper flux limit", ylä, 0);
    kirjoita(f, "lower flux limit", ala, 0);
    kirjoita(f, "accepted proportion", osuus, 4);
    kirjoita(f, "$\\frac{\\text{obtained}}{\\text{target}}$ average flux", osuma, 4);
    kirjoita(f, "R$^2$", r², 4);

    fprintf(f, "\\end{tabular}\n");
    fclose(f);
}

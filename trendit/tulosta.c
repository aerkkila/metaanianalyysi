#include <stdio.h>

#define max_kausia 6
#define max_muuttujat 6

struct tul_jasen {
    float kulmak, parvot;
    char lajinimi[26];
};

struct tul_maarite {
    int nmuutt, kausia;
    char *kaudet_ulos[max_kausia], *muuttujat[max_muuttujat], *variables[max_muuttujat], latexmuutt[max_muuttujat];
};

int kausijärj[max_kausia];

FILE* csv;
FILE* tex;

static void alusta_lista(const struct tul_maarite* restrict m, const char* kantanimi) {
    char nimi[strlen(kantanimi)+5];
    sprintf(nimi, "%s.csv", kantanimi);
    csv = fopen(nimi, "w");
    strcpy(strstr(nimi, ".csv"), ".tex");
    tex = fopen(nimi, "w");

    // latex-tiedoston alustaminen
    fprintf(tex, "\\begin{tabular}{l");
    for(int i=0; i<m->nmuutt; i++) {
	if(!m->latexmuutt[i])
	    continue;
        fputc('|', tex);
	for(int j=0; j<m->kausia; j++)
	    fputc('r', tex);
    }
    fprintf(tex, "}\n");
    for(int i=0; i<m->nmuutt; i++) {
	if(!m->latexmuutt[i])
	    continue;
        fprintf(tex, " & \\multicolumn{%i}{c}{%s}", m->kausia, m->variables[i]);
    }
    fprintf(tex, " \\\\\n");
    for(int i=0; i<m->nmuutt; i++) {
	if(!m->latexmuutt[i])
	    continue;
	for(int j=0; j<m->kausia; j++)
            fprintf(tex, " & {%s}", m->kaudet_ulos[j]);
    }
    fprintf(tex, " \\\\\n\\midrule\n");

    // csv:n alustaminen
    for(int i=0; i<m->nmuutt; i++) {
        fprintf(csv, ",%s", m->muuttujat[i]);
	for(int j=0; j<m->kausia-1; j++)
	    fputc(',', csv);
    }
    fputc('\n', csv);
    for(int i=0; i<m->nmuutt; i++)
	for(int j=0; j<m->kausia; j++)
            fprintf(csv, ",%s", m->kaudet_ulos[j]);
    fputc('\n', csv);
}

char _csvbuf[12];
char* csvväri(float arvo) {
    return strcpy(_csvbuf,
	    arvo < 0.01? "\033[1;91m":
	    arvo < 0.03? "\033[94m":
	    arvo < 0.05? "\033[92m":
	    ""), _csvbuf;
}

char _texbuf[32];
char* latexluku(float arvo, float luku) {
    static const char* muodot[] = {
	"\\textbf{%.@f}", "%.@f", "(%.@f)", "\\textcolor{blue}{%.@f}",
    };
    const char tarkk = '3';
    const float rajat[] = {0.01, 0.03, 0.05};
    int i;
    for(i=0; i<3; i++)
	if(arvo < rajat[i])
	    break;
    char muoto[32];
    strcpy(muoto, muodot[i]);
    *strchr(muoto, '@') = tarkk;
    return sprintf(_texbuf, muoto, luku), _texbuf;
}

void tulosta_jasen(struct tul_jasen* jäs, const struct tul_maarite* m) {
    int i=0;
    static int x = 0;
    if(x == 0) {
	char* lajinimi = jäs->lajinimi + strlen(m->muuttujat[x/m->kausia]) + 1;
	fprintf(csv, "%s", lajinimi);
	char* ptr = lajinimi;
	while((ptr=strchr(ptr, '_'))) *ptr = ' ';
	fprintf(tex, "%s", lajinimi);
    }

    float luku = jäs->kulmak*10; // trendit kymmentä vuotta kohti
    float arvo = jäs->parvot;
    fprintf(csv, ",%s%.3f\033[0m", csvväri(arvo), luku);
    if(m->latexmuutt[x / m->kausia])
	fprintf(tex, " & %s", latexluku(arvo, luku));

    if(++x == m->nmuutt*m->kausia) {
	fprintf(csv, "\n");
	fprintf(tex, " \\\\\n");
	x = 0;
    }
}

static void lopeta_lista() {
    fprintf(tex, "\\end{tabular}\n");
    csv = (fclose(csv), NULL);
    tex = (fclose(tex), NULL);
}

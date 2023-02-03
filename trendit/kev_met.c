#include <fcntl.h>
#include <unistd.h>
#include <err.h>
#include <stdio.h>

typedef double mk_ytyyppi;
typedef double mk_xtyyppi;
#include "mkts.c"

int _num;
#define R(f,a,b) if((_num=read(f, a, b)) != (int)(b)) warn("read rivillä %i (%i != %i)", __LINE__, _num, (int)(b))

static void mkts(float* kohde, const double* data, const double* vuodet, int vuosia) {
    /*
    float y[vuosia];
    for(int i=0; i<vuosia; i++)
	y[i] = data[i]; // vakiotermi määritetään muutettavasta float-taulukosta
	*/
    kohde[0] = mannkendall(data, vuosia);
    kohde[1] = ts_kulmakerroin_yx(data, vuodet, vuosia);
    //kohde[2] = ts_vakiotermi_yx(y, vuodet, vuosia, kohde[1]);
}

char* latexluku(float f[2], char* _texbuf) {
    static const char* muodot[] = {
	"\\textbf{%.@f}", "%.@f", "(%.@f)", "\\textcolor{blue}{%.@f}",
    };
    const char tarkk = '3';
    const float rajat[] = {0.01, 0.03, 0.05};
    int i;
    for(i=0; i<3; i++)
	if(f[0] < rajat[i])
	    break;
    char muoto[32];
    strcpy(muoto, muodot[i]);
    *strchr(muoto, '@') = tarkk;
    return sprintf(_texbuf, muoto, f[1]*10), _texbuf;
}

int main() {
    int fd;
    char vuosia, ik;
    if((fd = open("kev_met.bin", O_RDONLY)) < 0)
	err(1, "open");
    R(fd, &vuosia, 1);
    R(fd, &ik, 1);
    ik++; // myös kokonaisalue
    double vuodet[vuosia], emi[ik][vuosia], vuo[ik][vuosia];
    R(fd, vuodet, vuosia*sizeof(double));
    R(fd, emi, ik*vuosia*sizeof(double));
    R(fd, vuo, ik*vuosia*sizeof(double));
    close(fd);

    float kohde[2][ik][2];
    for(int i=0; i<ik; i++) {
	mkts(kohde[0][i], emi[i], vuodet, vuosia);
	mkts(kohde[1][i], vuo[i], vuodet, vuosia);
    }

    /* latex-taulukko */
    FILE *f = fopen("kev_met.tex", "w");
    fprintf(f, "\\begin{tabular}{l|rr}\n"
	    " & emission ($\\Delta$(Tg) / 10 yr) & flux ($\\Delta$(nmol m$^{-2}$ s$^{-1}$) / 10 yr) \\\\\n"
	    "\\midrule\n");
    char* nimet[] = {"nonpermafrost", "sporadic", "discontinuous", "continuous", "total"};

    char buf[2][30];
    for(int i=0; i<ik; i++)
	fprintf(f, "%s & %s & %s \\\\\n", nimet[i], latexluku(kohde[0][i], buf[0]), latexluku(kohde[1][i], buf[1]));

    fprintf(f, "\\end{tabular}\n");
    fclose(f);
}

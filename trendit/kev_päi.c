#include <stdio.h>
#include <err.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <string.h>

#include "tulosta.c" // latexluku
#define jvuosia 11

const char* ikirnimet[] = {"nonpermafrost", "sporadic", "discontinuous", "continuous"};

typedef short mk_ytyyppi;
typedef short mk_xtyyppi;
#include "mkts.c"

int _num;
#define R(f,a,b) if((_num=read(f, a, b)) != (int)(b)) warn("read rivillä %i (%i != %i)", __LINE__, _num, (int)(b))

void lue_jäätym(short tulos[3][4][jvuosia]) {
    char* nimet[] = {"start", "end", "length"};
    char nimi[64];
    for(int e0=0; e0<3; e0++) {
	sprintf(nimi, "../kausidata2301/%s_ikir.csv", nimet[e0]);
	int fd = open(nimi, O_RDONLY);
	struct stat st;
	fstat(fd, &st);
	char* tiedosto = mmap(NULL, st.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
	close(fd);
	char* ptr = tiedosto;
	for(int i=0; i<4; i++) {
	    ptr = strstr(ptr, "freezing");
	    for(int v=0; v<jvuosia; v++) {
		ptr = strchr(ptr, ',');
		tulos[e0][i][v] = atoi(++ptr);
	    }
	}
	munmap(tiedosto, st.st_size);
    }
}

int main() {
    int fd = open("kevään_päivät.bin", O_RDONLY);
    char vuosia, ik;
    R(fd, &vuosia, 1);
    R(fd, &ik, 1);
    short alut[ik][vuosia];
    short loput[ik][vuosia];
    short vuodet[12];
    R(fd, alut, ik*vuosia*sizeof(short));
    R(fd, loput, ik*vuosia*sizeof(short));
    close(fd);

    for(int i=0; i<12; i++)
	vuodet[i] = 2011+i;

    FILE *f = fopen("kevsyk.tex", "w");
    fprintf(f, "\\begin{tabular}{l|rrr|rrr}\n"
	    " & \\multicolumn{3}{c}{freezing} & \\multicolumn{3}{c}{spring} \\\\\n"
	    " & start & end & length & start & end & length \\\\\n"
	    "\\midrule\n");

    short jäätym[3][4][jvuosia];
    lue_jäätym(jäätym);

    for(int i=0; i<ik; i++) {
	float p, a;
	fprintf(f, "%s", ikirnimet[i]);
	/* jäätyminen */
	for(int j=0; j<3; j++) {
	    p = mannkendall(jäätym[j][i], jvuosia);
	    a = ts_kulmakerroin_yx(jäätym[j][i], vuodet, jvuosia);
	    fprintf(f, " & %s", latexluku(p, a*10));
	}
	/* kevät */
	/* alut */
	p = mannkendall(alut[i], vuosia);
	a = ts_kulmakerroin_yx(alut[i], vuodet, vuosia);
	fprintf(f, " & %s", latexluku(p, a*10));
	/* loput */
	p = mannkendall(loput[i], vuosia);
	a = ts_kulmakerroin_yx(loput[i], vuodet, vuosia);
	fprintf(f, " & %s", latexluku(p, a*10));
	/* pituudet */
	for(int v=0; v<vuosia; v++)
	    loput[i][v] -= alut[i][v];
	p = mannkendall(loput[i], vuosia);
	a = ts_kulmakerroin_yx(loput[i], vuodet, vuosia);
	fprintf(f, " & %s", latexluku(p, a*10));
	fprintf(f, " \\\\\n");
    }
    fprintf(f, "\\end{tabular}\n");
    fclose(f);
}

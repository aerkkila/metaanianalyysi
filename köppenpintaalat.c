#include <stdio.h>
#include <math.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <assert.h>

const char* const nimet[] = {"", "D.b", "D.c", "D.d", "ET"};

const double r2 = 6362132.0*6362132.0;
#define ASTE 0.017453293
#define PINTAALA(lat, hila) ((hila) * r2 * (sin((lat)+0.5*(hila)) - sin((lat)-0.5*(hila))))

int main() {
    int fd = open("köppenmaski.txt", O_RDONLY);
    struct stat filestat;
    fstat(fd, &filestat);
    int pit = filestat.st_size;
    assert(pit==19800);
    char ptr[pit];
    read(fd, ptr, pit);

    double alat[55];
    for(int i=0; i<55; i++)
	alat[i] = PINTAALA(ASTE*(29.5+i), ASTE);
    double köppenalat[5] = {0};
    for(int i=0; i<pit; i++)
	köppenalat[(int)ptr[i]-'0'] += alat[i/360];

    for(int i=1; i<5; i++)
	printf("%-3s: %5.1lf Mkm$^2$\\\\\n", nimet[i], köppenalat[i]*1e-6*1e-6);

    close(fd);
}

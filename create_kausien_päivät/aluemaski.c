#include <nctietue3.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define indir "ftpercent/"
typedef char tyyppi; const int nctyyppi = NC_BYTE;

int main() {
    nct_set* set = nct_read_nc(indir "number_of_pixels.nc");
    char* vuoret = nct_read_from_nc("vuoret.nc", "luokka");
    nct_var* var = nct_firstvar(set);
    int xypit = var->len;
    int xpit = nct_get_var(set, "lon")->len;
    const double* lat = nct_get_var(set, "lat")->data;
    tyyppi* maski = malloc(xypit*sizeof(tyyppi));
    memset(maski, 0, xypit*sizeof(tyyppi));
    const char* data = var->data;
    int j_alku = 0;
    while(lat[j_alku] < 50)
	j_alku++;
    for(int i=j_alku*xpit; i<xypit; i++)
	maski[i] = data[i] > 0 && !vuoret[i];
    nct_set ulos = {0};
    nct_copy_var(&ulos, nct_get_var(set, "lat"), 1);
    nct_copy_var(&ulos, nct_get_var(set, "lon"), 1);
    nct_add_var_alldims(&ulos, maski, nctyyppi, "maski");
    nct_write_nc(&ulos, "aluemaski.nc");
    nct_free(&ulos, set);
    free(vuoret);
}

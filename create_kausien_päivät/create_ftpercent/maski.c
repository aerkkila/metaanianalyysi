#include <nctietue3.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define indir "data/"
typedef char tyyppi; const int nctyyppi = NC_BYTE;

int main() {
    nct_set* set = nct_read_mfnc_regex(indir "^L3FT_[0-9]\\{4\\}.nc", 0, "time");
    nct_var* var = nct_firstvar(set);
    int tpit = nct_get_vardim(var, 0)->len;
    int xypit = nct_get_len_from(var, 1);
    tyyppi* maski = malloc(xypit*sizeof(tyyppi));
    memset(maski, -1, xypit*sizeof(tyyppi));
    const char* data = var->data;
    for(int t=0; t<tpit; t++)
	for(int i=0; i<xypit; i++)
	    if (data[t*xypit+i] > 0)
		maski[i] = 1;
    nct_set ulos = {0};
    nct_copy_var(&ulos, nct_get_var(set, "y"), 1);
    nct_copy_var(&ulos, nct_get_var(set, "x"), 1);
    nct_add_var_alldims(&ulos, maski, nctyyppi, "data");
    nct_write_nc(&ulos, "maski.nc");
    nct_free(&ulos, set);
}

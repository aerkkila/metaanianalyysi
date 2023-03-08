#include <nctietue3.h>
#include <stdio.h>

int main(int argc, char** argv) {
    if(argc < 2) {
	puts("argumentti puuttuu");
	return 1; }
    nct_readm_nc(set, argv[1]);
    nct_var* var0 = nct_get_var(&set, "tundra_wetland");
    var0 = nct_rename(nct_copy_var(&set, var0, 0), "wetland_prf", 0);
    double* data0 = var0->data;
    double* data1 = nct_get_var(&set, "permafrost_bog")->data;
    size_t pit = var0->len;
    for(int i=0; i<pit; i++)
	data0[i] += data1[i];
    var0 = nct_get_var(&set, "bog");
    var0 = nct_rename(nct_copy_var(&set, var0, 0), "wetland_nonprf", 0);
    data0 = var0->data;
    data1 = nct_get_var(&set, "fen")->data;
    double* data2 = nct_get_var(&set, "marsh")->data;
    for(int i=0; i<pit; i++)
	data0[i] += data1[i]+data2[i];
    nct_write_nc(&set, argv[1]);
    nct_free1(&set);
}

#include <nctietue2.h>
#include <stdio.h>

int main(int argc, char** argv) {
    if(argc < 2) {
	puts("argumentti puuttuu");
	return 1; }
    nct_vset* vset = nct_read_ncfile(argv[1]);
    nct_var* var0 = nct_vardup(nct_get_var(vset, "tundra_wetland"), "wetland_prf");
    double* data0 = var0->data;
    double* data1 = nct_get_var(vset, "permafrost_bog")->data;
    size_t pit = nct_get_varlen(var0);
    for(int i=0; i<pit; i++)
	data0[i] += data1[i];
    data0 = nct_vardup(nct_get_var(vset, "bog"), "wetland_nonprf")->data;
    data1 = nct_get_var(vset, "fen")->data;
    double* data2 = nct_get_var(vset, "marsh")->data;
    for(int i=0; i<pit; i++)
	data0[i] += data1[i]+data2[i];
    nct_write_ncfile(vset, argv[1]);
    nct_free_vset(vset);
}

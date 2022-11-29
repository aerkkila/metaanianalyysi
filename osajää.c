#include <nctietue2.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <err.h>
#include <stdlib.h>
#include <time.h>

#define kansio "../smos_uusi/ft_percent/"

#define kansio_alku "../smos_uusi/start_end/"

nct_vset* lue_alut(const char* restrict regex, char* dim, int xtype) {
    char* nimet = nct__get_filenames(regex, 0);
    int n = (intptr_t)nct__get_filenames(NULL, 0);
    nct_vset* vset = nct_read_ncmultifile_ptr(nimet, n, dim);
    int dimid = nct_get_dimid(vset, dim);
    int* vuodet = malloc(n*sizeof(int));
    char* ptr = nimet;
    int pit1 = strlen("vvvv.nc");
    for(int i=0; i<n; i++) {
	int pit = strlen(ptr);
	if(sscanf(ptr+pit-pit1, "%i", vuodet+i) != 1)
	    warn("sscanf %s", ptr+pit-pit1);
	vuodet[i]++; // korjataan vuosinumerointi intuitiivisemmaksi
	ptr += pit+1;
    }
    nct_dim2var(vset->dims[dimid], vuodet, xtype);
    free(nimet);
    return vset;
}

#define onko_osittain(k,o) ((k)*9+(o) >= 0.9)

int main() {
    nct_vset* ft = nct_read_ncmultifile_regex(kansio "^partly_frozen_percent_pixel_[0-9]*.nc", 0, "@0");
    float* osittdt = nct_next_truevar(ft->vars[0], 0)->data;

    nct_vset* ft_kokon = nct_read_ncmultifile_regex(kansio "^frozen_percent_pixel_[0-9]*.nc", 0, "@0");
    float* kokondt = nct_next_truevar(ft->vars[0], 0)->data;

    char* maski = nct_read_from_ncfile("aluemaski.nc", "maski", NULL, -1);

    nct_vset* alku = lue_alut(kansio_alku "^freezing_start_doy_[0-9]*.nc", "vuosi", NC_INT);
    nct_var* alkuvar = nct_next_truevar(alku->vars[0], 0);
    float* fpäivät = alkuvar->data;
    int pit_xy = nct_get_varlen_from(alkuvar, 1);
    int päivä0 = 0;

    NCTDIM(*alku, "vuosi").len--;
    nct_var* varvuodet = &NCTVAR(*alku, "vuosi");
    int n = --varvuodet->len;
    alkuvar->len = nct_get_varlen_from(alkuvar, 0);
    int* vuodet = varvuodet->data;

    struct tm aikatm = {.tm_year=vuodet[0]-1900, .tm_mday=1};
    int alkujen_ero = (mktime(&aikatm) - nct_mktime0(&NCTDIM(*ft, "time"), NULL).a.t) / 86400;

    for(int v=0; v<n; v++) {
	int offset = v*pit_xy;
	for(int i=0; i<pit_xy; i++) {
	    if(!maski[i]) {
		fpäivät[v*pit_xy+i] = 0.0f / 0.0f;
		continue; }
	    int ind = (int)fpäivät[i+offset] + päivä0 + alkujen_ero;
	    fpäivät[i+offset] = ind;//osittdt[ind*pit_xy+i];
	}
	päivä0 += 365 + (vuodet[v]%4==0 && (vuodet[v]%100 || !(vuodet[v]%400)));
    }

    for(int t=0; t<n; t++) {
	int vxy = t*pit_xy;
	for(int i=0; i<pit_xy; i++) {
	    if(fpäivät[vxy+i] != fpäivät[vxy+i]) continue;
	    int päivä = (int)fpäivät[vxy+i];
	    int ind = päivä*pit_xy + i;
	    int j=0;
	    while(onko_osittain(kokondt[ind-j*pit_xy], osittdt[ind-j*pit_xy])) j++;
	    fpäivät[vxy+i] = j;
	}
    }

    nct_write_ncfile(alku, "testi.nc");

    free(maski);
    nct_free_vset(alku);
    nct_free_vset(ft);
    nct_free_vset(ft_kokon);
}

#include <nctietue3.h>
#include <string.h>

int main() {
    nct_readm_ncf(set, "ft_percent/frozen_percent_pixel_2014.nc", nct_rlazy);

    nct_var* var = nct_firstvar(&set);
    nct_load_as(var, NC_FLOAT);
    const float* dt = var->data;

    int pit = var->len;
    int lonpit = nct_loadg_as(&set, "lon", NC_FLOAT)->len;
    float* lat = nct_loadg_as(&set, "lat", NC_FLOAT)->data;

    /* Vähintään 50° N */
    int alku = 0;
    while(lat[alku] < 50) alku++;
    alku *= lonpit;

    /* Smos-data määritelty. */
    char maski[pit];
    memset(maski, 0, alku);
    for(int i=alku; i<pit; i++)
	maski[i] = dt[i]==dt[i];

    /* Ei Aasian eteläisiä vuoristoja.
       Ikirmaski on luotu lukemalla ikirdata.nc ja piirtämällä siihen käsin se alue, joka ei kelpaa
       ja laittamalla arvoksi 5. */
    nct_readm_ncf(ikir, "ikirmaski.nc", nct_rlazy);
    char* cdt = nct_loadg_as(&ikir, "luokka", NC_BYTE)->data;
    for(int i=alku; i<pit; i++)
	maski[i] = maski[i] && cdt[i]!=5;

    nct_set tallenn = {0};
    nct_copy_var(&tallenn, nct_get_var(&set, "lat"), 1);
    nct_copy_var(&tallenn, nct_get_var(&set, "lon"), 1);
    nct_add_var_alldims(&tallenn, maski, NC_BYTE, "maski") -> not_freeable = 1;
    nct_write_nc(&tallenn, "tee_yhdistelmä/muunnos.nc"); // muualla on linkitetty tuohon

    nct_free(&tallenn, &set, &ikir);
}

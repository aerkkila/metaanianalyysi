#include <nctietue2.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <err.h>

#define kansio "ft_percent/"
#define talvi 3
#define jäätym 2
#define kesä 1

const char* aika0str = "days since 2010-08-01";
struct tm aika0tm = {.tm_year=2011-1900, .tm_mon=8-1, .tm_mday=1};
time_t t0;
#define jäätyykö(froz, part) ((froz)*9+(part) >= 0.9)
//#define jäätyykö(froz, part) (froz >= 0.1)

int päiviä_taitteeseen(int t, int seur) {
    struct tm aika0 = aika0tm;
    aika0.tm_mday += t;
    time_t a0 = mktime(&aika0);
    aika0.tm_mon=aika0tm.tm_mon;
    aika0.tm_mday=aika0tm.tm_mday;
    aika0.tm_year += seur;
    time_t a1 = mktime(&aika0);
    return (a1-a0) / 86400;
}

int talven_pituus(float* fr, int aika0, int pit_xy) {
    int ajan_huippu = päiviä_taitteeseen(aika0, 0);
    if(ajan_huippu < 0)
	ajan_huippu = päiviä_taitteeseen(aika0, 1);
    int pit = 0;
    for(int i=0; i<ajan_huippu; i++)
	if(fr[i*pit_xy] >= 0.9)
	    pit = i+1;
    return pit;
}

/* Jos jatkuu kesään eikä talveen, lisättäköön pituuteen 10000 merkiksi siitä. */
int jäätym_pituus(float* fr, float* pr, int aika0, int pit_xy) {
    int ajan_huippu = päiviä_taitteeseen(aika0, 0);
    if(ajan_huippu < 0)
	ajan_huippu = päiviä_taitteeseen(aika0, 1);
    int pit = 0;
    for(int i=0; i<ajan_huippu; i++)
	if(fr[i*pit_xy] >= 0.9)
	    return i;
	else if(jäätyykö(fr[i*pit_xy], pr[i*pit_xy]))
	    pit = i+1;
    return pit+10000;
}

int main(int argc, char** argv) {
    nct_vset* partly = nct_read_ncmultifile_regex(kansio "^partly_frozen_percent_pixel_[0-9]*.nc$", 0, NULL);
    nct_vset* frozen = nct_read_ncmultifile_regex(kansio "^frozen_percent_pixel_[0-9]*.nc$", 0, NULL);
    char* maski = nct_read_from_ncfile("aluemaski.nc", NULL, NULL, 0);

    t0 = mktime(&aika0tm);
    nct_convert_timeunits(nct_get_var(partly, "time"), aika0str); // käytännössä tämä vain lisää vakion aika-arvoihin
    nct_convert_timeunits(nct_get_var(frozen, "time"), aika0str);
    nct_var* aika = nct_get_var(partly, "time");
    int t_alku = -((int*)aika->data)[0];
    int t_pit = (aika->len-t_alku)/365*365;

    int pit_xy = nct_get_varlen_from(nct_next_truevar(partly->vars[0], 0), 1);
    struct tm aika1tm = aika0tm;
    aika1tm.tm_mday += t_pit;
    char* kausi = malloc(t_pit*pit_xy);

    float* froz = nct_next_truevar(frozen->vars[0], 0)->data;
    float* part = nct_next_truevar(partly->vars[0], 0)->data;

    for(int i=0; i<pit_xy; i++) {
	printf("\r%i/%i ", i+1, pit_xy);
	fflush(stdout);
	if(!maski[i]) {
	    for(int t=0; t<t_pit; t++)
		kausi[t*pit_xy+i] = 0;
	    continue;
	}
	int t = t_alku;

	for(; froz[t*pit_xy+i] != froz[t*pit_xy+i]; t++)
	    kausi[(t-t_alku)*pit_xy+i] = 0;

kesä_loppuun:
	for(; !jäätyykö(froz[t*pit_xy+i], part[t*pit_xy+i]); t++) {
	    if(t >= t_pit+t_alku)
		goto aika_päättyi;
	    kausi[(t-t_alku)*pit_xy+i] = kesä;
	}
	if(froz[t*pit_xy+i] >= 0.9) {
	    kausi[(t++-t_alku)*pit_xy+i] = talvi; // muuten tämä juuttuu ellei taitteessa ei ole kesä
	    if(t>=t_pit+t_alku)
		goto aika_päättyi;
	    goto talvi_loppuun; }
	kausi[(t++-t_alku)*pit_xy+i] = jäätym; // sama koskee tätä
	if(t>=t_pit+t_alku)
	    goto aika_päättyi;
	goto jäätyminen_loppuun;

talvi_loppuun:
	int jäljellä = talven_pituus(froz+t*pit_xy+i, t-t_alku, pit_xy);
        if(t+jäljellä > t_pit+t_alku)
	    jäljellä = t_pit+t_alku-t;
	for(int tt=0; tt<jäljellä; tt++, t++)
	    kausi[(t-t_alku)*pit_xy+i] = talvi;
	if(t >= t_pit+t_alku)
	    goto aika_päättyi;
	goto kesä_loppuun_keväällä;

jäätyminen_loppuun:
	jäljellä = jäätym_pituus(froz+t*pit_xy+i, part+t*pit_xy+i, t-t_alku, pit_xy);
	int seuraava = talvi;
	if(jäljellä > 9999) { // tämä päätettiin merkitä näin
	    seuraava = kesä;
	    jäljellä -= 10000;
	}
        if(t+jäljellä > t_pit+t_alku)
	    jäljellä = t_pit+t_alku-t;
	for(int tt=0; tt<jäljellä; tt++, t++)
	    kausi[(t-t_alku)*pit_xy+i] = jäätym;
	if(t >= t_pit+t_alku)
	    goto aika_päättyi;
	if(seuraava == talvi)
	    goto talvi_loppuun;
	goto kesä_loppuun_keväällä;

kesä_loppuun_keväällä:
	jäljellä = päiviä_taitteeseen(t-t_alku, 0);
	if(jäljellä < 0)
	    jäljellä = päiviä_taitteeseen(t-t_alku, 1);
        if(t+jäljellä > t_pit+t_alku)
	    jäljellä = t_pit+t_alku-t;
	for(int tt=0; tt<jäljellä; tt++, t++)
	    kausi[(t-t_alku)*pit_xy+i] = kesä;
	goto kesä_loppuun;

aika_päättyi:;
    }
    putchar('\n');

    nct_vset k = {0};
    nct_var* var = nct_add_dim(&k, nct_range_NC_INT(0,t_pit,1), t_pit, NC_INT, "time");
    nct_add_varatt_text(var, "units", (char*)aika0str, 0);
    nct_copy_var(&k, nct_get_var(partly, "lat"), 1);
    nct_copy_var(&k, nct_get_var(partly, "lon"), 1);
    int dimids[] = {0,1,2};
    nct_add_var(&k, kausi, NC_BYTE, "kausi", 3, dimids);
    nct_write_ncfile(&k, "kaudet.nc");
    free(maski);
    nct_free_vset(&k);
    nct_free_vset(partly);
    nct_free_vset(frozen);
}

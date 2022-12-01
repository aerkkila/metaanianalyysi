#include <nctietue2.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <err.h>
#include <assert.h>

#define kansio "ft_percent/"
#define talvi 3
#define jäätym 2
#define kesä 1

#define jäätyykö(froz, part) ((froz)*9+(part) >= 0.9)
//#define jäätyykö(froz, part) (froz >= 0.1)

/* Jos aika0 on karkausvuonna, alkupäiviin tulee pieni virhe. */
const char* aika0str = "days since 2010-08-01";
struct tm aika0tm = {.tm_year=2010-1900, .tm_mon=8-1, .tm_mday=1};
time_t t0;
#define taitesekunteja 16
time_t taitesekunnit[taitesekunteja];

int päiviä_taitteeseen(int t, int seur) {
    struct tm aika1tm = aika0tm;
    aika1tm.tm_mday += t;
    time_t t1 = mktime(&aika1tm);
    /*
    aika1tm.tm_mon  = aika0tm.tm_mon;
    aika1tm.tm_mday = aika0tm.tm_mday;
    aika1tm.tm_year += seur;
    time_t t2 = mktime(&aika1tm);
    Yllä oleva korvataan valmiiksi lasketuilla taitesekunneilla. */
    time_t t2 = taitesekunnit[aika1tm.tm_year - aika0tm.tm_year + seur];
    return (t2-t1) / 86400;
}

int v_g, yday_g, t_alku_g, kark_g;
void aikamuunnos(int t) {
   struct tm aika1tm = aika0tm;
   aika1tm.tm_mday += t-t_alku_g;
   mktime(&aika1tm);
   int v = aika1tm.tm_year+1900;
   kark_g = !(v%4) && (v%100 || !v%400);
   if(aika1tm.tm_yday-kark_g >= aika0tm.tm_yday) { // syksy
       v_g    = aika1tm.tm_year - aika0tm.tm_year;
       yday_g = aika1tm.tm_yday - kark_g - 365;
   }
   else { // kevät
       v_g    = aika1tm.tm_year - aika0tm.tm_year - 1;
       yday_g = aika1tm.tm_yday;
   }
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

int pit_xy_g;
void vaihdepäivä(int t, int p, float* loppuva[2], float* alkava[2]) {
    aikamuunnos(t);
    loppuva[1][v_g*pit_xy_g+p] = yday_g;
    alkava[0][v_g*pit_xy_g+p] = yday_g;
}

void vaihdepäivä1(int t, int p, float* loppuva[2], float* alkava[2]) {
    aikamuunnos(t);
    alkava[0][v_g*pit_xy_g+p] = yday_g;
    if(v_g > 0)
	loppuva[1][(v_g-1)*pit_xy_g+p] = yday_g + 365 - kark_g;
}

struct päiväluvut {
    float *k[2], *j[2], *t[2];
};

void alusta_päiväluvut(struct päiväluvut* pl, int pit_xy, int tpit) {
    int vuosia = tpit/366+1;
    for(int i=0; i<2; i++) {
	pl->k[i] = malloc(pit_xy*vuosia*sizeof(float));
	pl->j[i] = malloc(pit_xy*vuosia*sizeof(float));
	pl->t[i] = malloc(pit_xy*vuosia*sizeof(float));
	assert(pl->k[i] && pl->j[i] && pl->t[i]);
	for(int j=0; j<vuosia*pit_xy; pl->k[i][j++]=0.0f/0.0f);
	for(int j=0; j<vuosia*pit_xy; pl->j[i][j++]=0.0f/0.0f);
	for(int j=0; j<vuosia*pit_xy; pl->t[i][j++]=0.0f/0.0f);
    }
}

void alusta_taitesekunnit() {
    struct tm aikatm = aika0tm;
    for(int i=0; i<taitesekunteja; i++) {
	taitesekunnit[i] = mktime(&aikatm);
	aikatm.tm_year++;
    }
}

int main(int argc, char** argv) {
    nct_vset* partly = nct_read_ncmultifile_regex(kansio "^partly_frozen_percent_pixel_[0-9]*.nc$", 0, NULL);
    nct_vset* frozen = nct_read_ncmultifile_regex(kansio "^frozen_percent_pixel_[0-9]*.nc$", 0, NULL);
    char* maski = nct_read_from_ncfile("aluemaski.nc", NULL, NULL, 0);

    t0 = mktime(&aika0tm);
    nct_convert_timeunits(nct_get_var(partly, "time"), aika0str); // käytännössä tämä vain lisää vakion aika-arvoihin
    nct_convert_timeunits(nct_get_var(frozen, "time"), aika0str);
    nct_var* aika = nct_get_var(partly, "time");
    const int t_alku = -((int*)aika->data)[0];
    t_alku_g = t_alku;
    int t_pit = (aika->len-t_alku)/365*365;

    const int pit_xy = nct_get_varlen_from(nct_next_truevar(partly->vars[0], 0), 1);
    pit_xy_g = pit_xy;
    struct tm aika1tm = aika0tm;
    aika1tm.tm_mday += t_pit;
    char* kausi = malloc(t_pit*pit_xy);

    float* froz = nct_next_truevar(frozen->vars[0], 0)->data;
    float* part = nct_next_truevar(partly->vars[0], 0)->data;

    struct päiväluvut pl;
    alusta_päiväluvut(&pl, pit_xy, t_pit);

    alusta_taitesekunnit();

    for(int i=0; i<pit_xy; i++) {
	printf("\r%i/%i ", i+1, pit_xy);
	fflush(stdout);
	if(!maski[i]) {
	    for(int t=0; t<t_pit; t++)
		kausi[t*pit_xy+i] = 0;
	    continue;
	}
	int t = t_alku;

	for(; t<t_pit && froz[t*pit_xy+i] != froz[t*pit_xy+i]; t++)
	    kausi[(t-t_alku)*pit_xy+i] = 0;

kesä_loppuun:
	for(; !jäätyykö(froz[t*pit_xy+i], part[t*pit_xy+i]); t++) {
	    if(t >= t_pit+t_alku)
		goto aika_päättyi;
	    kausi[(t-t_alku)*pit_xy+i] = kesä;
	}
	/* Ensimmäinen päivä talvesta tai syksystä pitää laittaa jo täällä,
	 * koska muuten tämä kiertää loputtomasti ellei taitteessa ole kesä. */
	if(froz[t*pit_xy+i] >= 0.9) {
	    vaihdepäivä1(t, i, pl.k, pl.t);
	    kausi[(t++-t_alku)*pit_xy+i] = talvi;
	    if(t>=t_pit+t_alku)
		goto aika_päättyi;
	    goto talvi_loppuun; }

	vaihdepäivä1(t, i, pl.k, pl.j);
	kausi[(t++-t_alku)*pit_xy+i] = jäätym;
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
	vaihdepäivä(t, i, pl.t, pl.k);
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
	if(seuraava == talvi) {
	    vaihdepäivä(t, i, pl.j, pl.t);
	    goto talvi_loppuun; }
	vaihdepäivä(t, i, pl.j, pl.k);
	goto kesä_loppuun_keväällä;

/* Toisin kuin kohdassa kesä_loppuun tässä mikään ei laukaise jäätymiskautta tai talvea. */
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

    nct_var* latvar = nct_get_var(partly, "lat");
    nct_var* lonvar = nct_get_var(partly, "lon");
    int dimids[] = {0,1,2};

    nct_vset k = {0};
    nct_var* var = nct_add_dim(&k, nct_range_NC_INT(0,t_pit,1), t_pit, NC_INT, "time");
    nct_add_varatt_text(var, "units", (char*)aika0str, 0);
    nct_copy_var(&k, latvar, 1);
    nct_copy_var(&k, lonvar, 1);
    nct_add_var(&k, kausi, NC_BYTE, "kausi", 3, dimids);
    nct_write_ncfile(&k, "kaudet.nc");
    nct_free_vset(&k);

    k = (nct_vset){0};
    int vuosia = t_pit/366+1;
    int vuosi0 = aika0tm.tm_year+1+1900;
    nct_add_dim(&k, nct_range_NC_INT(vuosi0, vuosi0+vuosia, 1), vuosia, NC_INT, "vuosi");
    nct_copy_var(&k, latvar, 1);
    nct_copy_var(&k, lonvar, 1);
    nct_add_var(&k, pl.k[0], NC_FLOAT, "summer_start",   3, dimids);
    nct_add_var(&k, pl.k[1], NC_FLOAT, "summer_end",     3, dimids);
    nct_add_var(&k, pl.j[0], NC_FLOAT, "freezing_start", 3, dimids);
    nct_add_var(&k, pl.j[1], NC_FLOAT, "freezing_end",   3, dimids);
    nct_add_var(&k, pl.t[0], NC_FLOAT, "winter_start",   3, dimids);
    nct_add_var(&k, pl.t[1], NC_FLOAT, "winter_end",     3, dimids);
    nct_write_ncfile(&k, "kausien_päivät.nc");
    nct_free_vset(&k);

    free(maski);
    nct_free_vset(partly);
    nct_free_vset(frozen);
}

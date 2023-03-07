#include <nctietue3.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <err.h>
#include <assert.h>

#define kansio "ft_percent/"
#define talvi 3
#define jäätym 2
#define syksy jäätym
#define kesä 1

#ifdef Short
typedef short päi_tyy;
const char* nimi_ulos = "kausien_päivät_int16.nc";
const int nctyyppi = NC_SHORT;
#define täyttö 999
#else
typedef float päi_tyy;
const char* nimi_ulos = "kausien_päivät.nc";
const int nctyyppi = NC_FLOAT;
#define täyttö (0.0f/0.0f)
#endif

#define jäätyykö(froz, part) ((froz)*9+(part) >= 0.9)
//#define jäätyykö(froz, part) (froz >= 0.1)

const char* aika0str = "days since 2010-08-01";
struct tm aika0tm = {.tm_year=2010-1900, .tm_mon=8-1, .tm_mday=1};
struct tm aikatm_kesä = {.tm_year=2011-1900, .tm_mon=2-1, .tm_mday=1};
#define taitesekunteja 16
time_t taitesekunnit[2][taitesekunteja];
int kausimerkki = kesä;

int päiviä_taitteeseen(int t, int vuosi) {
    struct tm aika1tm = aika0tm;
    aika1tm.tm_mday += t;
    time_t t1 = mktime(&aika1tm);
    time_t t2 = taitesekunnit[0][vuosi];
    return (t2-t1) / 86400;
}

int t_alku_g; // t_alku sisään, yday ulos
int aikamuunnos(int t, int vuosi) {
   struct tm aika1tm = aika0tm;
   aika1tm.tm_mday += t-t_alku_g;
   time_t tnyt = mktime(&aika1tm);
   struct tm vuoden_alku = {
       .tm_year = vuosi + aika0tm.tm_year+1,
       .tm_mon  = 0,
       .tm_mday = 1,
   };
   time_t talku = mktime(&vuoden_alku);
   return (tnyt - talku) / 86400;
}

int talven_pituus(float* fr, float* pr, int aika0, int pit_xy, int t_pit, int vuosi) {
    kausimerkki = kesä;
    int ajan_huippu = päiviä_taitteeseen(aika0, vuosi+1);
    if(ajan_huippu <= 0)
	asm("int $3");
    if(ajan_huippu + aika0 > t_pit)
	ajan_huippu = t_pit - aika0;
    int pit = 0;
    for(int i=0; i<ajan_huippu; i++)
	if(fr[i*pit_xy] >= 0.9)
	    pit = i+1;
    if(pit < ajan_huippu)
	return pit;
    /* Jos vuoden taitteeseen asti oli talvea,
       tarkistetaan puoleen väliin asti kesän taitetta, onko talvi jatkuvaa
       ja katkaistaan heti ellei ole eli käsitellään sitä niin kuin kesää.
       Tällöin talvi saa vaihtua myös jäätymiskaudeksi, mikä yleensä ei ole mahdollista. */
    ajan_huippu += (taitesekunnit[1][vuosi+1] - taitesekunnit[0][vuosi+1]) / 86400 / 2;
    if(ajan_huippu + aika0 > t_pit)
	ajan_huippu = t_pit - aika0;
    for(int i=pit; i<ajan_huippu; i++)
	if(!jäätyykö(fr[i*pit_xy], pr[i*pit_xy]))
	    return i;
	else if(fr[i*pit_xy] < 0.9) {
	    kausimerkki = syksy;
	    return i; }
    kausimerkki = talvi;
    return pit;
}

/* Tapausta, jossa vuoden taitteessa on jäätymiskausi meneillään, ei ole käsitelty. */
int jäätym_pituus(float* fr, float* pr, int aika0, int pit_xy, int t_pit, int vuosi) {
    kausimerkki = talvi;
    int ajan_huippu = päiviä_taitteeseen(aika0, vuosi+1);
    assert(ajan_huippu > 0);
    if(ajan_huippu + aika0 > t_pit)
	ajan_huippu = t_pit - aika0;
    int pit = 0;
    for(int i=0; i<ajan_huippu; i++)
	if(fr[i*pit_xy] >= 0.9)
	    return i;
	else if(jäätyykö(fr[i*pit_xy], pr[i*pit_xy]))
	    pit = i+1;
    kausimerkki = kesä;
    assert(pit != ajan_huippu);
    return pit;
}

int kesän_pituus(float* fr, float* pr, int aika0, int pit_xy, int t_pit, int vuosi) {
    /* Tätä funktiota kutsutaan vain vuoden taitteesta. */
    int ajan_huippu = (taitesekunnit[1][vuosi] - taitesekunnit[0][vuosi]) / 86400;
    if(ajan_huippu + aika0 > t_pit)
	ajan_huippu = t_pit - aika0;
    int i=0;
    kausimerkki = kesä;
    for(; i<ajan_huippu; i++)
	if(fr[i*pit_xy] >= 0.9) {
	    kausimerkki = talvi;
	    return i; }
	else if(jäätyykö(fr[i*pit_xy], pr[i*pit_xy])) {
	    kausimerkki = syksy;
	    return i; }
    /* Tarkistettakoon vielä vuoden taitteeseen asti,
       ettei talvi ala kesän taitetta myöhemmin joskus keväällä. */
    ajan_huippu = i + (taitesekunnit[0][vuosi+1] - taitesekunnit[1][vuosi]) / 86400;
    if(ajan_huippu + aika0 > t_pit)
	ajan_huippu = t_pit - aika0;
    int i_alkup = i;
    for(; i<ajan_huippu; i++)
	if(fr[i*pit_xy] >= 0.9) {
	    kausimerkki = talvi;
	    return i; }
	else if(jäätyykö(fr[i*pit_xy], pr[i*pit_xy])) {
	    kausimerkki = syksy;
	    return i; }
    return i_alkup;
}

int pit_xy_g;
void vaihdepäivä(int v, int t, int p, päi_tyy* loppuva[2], päi_tyy* alkava[2]) {
    int yday = aikamuunnos(t, v);
    if(yday > 600) {
	asm("int $3");
	aikamuunnos(t, v);
    }
    loppuva[1][v*pit_xy_g+p] = yday;
    alkava[0][v*pit_xy_g+p] = yday;
}

void vaihdepäivä1(int v, int t, int p, päi_tyy* loppuva[2], päi_tyy* alkava[2]) {
    if(v > 0)
	loppuva[1][(v-1)*pit_xy_g+p] = aikamuunnos(t, v-1);
    alkava[0][v*pit_xy_g+p] = aikamuunnos(t, v);
}

struct päiväluvut {
    päi_tyy *k[2], *j[2], *t[2];
};

void alusta_päiväluvut(struct päiväluvut* pl, int pit_xy, int tpit) {
    int vuosia = tpit/366+1;
    for(int i=0; i<2; i++) {
	pl->k[i] = malloc(pit_xy*vuosia*sizeof(päi_tyy));
	pl->j[i] = malloc(pit_xy*vuosia*sizeof(päi_tyy));
	pl->t[i] = malloc(pit_xy*vuosia*sizeof(päi_tyy));
	assert(pl->k[i] && pl->j[i] && pl->t[i]);
	for(int j=0; j<vuosia*pit_xy; pl->k[i][j++]=täyttö);
	for(int j=0; j<vuosia*pit_xy; pl->j[i][j++]=täyttö);
	for(int j=0; j<vuosia*pit_xy; pl->t[i][j++]=täyttö);
    }
}

void alusta_taitesekunnit() {
    /* Kesän sekunti, johon asti tarkistetaan, tuleeko vielä jäätynyttä,
       ja siten onko talvi päättynyt. */
    struct tm aikatm = aika0tm;
    for(int i=0; i<taitesekunteja; i++) {
	taitesekunnit[0][i] = mktime(&aikatm);
	aikatm.tm_year++;
    }
    /* Jos kesä kestää monta vuotta,
       tällöin laitetaan yhden vuoden kesän pääte, ja seuraavan alku. */
    aikatm = aikatm_kesä;
    for(int i=0; i<taitesekunteja; i++) {
	taitesekunnit[1][i] = mktime(&aikatm);
	aikatm.tm_year++;
    }
}

int main(int argc, char** argv) {
    nct_readflags = nct_ratt;
    nct_set* partly = nct_read_mfnc_regex(kansio "^partly_frozen_percent_pixel_[0-9]*.nc$", 0, NULL);
    nct_set* frozen = nct_read_mfnc_regex(kansio "^frozen_percent_pixel_[0-9]*.nc$", 0, NULL);
    char* maski = nct_read_from_nc("aluemaski.nc", NULL);

    mktime(&aika0tm);
    mktime(&aikatm_kesä);
    /* convert_timeunits ainoastaan lisää tähän vakion eli siirtää alkuhetkeä,
       koska, ajan välimatka on jo päivä. */
    nct_var* aika = nct_convert_timeunits(nct_get_var(partly, "time"), aika0str);
    assert(aika);
    nct_convert_timeunits(nct_get_var(frozen, "time"), aika0str);
    const int t_alku = -((int*)aika->data)[0];
    t_alku_g = t_alku;
    int t_pit = (aika->len-t_alku)/365*365;

    const int pit_xy = nct_get_len_from(nct_firstvar(partly), 1);
    pit_xy_g = pit_xy;
    struct tm aika1tm = aika0tm;
    aika1tm.tm_mday += t_pit;
    char* kausi = malloc(t_pit*pit_xy);

    float* froz = nct_firstvar(frozen)->data;
    float* part = nct_firstvar(partly)->data;

    struct päiväluvut pl;
    alusta_päiväluvut(&pl, pit_xy, t_pit);

    alusta_taitesekunnit();

    for(int i=0; i<pit_xy; i++) {
	printf("%i/%i \r", i+1, pit_xy);
	fflush(stdout);
	if(!maski[i]) {
	    for(int t=0; t<t_pit; t++)
		kausi[t*pit_xy+i] = 0;
	    continue;
	}
	int t = t_alku;

	int vuosi = -1;

kesä_loppuun:
	int jäljellä = kesän_pituus(froz+t*pit_xy+i, part+t*pit_xy+i, t-t_alku, pit_xy, t_pit, vuosi+1);
	for(int tt=0; tt<jäljellä; tt++, t++)
	    kausi[(t-t_alku)*pit_xy+i] = kesä;
	if(t>=t_pit+t_alku)
	    goto aika_päättyi;
	/* Ensimmäinen päivä talvesta tai syksystä pitää laittaa jo täällä,
	 * koska muuten tämä kiertää loputtomasti ellei taitteessa ole kesä. */
	switch (kausimerkki) {
	    case talvi:
		vaihdepäivä1(++vuosi, t, i, pl.k, pl.t);
		kausi[(t++-t_alku)*pit_xy+i] = talvi;
		goto talvi_loppuun;
	    case syksy:
		vaihdepäivä1(++vuosi, t, i, pl.k, pl.j);
		kausi[(t++-t_alku)*pit_xy+i] = jäätym;
		goto jäätyminen_loppuun;
	    case kesä:
		vaihdepäivä1(++vuosi, t, i, pl.k, pl.k);
		kausi[(t++-t_alku)*pit_xy+i] = kesä;
		goto kesä_loppuun_keväällä;
	    default:
		asm("int $3");
	}

talvi_loppuun:
	jäljellä = talven_pituus(froz+t*pit_xy+i, part+t*pit_xy+i, t-t_alku, pit_xy, t_pit, vuosi);
	for(int tt=0; tt<jäljellä; tt++, t++)
	    kausi[(t-t_alku)*pit_xy+i] = talvi;
	if(t >= t_pit+t_alku)
	    goto aika_päättyi;
	switch(kausimerkki) {
	    case kesä:
		vaihdepäivä(vuosi, t, i, pl.t, pl.k);
		goto kesä_loppuun_keväällä;
	    case talvi:
		vaihdepäivä1(++vuosi, t, i, pl.t, pl.t);
		kausi[(t++-t_alku)*pit_xy+i] = talvi;
		goto talvi_loppuun;
	    case syksy:
		vaihdepäivä1(++vuosi, t, i, pl.t, pl.j);
		kausi[(t++-t_alku)*pit_xy+i] = syksy;
		goto jäätyminen_loppuun;
	}

jäätyminen_loppuun:
	jäljellä = jäätym_pituus(froz+t*pit_xy+i, part+t*pit_xy+i, t-t_alku, pit_xy, t_pit, vuosi);
	for(int tt=0; tt<jäljellä; tt++, t++)
	    kausi[(t-t_alku)*pit_xy+i] = jäätym;
	if(t >= t_pit+t_alku)
	    goto aika_päättyi;
	switch(kausimerkki) {
	    case talvi:
		vaihdepäivä(vuosi, t, i, pl.j, pl.t);
		goto talvi_loppuun;
	    case kesä:
		vaihdepäivä(vuosi, t, i, pl.j, pl.k);
		goto kesä_loppuun_keväällä;
	    default:
		assert(0);
	}

/* Toisin kuin kohdassa kesä_loppuun tässä mikään ei laukaise jäätymiskautta tai talvea. */
kesä_loppuun_keväällä:
	jäljellä = päiviä_taitteeseen(t-t_alku, vuosi+1);
	assert(jäljellä > 0);
        if(t+jäljellä > t_pit+t_alku)
	    jäljellä = t_pit+t_alku-t;
	for(int tt=0; tt<jäljellä; tt++, t++)
	    kausi[(t-t_alku)*pit_xy+i] = kesä;
	goto kesä_loppuun;

aika_päättyi:;
    }
    printf("\033[K");

    nct_var* latvar = nct_get_var(partly, "lat");
    nct_var* lonvar = nct_get_var(partly, "lon");
    int dimids[] = {0,1,2};

    nct_set k = {0};
    nct_var* var = nct_dim2coord(nct_add_dim(&k, t_pit, "time"), NULL, NC_INT);
    nct_put_interval(var, 0, 1);
    nct_add_varatt_text(var, "units", (char*)aika0str, 0);
    nct_copy_var(&k, latvar, 1);
    nct_copy_var(&k, lonvar, 1);
    nct_add_var(&k, kausi, NC_BYTE, "kausi", 3, dimids);
    nct_write_nc(&k, "kaudet1.nc");
    nct_free1(&k);

    k = (nct_set){0};
    int vuosia = t_pit/366+1;
    int vuosi0 = aika0tm.tm_year+1+1900;
    var = nct_dim2coord(nct_add_dim(&k, vuosia, "vuosi"), NULL, NC_INT);
    nct_put_interval(var, vuosi0, 1);
    nct_copy_var(&k, latvar, 1);
    nct_copy_var(&k, lonvar, 1);
    nct_add_var(&k, pl.k[0], nctyyppi, "summer_start",   3, dimids);
    nct_add_var(&k, pl.k[1], nctyyppi, "summer_end",     3, dimids);
    nct_add_var(&k, pl.j[0], nctyyppi, "freezing_start", 3, dimids);
    nct_add_var(&k, pl.j[1], nctyyppi, "freezing_end",   3, dimids);
    nct_add_var(&k, pl.t[0], nctyyppi, "winter_start",   3, dimids);
    nct_add_var(&k, pl.t[1], nctyyppi, "winter_end",     3, dimids);
    nct_write_nc(&k, nimi_ulos);

    free(maski);
    nct_free(&k, partly, frozen);
}

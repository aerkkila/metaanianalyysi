#include <nctietue3.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <err.h>
#include <assert.h>
#include <sys/stat.h>

#define kansio "ft_percent/"
#define talvi 3
#define jäätym 2
#define syksy jäätym
#define kesä 1
#define epäkausi 0

/* Tarvitaan vain debug-käyttöön. Päivästä pitää vähentää t_alku. */
void laita_päivä(int);

/* kopioitu muualta */
static struct alue_t {
    float lat0, lon0;
    int latpit, lonpit;
    float väli;
} alue = {
    .lat0 = 29,
    .lon0 = -180,
    .latpit = 55,
    .lonpit = 360,
    .väli = 1,
};

#define täyttö 999
typedef float päi_tyy;
const char* nimi_ulos = "kausien_päivät.nc";
const int nctyyppi = NC_FLOAT;

const char* ulosdir = ".";
const char* ulosdir16 = ".";
#define AA
#if defined AA
#define kelpaako(a, b) ((a)==(a))
#define jäätyykö(lA, lB) ((lA) + 9*(lB) >= 0.9) // && (lA)==(lA))
#define talveako(lA, lB) ((lB) >= 0.9) // && (lA)==(lA))
const char menetelmä_sy[] = "partly + 9*frozen >= 0.9";
const char menetelmä_ta[] = "frozen >= 0.9";
const char* tunniste = "";
const char* luettavaA = kansio "^partly_frozen_percent_pixel_[0-9]*.nc$";
const char* luettavaB = kansio "^frozen_percent_pixel_[0-9]*.nc$";
#else
virhe;
#endif

/* Näitten kahden rivin pitää kuvata samaa päivää. Katsokaani myös kohta ajan_selitys.
   aika0str on se, mistä tuloksen aikasarja alkaa ja pitää olla myöhäisempi kuin syötteen aikasarjan alku.
   Kesän taite on seuraavan vuoden puolella. Ei missään tapauksessa ennen aika0str-aikaa. */
const char* aika0str = "days since 2010-08-01";
struct tm aika0tm = {.tm_year=2010-1900, .tm_mon=8-1, .tm_mday=1};
struct tm aikatm_kesä = {.tm_year=2011-1900, .tm_mon=2-1, .tm_mday=1};
#define taitesekunteja 46
time_t taitesekunnit[2][taitesekunteja];
int kausimerkki = kesä;
int t_alku_g;

/* debug */
/* Pääfunktion muuttujan t päivämäärän löytämiseksi oikea kutsu on laita_päivä(t-t_alku) */
void laita_päivä(int t) {
    struct tm tm = aika0tm;
    tm.tm_mday += t;
    mktime(&tm);
    printf("%i-%i-%i\n", tm.tm_year+1900, tm.tm_mon+1, tm.tm_mday);
}

int päiviä_taitteeseen(int t, int vuosi) {
    struct tm aika1tm = aika0tm;
    aika1tm.tm_mday += t - t_alku_g;
    time_t t1 = mktime(&aika1tm);
    time_t t2 = taitesekunnit[0][vuosi];
    return (t2-t1) / 86400;
}

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

int talven_pituus(float* lA, float* lB, int tnyt, int pit_xy, int t_loppu, int vuosi) {
    kausimerkki = kesä;
    int ajan_huippu = päiviä_taitteeseen(tnyt, vuosi+1);
    if (ajan_huippu < 0)
	asm("int $3");
    if (ajan_huippu + tnyt > t_loppu)
	ajan_huippu = t_loppu - tnyt;
    int pit = 0;
    for(int i=0; i<ajan_huippu; i++)
	if talveako(lA[i*pit_xy], lB[i*pit_xy])
	    pit = i+1;
    if (pit < ajan_huippu)
	return pit;
    /* Jos vuoden taitteeseen (elokuun alku) asti oli talvea,
       tarkistetaan puoleen väliin asti kesän taitetta (helmikuun alku), onko talvi jatkuvaa
       ja katkaistaan heti ellei ole eli käsitellään sitä niin kuin kesää.
       Tällöin talvi saa vaihtua myös jäätymiskaudeksi, mikä yleensä ei ole mahdollista. */
    ajan_huippu += (taitesekunnit[1][vuosi+1] - taitesekunnit[0][vuosi+1]) / 86400 / 2;
    if (ajan_huippu + tnyt > t_loppu)
	ajan_huippu = t_loppu - tnyt;
    for(int i=pit; i<ajan_huippu; i++)
	/* Talvi tarkistetaan ensin, koska talvi täytää myös jäätymiskauden ehdon. */
	if (!talveako(lA[i*pit_xy], lB[i*pit_xy])) {
	    kausimerkki = syksy;
	    return i; }
	else if (!jäätyykö(lA[i*pit_xy], lB[i*pit_xy]))
	    return i;
    kausimerkki = talvi;
    return pit;
}

int jäätym_pituus(float* lA, float* lB, int tnyt, int pit_xy, int t_loppu, int vuosi) {
    kausimerkki = talvi;
    int ajan_huippu = päiviä_taitteeseen(tnyt, vuosi+1);
    if (ajan_huippu <= 0)
	errx(1, "ajan_huippu = %i, vuosi = %i, t_loppu = %i, tnyt = %i",
		ajan_huippu, vuosi, t_loppu, tnyt);
    if (ajan_huippu + tnyt > t_loppu)
	ajan_huippu = t_loppu - tnyt;
    int pit = 0;
    for(int i=0; i<ajan_huippu; i++)
	if talveako(lA[i*pit_xy], lB[i*pit_xy])
	    return i;
	else if (jäätyykö(lA[i*pit_xy], lB[i*pit_xy]))
	    pit = i+1;
    /* Ellei löytynyt, on syytä epäillä epälukuja. */
    if (!kelpaako(lA[(ajan_huippu-1)*pit_xy], lB[(ajan_huippu-1)*pit_xy])) {
	kausimerkki = epäkausi;
	return ajan_huippu; }
    int ind = (ajan_huippu-1)*pit_xy;
    kausimerkki = jäätyykö(lA[ind], lB[ind]) ? syksy : kesä;
    return pit;
}

int ohi_vuoden_taitteesta = 0;
/* Jos tätä funktiota ei kutsuta vuoden taitteesta (taitesekunnit[0][vuosi]),
   eli jos ei-kesä päättyy vasta elokuussa,
   täytyy asettaa globaali muuttuja ohi_vuoden_taitteesta ennen tämän funktion kutsua.
   Kyseinen muuttuja kertoo montako päivää vuoden taite on ohitettu.
   Ajan huippu on yksikössä aika-askelia tästä hetkestä.
   Siihen asetetaan ensin se päivä, jolloin monivuotinen kesä katkaistaan. */
int kesän_pituus(float* lA, float* lB, int tnyt, int pit_xy, int t_loppu, int vuosi) {
    int ajan_huippu = (taitesekunnit[1][vuosi] - taitesekunnit[0][vuosi] - ohi_vuoden_taitteesta) / 86400;
    ohi_vuoden_taitteesta = 0;
    if (ajan_huippu + tnyt > t_loppu)
	ajan_huippu = t_loppu - tnyt;
    int i=0;
    kausimerkki = kesä;
    for(; i<ajan_huippu; i++)
	if talveako(lA[i*pit_xy], lB[i*pit_xy]) {
	    kausimerkki = talvi;
	    return i; }
	else if (jäätyykö(lA[i*pit_xy], lB[i*pit_xy])) {
	    kausimerkki = syksy;
	    return i; }
    /* Ellei löytynyt, on syytä epäillä epälukuja. */
    if (!kelpaako(lA[(i-1)*pit_xy], lB[(i-1)*pit_xy])) {
	kausimerkki = epäkausi;
	return i; }
    /* Tarkistettakoon vielä vuoden taitteeseen asti,
       ettei talvi ala kesän taitetta myöhemmin joskus keväällä. */
    ajan_huippu = i + (taitesekunnit[0][vuosi+1] - taitesekunnit[1][vuosi]) / 86400;
    if (ajan_huippu + tnyt > t_loppu)
	ajan_huippu = t_loppu - tnyt;
    int i_alkup = i;
    for(; i<ajan_huippu; i++)
	if talveako(lA[i*pit_xy], lB[i*pit_xy]) {
	    kausimerkki = talvi;
	    return i; }
	else if (jäätyykö(lA[i*pit_xy], lB[i*pit_xy])) {
	    kausimerkki = syksy;
	    return i; }
    /* Ellei löytynyt, on syytä epäillä epälukuja. */
    if (!kelpaako(lA[(i-1)*pit_xy], lB[(i-1)*pit_xy])) {
	kausimerkki = epäkausi;
	return i; }
    return i_alkup;
}

int pit_xy_g, vuosia_g;

#ifdef TRANSPOOSI
#define pl_ind(p,v) ((p)*vuosia_g+(v))
#else
#define pl_ind(p,v) ((v)*pit_xy_g+(p))
#endif
void vaihdepäivä(int v, int t, int p, päi_tyy* loppuva[2], päi_tyy* alkava[2]) {
    int yday = aikamuunnos(t, v);
    if(yday > 600) {
	asm("int $3");
	aikamuunnos(t, v);
    }
    loppuva[1][pl_ind(p,v)] = yday;
    alkava[0][pl_ind(p,v)] = yday;
}

void vaihdepäivä1(int v, int t, int p, päi_tyy* loppuva[2], päi_tyy* alkava[2]) {
    if(v > 0)
	loppuva[1][pl_ind(p,v-1)] = aikamuunnos(t, v-1);
    alkava[0][pl_ind(p,v)] = aikamuunnos(t, v);
}

struct päiväluvut {
    päi_tyy *k[2], *j[2], *t[2];
};

void alusta_päiväluvut(struct päiväluvut* pl, int pit_xy, int tpit) {
    int vuosia = tpit/366+1;
    vuosia_g = vuosia;
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
    if (mkdir(ulosdir, 0755) && errno != EEXIST)
	err(1, "mkdir %s", ulosdir);
    if (mkdir(ulosdir16, 0755) && errno != EEXIST)
	err(1, "mkdir %s", ulosdir16);
    nct_readflags = nct_ratt;
    nct_set* luokkaA = nct_read_mfnc_regex(luettavaA, 0, NULL);
    nct_set* luokkaB = NULL;
    if (luettavaB)
	luokkaB = nct_read_mfnc_regex(luettavaB, 0, NULL);

    char* maski = nct_read_from_nc("aluemaski.nc", NULL);

    mktime(&aika0tm);
    mktime(&aikatm_kesä);
    /* convert_timeunits ainoastaan lisää tähän vakion eli siirtää alkuhetkeä,
       koska, ajan välimatka on jo päivä. */
    nct_var* aika = nct_convert_timeunits(nct_get_var(luokkaA, "time"), aika0str);
    assert(aika);
    /* ajan_selitys:
       Nyt kun yllä tehtiin convert_timeunits,
       aika->data[0] kuvaa montako päivää aika0str-hetkestä on aikasarjan alkuun.
       ** aika0str on oltava myöhempi kuin aikasarjan alku, **
       koska luenta aloitetaan aika0str-hetkestä.
       Kaikka t_$jotain-muuttujat ovat aika->data:n yksiköitä eli kulunutta koko aikasarjan alusta.
       Ei siis että montako aika-askelta on kulunut t_alku-hetkestä. */
    const int t_alku = -nct_get_integer(aika, 0); // aika->data[0] on negatiivinen, koska aiempi kuin aika0str
    assert (t_alku >= 0);
    t_alku_g = t_alku;
    int t_loppu = (aika->len-t_alku)/365*365 + t_alku; // lopetettaessa vuosia on kulunut suurinpiirtein kokonaisluku alkuhetkestä
    assert (t_loppu <= aika->len);

    const int pit_xy = nct_get_len_from(nct_firstvar(luokkaA), 1);
    pit_xy_g = pit_xy;
    struct tm aika1tm = aika0tm;
    aika1tm.tm_mday += t_loppu;

    float* lA = nct_firstvar(luokkaA)->data;
    float* lB = NULL;
    if (luokkaB)
	lB = nct_firstvar(luokkaB)->data;

    struct päiväluvut pl;
    alusta_päiväluvut(&pl, pit_xy, t_loppu-t_alku);

    alusta_taitesekunnit();

    for(int i=0; i<pit_xy; i++) {
	printf("%i/%i \r", i+1, pit_xy);
	fflush(stdout);
	if (!maski[i])
	    continue;
	int t = t_alku;

	int vuosi = -1;

kesä_loppuun:
	int jäljellä = kesän_pituus(lA+t*pit_xy+i, lB+t*pit_xy+i, t, pit_xy, t_loppu, vuosi+1);
	t += jäljellä;
	if (t >= t_loppu)
	    goto aika_päättyi;
	/* Ensimmäinen päivä talvesta tai syksystä pitää laittaa jo täällä,
	 * koska muuten tämä kiertää loputtomasti ellei taitteessa ole kesä. */
	switch (kausimerkki) {
	    case talvi:
		vaihdepäivä1(++vuosi, t, i, pl.k, pl.t);
		t++;
		goto talvi_loppuun;
	    case syksy:
		vaihdepäivä1(++vuosi, t, i, pl.k, pl.j);
		t++;
		goto jäätyminen_loppuun;
	    case kesä:
		vaihdepäivä1(++vuosi, t, i, pl.k, pl.k);
		t++;
		goto kesä_loppuun_keväällä;
	    case epäkausi:
		goto aika_päättyi;
	    default:
		__builtin_unreachable();
	}

talvi_loppuun:
	jäljellä = talven_pituus(lA+t*pit_xy+i, lB+t*pit_xy+i, t, pit_xy, t_loppu, vuosi);
	t += jäljellä;
	if (t >= t_loppu)
	    goto aika_päättyi;
	switch(kausimerkki) {
	    case kesä:
		vaihdepäivä(vuosi, t, i, pl.t, pl.k);
		goto kesä_loppuun_keväällä;
	    case talvi:
		vaihdepäivä1(++vuosi, t, i, pl.t, pl.t);
		t++;
		goto talvi_loppuun;
	    case syksy:
		vaihdepäivä1(++vuosi, t, i, pl.t, pl.j);
		t++;
		goto jäätyminen_loppuun;
	}

jäätyminen_loppuun:
	jäljellä = jäätym_pituus(lA+t*pit_xy+i, lB+t*pit_xy+i, t, pit_xy, t_loppu, vuosi);
	t += jäljellä;
	if (t >= t_loppu)
	    goto aika_päättyi;
	switch(kausimerkki) {
	    case talvi:
		vaihdepäivä(vuosi, t, i, pl.j, pl.t);
		goto talvi_loppuun;
	    case kesä:
		vaihdepäivä(vuosi, t, i, pl.j, pl.k);
		goto kesä_loppuun_keväällä;
	    case syksy:
		vaihdepäivä(++vuosi, t, i, pl.j, pl.j);
		t++;
		goto jäätyminen_loppuun;
	    case epäkausi:
		goto aika_päättyi;
	    default:
		__builtin_unreachable();
	}

/* Toisin kuin kohdassa kesä_loppuun tässä mikään ei laukaise jäätymiskautta tai talvea. */
kesä_loppuun_keväällä:
	jäljellä = päiviä_taitteeseen(t, vuosi+1);
	if (jäljellä < 0) { // talvi tai syksy oli kestänyt elokuuhun asti
	    ohi_vuoden_taitteesta = -jäljellä;
	    goto kesä_loppuun; }
        if (t+jäljellä > t_loppu)
	    jäljellä = t_loppu-t;
	t += jäljellä;
	goto kesä_loppuun;

aika_päättyi:;
    }
    printf("\033[K");

    nct_set k = {0};
    int vuosia = (t_loppu-t_alku)/366+1;
    int vuosi0 = aika0tm.tm_year+1+1900;
#ifndef TRANSPOOSI
    nct_put_interval(nct_dim2coord(nct_add_dim(&k, vuosia, "vuosi"), NULL, NC_INT), vuosi0, 1);
#endif
    nct_put_interval(nct_dim2coord(nct_add_dim(&k, alue.latpit, "lat"), NULL, NC_FLOAT), alue.lat0, alue.väli);
    nct_put_interval(nct_dim2coord(nct_add_dim(&k, alue.lonpit, "lon"), NULL, NC_FLOAT), alue.lon0, alue.väli);
#ifdef TRANSPOOSI
    nct_put_interval(nct_dim2coord(nct_add_dim(&k, vuosia, "vuosi"), NULL, NC_INT), vuosi0, 1);
#endif
    int dimids[] = {0,1,2};
    nct_add_var(&k, pl.k[0], nctyyppi, "summer_start",   3, dimids);
    nct_add_var(&k, pl.k[1], nctyyppi, "summer_end",     3, dimids);
    nct_add_var(&k, pl.j[0], nctyyppi, "freezing_start", 3, dimids);
    nct_add_var(&k, pl.j[1], nctyyppi, "freezing_end",   3, dimids);
    nct_add_var(&k, pl.t[0], nctyyppi, "winter_start",   3, dimids);
    nct_add_var(&k, pl.t[1], nctyyppi, "winter_end",     3, dimids);
    char nimi[80];

    int ncid, varid;
    /* int16 */
    nct_set k1 = {0};
    nct_put_interval(nct_dim2coord(nct_add_dim(&k1, vuosia, "vuosi"), NULL, NC_INT), vuosi0, 1);
    nct_put_interval(nct_dim2coord(nct_add_dim(&k1, alue.latpit, "lat"), NULL, NC_FLOAT), alue.lat0, alue.väli);
    nct_put_interval(nct_dim2coord(nct_add_dim(&k1, alue.lonpit, "lon"), NULL, NC_FLOAT), alue.lon0, alue.väli);
    sprintf(nimi, "%s/kausien_päivät%s_int16.nc", ulosdir16, tunniste);
    ncid = nct_create_nc(&k1, nimi);

    int len = nct_firstvar(&k)->len;
    short* buff = malloc(len*sizeof(short));
    nct_foreach(&k, var) {
	float* data = var->data;
	for(int i=0; i<len; i++) {
	    buff[i] = data[i];
	    if (data[i] == täyttö)
		data[i] = 0.0/0.0f; // nan-arvo vasta nyt, ettei niitä tarvi käsitellä koodissa
	}
	int varid;
	ncfunk(nc_def_var, ncid, var->name, NC_SHORT, 3, dimids, &varid);
	nc_put_var(ncid, varid, buff);
    }
    nc_inq_varid(ncid, "freezing_start", &varid);
    nc_put_att_text(ncid, varid, "menetelmä", sizeof(menetelmä_sy), menetelmä_sy);
    nc_inq_varid(ncid, "winter_start", &varid);
    nc_put_att_text(ncid, varid, "menetelmä", sizeof(menetelmä_ta), menetelmä_ta);
    ncfunk(nc_close, ncid);
    free(buff);

    sprintf(nimi, "%s/kausien_päivät%s.nc", ulosdir, tunniste);
    ncid = nct_create_nc(&k, nimi); // luodaan vasta täällä, jotta nan-muunnos tulee voimaan silmukasta
    nc_inq_varid(ncid, "freezing_start", &varid);
    nc_put_att_text(ncid, varid, "menetelmä", sizeof(menetelmä_sy), menetelmä_sy);
    nc_inq_varid(ncid, "winter_start", &varid);
    nc_put_att_text(ncid, varid, "menetelmä", sizeof(menetelmä_ta), menetelmä_ta);
    nc_close(ncid);
    
    free(maski);
    nct_free(&k, &k1, luokkaA);
}

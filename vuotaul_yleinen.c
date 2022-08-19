#include <nctietue2.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdarg.h>
#include <time.h>

/* Kääntäjä tarvitsee argumentit `pkg-config --libs nctietue2` -lm
   nctietue2-kirjasto on osoitteessa https://github.com/aerkkila/nctietue2.git
   Jos kääntäminen ei onnistu, päivitettäköön gcc uudempaan versioon
   tai vaihdettakoon muuttujien nimet ascii-merkeiksi, kun nyt siellä on utf-8:a. */

const double r2 = 6371229.0*6371229.0;
#define PINTAALA(lat, hila) ((hila) * r2 * (sin((lat)+0.5*(hila)) - sin((lat)-0.5*(hila))))
#define ASTE 0.017453293

#define ARRPIT(a) sizeof(a)/sizeof(*(a))
#define MIN(a,b) (a)<(b)? (a): (b)
const char* ikirnimet[]      = {"non_permafrost", "sporadic", "discontinuous", "continuous"};
const char* köppnimet[]      = {"D.b", "D.c", "D.d", "ET"};
const char* wetlnimet[]      = {"wetland", "bog", "fen", "marsh", "permafrost_bog", "tundra_wetland"};
const char* kaudet[]         = {"whole_year", "summer", "freezing", "winter"};
enum                           {whole_year_e, summer_e, freezing_e, winter_e};
const char* pripost_sisaan[] = {"flux_bio_prior", "flux_bio_posterior"};
const char* pripost_ulos[]   = {"pri", "post"};
const int resol = 19800;
#define kausia 4
enum luokitus_e {kopp_e, ikir_e, wetl_e} luokenum;
int ppnum;

float *restrict vuoptr, *restrict lat;
char *restrict luok_c;
double *restrict alat;
nct_vset *luok_vs;
int latpit, ikirvuosi0, ikirvuosia, aikapit, vuosia;
struct tm tm0;

int argumentit(int argc, char** argv) {
    if(argc < 3) {
	printf("Käyttö: %s luokitus:köpp/ikir/wetl pri/post\n", argv[0]);
	return 1;
    }
    if(!strcmp(argv[1], "köpp"))
	luokenum = kopp_e;
    else if (!strcmp(argv[1], "ikir"))
	luokenum = ikir_e;
    else if (!strcmp(argv[1], "wetl"))
	luokenum = wetl_e;
    else {
	printf("Ei luettu luokitusargumenttia\n");
	return 1;
    }
    if(!strcmp(argv[2], "pri"))
	ppnum = 0;
    else if(!strcmp(argv[2], "post"))
	ppnum = 1;
    else {
	printf("Ei luettu pri/post-argumenttia\n");
	return 1;
    }
    return 0;
}

void* lue_kopp() {
    char* luok = malloc(resol);
    int pit;
    FILE* f = fopen("./köppenmaski.txt", "r");
    if(!f) return NULL;
    if((pit=fread(luok, 1, resol, f))!=resol)
	printf("Luettiin %i eikä %i\n", pit, resol);
    for(int i=0; i<resol; i++)
	luok[i] -= '0'+1; // '1' -> 0 jne.
    return (luok_c = luok);
}
void* lue_ikir() {
    nct_vset *vset = nct_read_ncfile("./ikirdata.nc");
    int varid = nct_get_varid(vset, "luokka");
    char* ret = vset->vars[varid]->data;
    vset->vars[varid]->nonfreeable_data = 1;
    nct_var* var = &NCTVAR(*vset, "vuosi");
    ikirvuosi0 = ((short*)var->data)[0]; // nouseva tavujärjestys, joten short toimii myös int-datalle
    ikirvuosia = nct_get_varlen(var);
    nct_free_vset(vset);
    return (luok_c = ret);
}
void* lue_wetl() {
    return (luok_vs = nct_read_ncfile("./BAWLD1x1.nc"));
}
void* lue_luokitus() {
    static void* (*funktio[])(void) = { [kopp_e]=lue_kopp, [ikir_e]=lue_ikir, [wetl_e]=lue_wetl, };
    return funktio[luokenum]();
}

struct laskenta {
    char* kausiptr;
    double *ainemäärä, *ainemäärä1, *ala_ja_aika, *ala_ja_aika1;
    int kuluva_kausi, kuluva_vuosi, lajinum;
};

void alusta_lasku(struct laskenta* args) {
    args->kuluva_kausi = freezing_e;
    args->kuluva_vuosi = 0;
    memset(args->ainemäärä1, 0, kausia*8);
    memset(args->ala_ja_aika1, 0, kausia*8);
}

void hyväksy_data(struct laskenta* args) {
    for(int k=0; k<kausia; k++) {
	args->ainemäärä   [k] += args->ainemäärä1[k];
	args->ala_ja_aika [k] += args->ala_ja_aika1[k];
	args->ainemäärä1[k]=args->ala_ja_aika1[k] = 0;
    }
}

/* Muilla kuin ikiroutaluokilla vuodata huomioidaan vain,
   jos hilaruudussa on ollut kaikki kaudet kaikkina vuosina. */
int tarkista_kausi(struct laskenta* args, int ind_t) {
    if(args->kausiptr[ind_t] == args->kuluva_kausi)
	return 1; // samaa kautta
    if((args->kuluva_kausi=args->kausiptr[ind_t]) != freezing_e)
	return 2; // kausi vaihtui
    if(++args->kuluva_vuosi != vuosia)
	return 3; // vuosi vaihtui
    return 0;     // vuosien määrä tuli täyteen
}

void laske_köpp(struct laskenta* args) {
    char* kausiptr = args->kausiptr;
    for(int r=0; r<resol; r++) {
	if(luok_c[r] != args->lajinum) continue;
	double ala = alat[r/360];
	int t;
	for(t=0; t<aikapit; t++)
	    if(kausiptr[t*resol + r] == freezing_e) break;
	alusta_lasku(args);
	for(; t<aikapit; t++) {
	    int ind_t = t*resol + r;
	    if(!tarkista_kausi(args, ind_t)) break;
	    double vuo1 = vuoptr[ind_t] * ala;
	    args->ainemäärä1  [(int)kausiptr[ind_t]] += vuo1; // *86400 kerrotaan lopussa: mol/s * s -> mol
	    args->ala_ja_aika1[(int)kausiptr[ind_t]] += ala;  // *86400 kerrotaan lopussa: m²*d -> m²*s
	    args->ainemäärä1  [0]                    += vuo1;
	    args->ala_ja_aika1[0]                    += ala;
	}
	hyväksy_data(args);
    }
}

/* Tämä kävi yllätävän monimutkaiseksi ollen ainoa ajasta riippuva luokitus.
   Jos ikiroutaluokka vaihtuu, aloitettu kausisto (syksy,talvi,kesä) käydään kuitenkin loppuun samana ikiroutaluokkana.
   Muissa luokituksissa pistettä ei huomioitaisi, jos kausia on eri määrä kuin vuosia.
   Tässä kuitenkin huomioidaan, jos puute aiheutuu ikiroutaluokan muutoksesta eikä sulamisdatan puutteesta.
*/
void laske_ikir(struct laskenta* args) {
    char* kausiptr = args->kausiptr;
    for(int r=0; r<resol; r++) {
	/* Optimoinnin vuoksi tarkistetaan, onko tämä piste milloinkaan oikeaa ikiroutaluokkaa. */
	for(int v=0; v<ikirvuosia; v++)
	    if(luok_c[v*resol+r] == args->lajinum)
		goto piste_kelpaa2;
	continue;
    piste_kelpaa2:

	double ala = alat[r/360];
	int t;
	for(t=0; t<aikapit; t++)
	    if(kausiptr[t*resol + r] == freezing_e) break;
	alusta_lasku(args);

	/* Tarkistetaan, huomioidaanko tämä piste sulamisdatan puolesta. */
	for(int t_=t; t_<aikapit; t_++)
	    if(!tarkista_kausi(args, t_*resol+r))
		goto piste_kelpaa1;
	continue;
    piste_kelpaa1:
	alusta_lasku(args);

	struct tm tma = tm0; // Tällä tarkistetaan, minkä vuoden ikiroutadataa käytetään.
	tma.tm_mday += t;
	int lukitse_ikirvuosi = 0;
	int lukitse_data = 0;
	for(; t<aikapit; t++, tma.tm_mday++) {
	    int ind_v, ind_t = t*resol + r;
	    int apu = tarkista_kausi(args, ind_t);
	    if(!apu) { // vuosi vaihtui ja määrä täyttyi
		if(lukitse_data) args->kuluva_vuosi--; // tätä oli muutettu, joten palautetaan
		break;
	    }
	    if(apu==3) { // vuosi vaihtui
		if(lukitse_data) args->kuluva_vuosi--;
		lukitse_ikirvuosi = 0;
	    }

	    if(!lukitse_ikirvuosi) {
		mktime(&tma);
		int v = tma.tm_year+1900-ikirvuosi0;
		if(v == ikirvuosia)
		    v = ikirvuosia-1; // Käytetään viimeistä vuotta, kun ikiroutadata loppuu kesken.
		ind_v = v*resol + r;
		lukitse_ikirvuosi = 1;
	    }
	    if(luok_c[ind_v] != args->lajinum) {
		lukitse_data = 1;
		continue;
	    }
	    lukitse_data = 0;

	    double vuo1 = vuoptr[ind_t] * ala;
	    args->ainemäärä1  [(int)kausiptr[ind_t]] += vuo1; // *86400 kerrotaan lopussa: mol/s * s -> mol
	    args->ala_ja_aika1[(int)kausiptr[ind_t]] += ala;  // *86400 kerrotaan lopussa: m²*d -> m²*s
	    args->ainemäärä1  [0]                    += vuo1;
	    args->ala_ja_aika1[0]                    += ala;
	}
	if(!args->kuluva_vuosi)
	    continue;
	double kerroin = (double)vuosia / args->kuluva_vuosi;
	for(int k=0; k<kausia; k++) {
	    args->ainemäärä1  [k] *= kerroin;
	    args->ala_ja_aika1[k] *= kerroin;
	}
	hyväksy_data(args);
    }
}

void laske_wetland(struct laskenta* args) {
    char* kausiptr = args->kausiptr;
    double* osuus0ptr = NCTVAR(*luok_vs, "wetland").data;
    double* osuus1ptr = NCTVAR(*luok_vs, wetlnimet[args->lajinum]).data;
    for(int r=0; r<resol; r++) {
	double ala = alat[r/360];
	if(!kausiptr[r])        continue;
	if(osuus0ptr[r] < 0.05) continue;

	int t;
	for(t=0; t<aikapit; t++)
	    if(kausiptr[t*resol + r] == freezing_e) break;
	alusta_lasku(args);

	for(; t<aikapit; t++) {
	    int ind_t = t*resol + r;
	    if(!tarkista_kausi(args, ind_t)) break;
	    double ala1 = osuus1ptr[r] * ala;
	    double vuo1 = vuoptr[ind_t] * ala1 / osuus0ptr[r]; // pinta-ala on osuutena wetlandista
	    args->ainemäärä1  [(int)kausiptr[ind_t]] += vuo1;  // *86400 kerrotaan lopussa: mol/s * s -> mol
	    args->ala_ja_aika1[(int)kausiptr[ind_t]] += ala1;  // *86400 kerrotaan lopussa: m²*d -> m²*s
	    args->ainemäärä1  [0]                    += vuo1;
	    args->ala_ja_aika1[0]                    += ala1;
	}
	hyväksy_data(args);
    }
}

char aprintapu[256];
char* aprintf(const char* muoto, ...) {
    va_list args;
    va_start(args, muoto);
    vsprintf(aprintapu, muoto, args);
    va_end(args);
    return aprintapu;
}

int main(int argc, char** argv) {
    if(argumentit(argc, argv))
	return 1;
    nct_vset vuo;
    nct_var* apuvar;
    FILE* ulos[kausia];
    const char** luoknimet[]    = { [kopp_e]=köppnimet, [ikir_e]=ikirnimet, [wetl_e]=wetlnimet, };
    const char* luokitus_ulos[] = { [kopp_e]="köppen",  [ikir_e]="ikir",    [wetl_e]="wetland", };
    int luokkia = ( luokenum==kopp_e? ARRPIT(köppnimet):
		    luokenum==ikir_e? ARRPIT(ikirnimet):
		    luokenum==wetl_e? ARRPIT(wetlnimet):
		    -1 );

    nct_read_ncfile_gd0(&vuo, "./flux1x1.nc");
    if(!lue_luokitus()) {
	printf("Luokitusta ei luettu\n");
	return 1;
    }

    apuvar = &NCTVAR(vuo, pripost_sisaan[ppnum]);
    if(apuvar->xtype != NC_FLOAT) {
	printf("Vuodatan tyyppi ei täsmää koodissa ja datassa.\n");
	return 1;
    }
    vuoptr  = apuvar->data;

    int res = NCTVARDIM(*apuvar,2).len;
    latpit = NCTVARDIM(*apuvar,1).len;
    if(res*latpit != resol) {
	puts("Virheellinen resoluutio");
	return 1;
    }
    lat = NCTVAR(vuo, "lat").data;
    double _alat[latpit];
    alat = _alat;
    for(int i=0; i<latpit; i++)
	alat[i] = PINTAALA(ASTE*lat[i], ASTE);

    for(int ftnum=1; ftnum<3; ftnum++) {
	nct_vset kausivset;
	nct_read_ncfile_gd0(&kausivset, aprintf("./kaudet%i.nc", ftnum));

	apuvar = &NCTVAR(kausivset, "kausi");
	if(apuvar->xtype != NC_BYTE && apuvar->xtype != NC_UBYTE) {
	    printf("Kausidatan tyyppi ei täsmää koodissa ja datassa.\n");
	    return 1;
	}
	char* kausiptr = apuvar->data;

	struct tm tm1;
	time_t t0, t1;
	tm0 = (struct tm){.tm_year=2011-1900, .tm_mon=8-1, .tm_mday=15};
	t0 = mktime(&tm0);
	t1 = nct_mktime(&NCTVAR(kausivset, "time"), &tm1, 0).a.t;
	int k_alku = (t0-t1) / 86400;
	t1 = nct_mktime(&NCTVAR(vuo, "time"), &tm1, 0).a.t;
	int v_alku = (t0-t1) / 86400;
	if(k_alku<0 || v_alku<0) {
	    puts("Virheellinen alkuhetki");
	    break;
	}
	kausiptr += k_alku*resol;
	vuoptr   += v_alku*resol;
	
	int l1      = NCTDIM(kausivset, "time").len - k_alku;
	int l2      = NCTDIM(vuo, "time").len - v_alku;
	int maxpit  = MIN(l1, l2);
	tm1         = (struct tm){.tm_year=2020-1900, .tm_mon=1-1, .tm_mday=15};
	aikapit     = (mktime(&tm1) - t0) / 86400;
	if(aikapit > maxpit) {
	    puts("Liikaa aikaa");
	    aikapit = maxpit;
	}
	vuosia = aikapit / 365;

	for(int i=0; i<kausia; i++) {
	    if(!(ulos[i] = fopen(aprintf("vuotaulukot/%svuo_%s_%s_ft%i.csv",
					 luokitus_ulos[luokenum], pripost_ulos[ppnum], kaudet[i], ftnum), "w"))) {
		printf("Ei luotu ulostiedostoa\n");
		return 1;
	    }
	    fprintf(ulos[i], "#%s, data %i\n,Tg,mol/s,mol/m²,nmol/s/m²,season_length\n", kaudet[i], ftnum);
	}
	double tallenn[kausia][luokkia];
	for(int lajinum=0; lajinum<luokkia; lajinum++) {
	    double ainemäärä   [kausia] = {0}; // mol
	    double ala_ja_aika [kausia] = {0}; // m²*s
	    double ainemäärä1  [kausia] = {0}; // mol
	    double ala_ja_aika1[kausia] = {0}; // m²*s

	    struct laskenta l_args = {.ainemäärä=ainemäärä, .ala_ja_aika=ala_ja_aika,
				      .ainemäärä1=ainemäärä1, .ala_ja_aika1=ala_ja_aika1,
				      .lajinum=lajinum, .kausiptr=kausiptr};

	    switch(luokenum) {
	    case wetl_e: laske_wetland(&l_args); break;
	    case ikir_e: laske_ikir   (&l_args); break;
	    case kopp_e: laske_köpp   (&l_args); break;
	    }

	    double pintaala = ala_ja_aika[0] / aikapit;
	    for(int i=0; i<kausia; i++) {
		ainemäärä[i]   *= 86400;
		ala_ja_aika[i] *= 86400;
		double kauden_osuus = ala_ja_aika[i]/ala_ja_aika[0]; // molemmissa on sama ala, koska luokka on sama
		double aika         = kauden_osuus * aikapit*86400;
		fprintf(ulos[i], "%s,%.4lf,%.4lf,%.4lf,%.5lf,%.4lf\n", luoknimet[luokenum][lajinum],
			ainemäärä[i] / vuosia * 1e-12*16.0416, // Tg
			ainemäärä[i] / aika,                   // mol/s
			ainemäärä[i] / vuosia / pintaala,      // mol/m²
			ainemäärä[i] / ala_ja_aika[i]*1e9,     // nmol/s/m²
			kauden_osuus
		    );
		tallenn[i][lajinum] = ainemäärä[i] / ala_ja_aika[i]*1e9;
	    }
	}

	if(luokenum == wetl_e) {
	    FILE *f = fopen(aprintf("vuokertoimet_%s%i.csv", pripost_ulos[ppnum], ftnum), "w");
	    for(int i=0; i<kausia; i++)
		fprintf(f, ",%s", kaudet[i]);
	    fputc('\n', f);
	    for(int i=0; i<luokkia; i++) {
		fprintf(f, "%s", luoknimet[luokenum][i]);
		for(int k=0; k<kausia; k++)
		    fprintf(f, ",%.6lf", tallenn[k][i]/tallenn[k][0]);
		fputc('\n', f);
	    }
	    fclose(f);
	}

	for(int i=0; i<kausia; i++)
	    fclose(ulos[i]);
	nct_free_vset(&kausivset);
	kausivset = (nct_vset){0};
    }
    free(luok_c);
    nct_free_vset(luok_vs);
    nct_free_vset(&vuo);
    return 0;
}

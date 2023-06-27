#include <nctietue3.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>	// mkdir
#include <err.h>	// mkdir
#include <time.h>

/* Yhdistää sulamisdatasta kunkin vuoden tiedostot yhdeksi täyttäen puuttuvat päivät edellisellä arvolla. */

const int pit = 720*720;
int year0=2010, year1=2022;
const char* varnames[] = {"L3FT", NULL};
const char tiednimi_muoto[] = "raaka/W_XX-ESA,SMOS,NH_25KM_EASE2_%4i%02i%02i_o_v201_01_l3soilft.nc";
#define outdir "data/"

void koordinaatit(nct_set* set, nct_set* ulos) {
    nct_var* var;
    void* coord;
    var = nct_get_var(set, "x");
    nct_load_as(var, NC_DOUBLE);
    coord = var->data;
    var->not_freeable = 1;
    var = nct_get_dim(ulos, "x");
    nct_dim2coord(var, coord, NC_DOUBLE);

    var = nct_get_var(set, "y");
    nct_load_as(var, NC_DOUBLE);
    coord = var->data;
    var->not_freeable = 1;
    var = nct_get_dim(ulos, "y");
    nct_dim2coord(var, coord, NC_DOUBLE);
}

const char* viimevuoden_loppu;

int main(int argc, char** argv) {
    if (argc > 2) {
	year0 = atoi(argv[1]);
	year1 = atoi(argv[2]);
    }
    char units[60];
    strcpy(units, "days since 0000-00-00"); // jotta strlen on heti oikein
    char* uusi = malloc(366*pit);
    if (!uusi) {
	fprintf(stderr, "malloc uusi epäonnistui\n");
	return 1;
    }

    if (mkdir(outdir, 0755) && errno != EEXIST)
	err(1, "Ei luotu kansiota " outdir);

    struct tm aikatm = {0};
    char tiednimi[sizeof(tiednimi_muoto)+8];

    for (const char** varname_p = varnames; *varname_p; varname_p++) {
	const char* varname = *varname_p;

	nct_var* var;
	nct_set tallenn = {0};

	nct_put_interval(nct_dim2coord(nct_add_dim(&tallenn, 366, "time"), NULL, NC_USHORT), 0, 1);
	nct_add_varatt_text(tallenn.vars[0], "units",    units,                 0);
	nct_add_varatt_text(tallenn.vars[0], "calendar", "proleptic_gregorian", 0);
	nct_add_dim(&tallenn, 720, "y");
	nct_add_dim(&tallenn, 720, "x");
	nct_add_var_alldims(&tallenn, uusi, NC_BYTE, "data")->not_freeable = 1;
	int on_koordinaatit = 0;

	puts("");
	for(int y=year0; y<year1; y++) {
	    int päiviä = 0;
	    int yday0 = 0; // poikkeaa nollasta vain ensimmäisen vuonna
	    aikatm.tm_year = y-1900;
	    sprintf(units, "days since %4i-01-01", y);
	    for(int m=1; m<=12; m++) {
		aikatm.tm_mon = m-1;
		for(int d=1; d<=31; d++) {
		    aikatm.tm_mday = d;
		    sprintf(tiednimi, tiednimi_muoto, y, m, d);
		    if (access(tiednimi, F_OK))
			continue;
		    printf("\033[A\r%i%02i%02i\033[K\n", y, m, d);
		    fflush(stdout);
		    nct_set* set = nct_read_ncf(tiednimi, nct_rlazy);
		    nct_var* var = nct_get_var(set, varname);
		    if (!var) {
			printf("Ei muuttujaa %s\n", varname);
			exit(1);
		    }
		    nct_load_as(var, NC_UBYTE);
		    if (!on_koordinaatit)
			on_koordinaatit = (koordinaatit(set, &tallenn), 1);
		    mktime(&aikatm);
		    /* Ensimmäinen vuosi saa alkaa keskeltä. */
		    if (y==year0 && !päiviä)
			yday0 = aikatm.tm_yday;
		    /* Täytetään puuttuvat päivät viimeksi luetulla. */
		    const char* ptr = päiviä ? uusi + (päiviä-1)*pit : viimevuoden_loppu;
		    while(päiviä < aikatm.tm_yday-yday0) {
			memmove(uusi+päiviä*pit, ptr, pit); // periaatteessa viimevuoden_loppu voisi leikata tätä, jos koko vuosi puuttuisi
			päiviä++;
		    }

		    memcpy(uusi+päiviä*pit, var->data, pit);
		    päiviä++;
		    nct_free1(set);
		}
	    }
	    /* Tarkistetaan, että vuosi kirjoitetaan loppuun, vaikka dataa puuttuisi lopusta.
	       Viimeinen vuosi saa kuitenkin loppua kesken. */
	    if (y+1 < year1) {
		aikatm.tm_mday = 31;
		aikatm.tm_mon = 11;
		mktime(&aikatm);
		const char* ptr = uusi + (päiviä-1)*pit;
		while (päiviä < aikatm.tm_yday+1-yday0) {
		    memcpy(uusi+päiviä*pit, ptr, pit);
		    päiviä++;
		}
	    }

	    viimevuoden_loppu = uusi+(päiviä-1)*pit;

	    nct_set_start(tallenn.dims[0], 0);
	    nct_set_length(tallenn.dims[0], aikatm.tm_yday+1);
	    nct_set_start(tallenn.dims[0], yday0);

	    char tallnimi[32];
	    sprintf(tallnimi, outdir "%s_%i.nc", varname, y);
	    /* Tallennettakoon pakattuna. */
	    nct_create_nc_def(&tallenn, tallnimi);
	    nct_var* var = nct_firstvar(&tallenn);
	    ncfunk(nc_def_var_deflate, tallenn.ncid, var->ncid, 0, 1, 6);
	    for(int i=0; i<tallenn.nvars; i++)
		ncfunk(nc_put_var, tallenn.ncid, tallenn.vars[i]->ncid, tallenn.vars[i]->data);
	    nct_close_nc(&tallenn);
	}
	nct_free1(&tallenn);
    }
    free(uusi);
    return 0;
}

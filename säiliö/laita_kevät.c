#include <nctietue2.h>
#include <stdio.h>
#include <stdlib.h>

#define dir "../"
#define ikirluokkia 4

#define arrpit(arr) (sizeof(arr) / sizeof(*(arr)))
char* alut[] = {"freezing_start", "winter_start", "summer_start"};
char* loput[] = {"freezing_end", "winter_end", "summer_end"};

typedef struct {
    short* sp;
    int vuosia;
    int vuosi0;
} taul;

static void muunna(nct_var* päivä) {
    volatile float* fpäivä = päivä->data;
    volatile short* späivä = päivä->data;
    int pit = nct_get_varlen(päivä);
    for (int p=0; p<pit; p++)
	späivä[p] = fpäivä[p]==fpäivä[p]? fpäivä[p]: 999;
    var->xtype = NC_SHORT;
    var->capacity *= 2;
}

/* Tämä kutsutaan vain kerran, joten voidaan hyvällä mielellä palauttaa tietue kopioiden. */
static taul lue_kevät() {
    FILE* f = fopen("../../kevät.csv", "r");
    int pit = 0;
    while(1) {
	char c = fgetc(f);
	if(c=='\n')
	    break;
	pit += c==',';
    }
    data = malloc(2*ikirluokkia*pit*sizeof(short));
    int ind=0;
    int vuosi0;
    for(int al=0; al<2; al++) {
	for(int il=0; il<ikirluokkia; il++) {
	    while(getc(f) != ',');
	    for(int i=0; i<pit; i++)
		fscanf(f, "%d", data+ind++);
	}
	fscanf(f, ",%d", &vuosi0);
	while(getc(f) != '\n');
    }
    return (taul){.sp=data, .vuosia=pit, .vuosi0=vuosi0};
}

int main() {
    nct_vset* kauvset = nct_read_ncfile(dir"kausien_päivät.nc");
    nct_var* tmpvar;
    taul kevät = lue_kevät();
    nct_get_dim(kauvset, "vuosi")->len = kevät.vuosia; // 2021 jää pois

    short *alu[arrpit(alut)], *lop[arrpit(alut)];
    for (int i=0; i<arrpit(alut); i++) {
	tmpvar = nct_get_var(kauvset, alut[i]);
	muunna(tmpvar);
	alu[i] = tmpvar->data;
	tmpvar = nct_get_var(kauvset, loput[i]);
	muunna(tmpvar);
	lop[i] = tmpvar->data;
    }

    nct_vset ikivset = nct_read_ncfile(dir"ikirdata.nc");
    tmpvar = nct_get_var(ikivset, "vuosi");
    int ikirv0 = nct_get_integer(tmpvar, 0);
    int ikirv1_ = nct_get_integer(tmpvar, -1);
    int ikirv[kevät.vuosia];
    for(int i=0; i<kevät.vuosia; i++)
	if(kevät.vuosi0+i > ikirv1_)
	    ikirv[i] = ikirv1_;
	else
	    ikirv[i] = kevät.vuosi0-ikirv0+i;

    char* luokka = nct_get_var(ikivset, "luokka")->data;
    int res = nct_get_varlen_from(luokka, 1);
    short* kev0 = kevät.sp;
    short* kev1 = kev0 + ikirluokkia*kevät.vuosia;
    for(int v=0; v<kevät.vuosia; v++) {
	for(int r=0; r<res; r++) {
	    int ikluok = luokka[ikirv[v]*res+r];
	    for(int k=0; k<arrpit[alut]; k++) {
		short num0 = alu[k][v*res+r];
		short num1 = lop[k][v*res+r];
		int kev_ind = ikluok*kevät.vuosia + v;
		//if(num0 <= kev0[kev_ind] &&
	    }
	}
    }
}

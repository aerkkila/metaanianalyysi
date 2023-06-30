#include <nctietue3.h>
#include <stdio.h>
#include "pintaalat.h"
#include <assert.h>

const int latpit = 55; // pintaalat.h ei toimi, ellei ole näin
const int lonpit = 360;
const int luokkia = 4;

double laske(char* data, int luokka) {
    int ind = 0;
    double ala = 0;
    for(int j=0; j<latpit; j++)
	for(int i=0; i<lonpit; i++, ind++)
	    ala += (data[ind] == luokka) * pintaalat[j];
    return ala;
}

void valintalajittelu(double* arr, int pit) {
    for(; pit>1; pit--) {
	double max = arr[0];
	int argmax = 0;
	int etum = 1;
	if (max < 0) {
	    max = -max;
	    etum = -1;
	}
	for(int i=1; i<pit; i++)
	    if (arr[i] > max) {
		max = arr[i];
		argmax = i;
		etum = 1;
	    }
	    else if (-arr[i] > max) {
		max = -arr[i];
		argmax = i;
		etum = -1;
	    }
	arr[argmax] = arr[pit-1];
	arr[pit-1] = etum * max;
    }
}

int main() {
    nct_set* set = nct_read_nc("ikirdata.nc");
    assert(nct_get_var(set, "lat")->len == latpit);
    assert(nct_get_var(set, "lon")->len == lonpit);
    char* luokkadata = nct_get_var(set, "luokka")->data;
    int vuosia, *vuodet;
    {
	nct_var* var = nct_get_var(set, "vuosi");
	vuosia = var->len;
	vuodet = var->data;
	assert(var->dtype == NC_INT);
    }
    double alat[luokkia][vuosia];
    double ero_pros[luokkia][vuosia-1];
    for(int luokka=0; luokka<luokkia; luokka++) {
	for(int v=0; v<vuosia; v++)
	    alat[luokka][v] = laske(luokkadata + v*latpit*lonpit, luokka);
	for(int v=1; v<vuosia; v++)
	    ero_pros[luokka][v-1] = ((alat[luokka][v] - alat[luokka][v-1]) / alat[luokka][v-1]) * 100;
    }

    for(int v=1; v<vuosia; v++) {
	printf("%4i: ", vuodet[v]);
	for(int luokka=0; luokka<luokkia; luokka++)
	    printf("%7.2f ", ero_pros[luokka][v-1]);
	putchar('\n');
    }

    for(int luokka=0; luokka<luokkia; luokka++)
	valintalajittelu(ero_pros[luokka], vuosia-1);

    for(int v=1; v<vuosia; v++) {
	for(int luokka=0; luokka<luokkia; luokka++)
	    printf("%7.2f ", ero_pros[luokka][v-1]);
	putchar('\n');
    }
}

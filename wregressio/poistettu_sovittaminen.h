
void sovittaminen_kerralla(data_t* dt, double kertoimet[]) {
    double r2;
    sovita_monta(dt, kertoimet, &r2, 0);
    printf("r² = %.4lf\n", r2);
    for(int i=0; i<wpit; i++)
	printf("%-12.4lf", kertoimet[i]);
    putchar('\n');
    for(int i=1; i<wpit; i++)
	printf("%-12.4lf", kertoimet[i]+kertoimet[0]);
    putchar('\n');
}

void sovita_1(data_t* dt, int num, double* vakio, double* kulma, double* r2) {
    double sum2, cov00, cov01, cov11;
    gsl_fit_wlinear(dt->wdata[num], 1, dt->alat, 1, dt->vuo, 1, dt->pit, vakio, kulma, &cov00, &cov01, &cov11, &sum2);
    *r2 = 1 - (sum2 / gsl_stats_wtss(dt->alat, 1, dt->vuo, 1, dt->pit));
}

void sovittaminen_erikseen(data_t* dt) {
    double vakio[wpit], kulma[wpit], r2;
    for(int i=1; i<wpit; i++) {
	sovita_1(dt, i, vakio+i, kulma+i, &r2);
	printf("vakio = %7.4lf\tkulma = %8.4lf\tyksi = %.4lf\tr² = %.5lf (%s)\n",
	       vakio[i], kulma[i], vakio[i]+kulma[i], r2, wetlnimet[i]);
    }
    double alat[wpit];
    memset(alat, 0, wpit*sizeof(double));
    double summa = 0, ala = 0;
    for(int i=1; i<wpit; i++) {
	for(int r=0; r<dt->pit; r++)
	    alat[i] += dt->alat[r]*dt->wdata[i][r];
	summa += alat[i] * (vakio[i]+kulma[i]);
	ala += alat[i];
    }
    printf("keskiarvo = %.5lf\n", summa/ala);
}

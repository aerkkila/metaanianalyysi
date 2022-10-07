/* Tämä oli osa wregressio.c:tä. Tallennettu kaiken varalta. */
    f = popen(aprintf("./piirrä_bootstrap.py %s", python_arg), "w");
    assert(f);
    assert(fwrite(&pit, 4, 1, f) == 1);
    assert(fwrite(&nboot_vakio, 4, 1, f) == 1);
    fprintf(f, "%s\n%s\n", kaudet[kausi], menetelmät[menetelmä]);

    putchar('\n');
    korosta;
    for(int i=1; i<pit; i++)
	printf("%-14s ", wetlnimet[i]);
    printf("%-6s pisteitä\n", "raja");
    perusväri;
    for(int a=0; a<rajapit; a++) {
	luo_data(&dt, &dt1, kausic, 0.05, vuorajat[a]);
	sovita_monta(&dt1, kertoimet, &r2, nboot_vakio);
	for(int i=1; i<pit; i++) {
	    kirj[i-1] = kertoimet[i]+kertoimet[0];
	    printf("%-15.3lf", kirj[i-1]);
	}
	printf("%-6.0lf %i\n", vuorajat[a], dt1.pit);
	kirj[pit-1] = (double)dt1.pit;
	kirj[pit] = vuorajat[a];
	assert(fwrite(kirj, sizeof(double), pit+1, f) == pit+1);
	assert(fwrite(kertoimet+pit, sizeof(double), (pit-1)*nboot_vakio, f) == (pit-1)*nboot_vakio);
    }
    vapauta(pclose, f);
    putchar('\n');

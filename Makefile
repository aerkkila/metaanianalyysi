kuvat: kuvia/LPX2019_flux1x1_kartta*.png kuvia/köppen_kartta.png kuvia/köppen_laatikko_*.png kuvia/prf_ft_histog_*.png kuvia/prf_ft_laatikko_*.png kuvia/prf_kartta_mean.png kuvia/prf_köppen_laatikko_*.png kuvia/prf_maa_histog*.png kuvia/prf_maa_laatikko_*.png kuvia/prf_metaani_bar.png kuvia/prf_metaani_kartta*.png kuvia/prf_metaani_laatikko.png

muunna_shapefile: muunna_shapefile.c köppentunnisteet.c
	gcc -o $@ muunna_shapefile.c -lshp -lnetcdf -lm -pthread -Ofast

kuvia/LPX2019_flux1x1_kartta*.png: LPX2019_flux1x1_kartta.py
	./LPX2019_flux1x1_kartta.py -s

kuvia/köppen_kartta.png: köppen_kartta.py
	./köppen_kartta.py -s

kuvia/köppen_laatikko_*.png: köppen_laatikko.py
	./köppen_laatikko.py -s

kuvia/prf_ft_histog_*.png: prf_ft_histog.py
	./prf_ft_histog.py -s start
	./prf_ft_histog.py -s end

kuvia/prf_ft_laatikko_*.png: prf_ft_laatikko.py
	./prf_ft_laatikko.py -s start
	./prf_ft_laatikko.py -s end

kuvia/prf_kartta_mean.png: prf_kartta_mean.py
	./prf_kartta_mean.py -s

kuvia/prf_köppen_laatikko_*.png: prf_köppen_laatikko.py
	./prf_köppen_laatikko.py -s start
	./prf_köppen_laatikko.py -s end

kuvia/prf_maa_histog*.png: prf_maa_histog.py
	./prf_maa_histog.py -s start
	./prf_maa_histog.py -s end

kuvia/prf_maa_laatikko_*.png: prf_maa_laatikko.py
	./prf_maa_laatikko.py -s start
	./prf_maa_laatikko.py -s end

kuvia/prf_metaani_bar.png: prf_metaani_bar.py
	./prf_metaani_bar.py -s

kuvia/prf_metaani_laatikko.png: prf_metaani_laatikko.py
	./prf_metaani_laatikko.py -s

kuvia/prf_metaani_kartta*.png: prf_metaani_kartta.py
	./prf_metaani_kartta.py -s

LPX2019_flux1x1_kartta.py: config_muutt.py
köppen_kartta.py: köppen_laatikko.py
köppen_laatikko.py: talven_ajankohta.py
prf_ft_histog.py: prf.py talven_ajankohta.py
prf_ft_laatikko.py: prf.py talven_ajankohta.py
prf_kartta_mean.py: prf.py
prf_köppen_laatikko.py: köppen_laatikko.py prf.py talven_ajankohta.py
prf_maa_histog.py: prf_maa_laatikko.py prf.py
prf_maa_laatikko.py: maalajit.py prf.py talven_ajankohta.py
prf_metaani_bar.py: config_muutt.py prf.py talven_ajankohta.py
prf_metaani_kartta.py: config_muutt.py prf.py talven_ajankohta.py
prf_metaani_laatikko.py: config_muutt.py prf.py talven_ajankohta.py
prf.py:

kuvat: kuvia/köppen_kartta.png kuvia/prf_histog_*.png kuvia/prf_kartta_mean.png kuvia/prf_maa_laatikko_*.png kuvia/prf_metaani_bar.png kuvia/prf_metaani_kartta*.png

muunna_shapefile: muunna_shapefile.c köppentunnisteet.c
	gcc -o $@ muunna_shapefile.c -lshp -lnetcdf -lm -pthread -Ofast

kuvia/köppen_kartta.png: köppen_kartta.py
	./köppen_kartta.py -s

kuvia/prf_histog_*.png: prf_histog.py
	./prf_histog.py -s start
	./prf_histog.py -s end

kuvia/prf_kartta_mean.png: prf_kartta_mean.py
	./prf_kartta_mean.py -s

kuvia/prf_maa_laatikko_*.png: prf_maa_laatikko.py
	./prf_maa_laatikko.py -s start
	./prf_maa_laatikko.py -s end

kuvia/prf_metaani_bar.png: prf_metaani_bar.py
	./prf_metaani_bar.py -s

kuvia/prf_metaani_kartta*.png: prf_metaani_kartta.py
	./prf_metaani_kartta.py -s

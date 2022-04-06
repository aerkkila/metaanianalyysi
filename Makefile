prf_koppen_csv = prf_köppen_['end''start']*[0-9]*.csv
prf_maa_DOY_csv = prf_maa_DOY_['end''start']*[0-9]*.csv
prf_maa_osuus_csv = prf_maa_osuus_[0-9]*.csv
tyotiedostot = "/media/levy/tyotiedostot"

all: flux1x1_jäätymiskausi.nc köppen1x1maski.nc kuvia/LPX2019_flux1x1_kartta*.png kuvia/köppen_kartta.png kuvia/köppen_laatikko_*.png kuvia/prf_ft_histog_*.png kuvia/prf_ft_laatikko_*.png kuvia/prf_kartta_mean.png kuvia/prf_köppen_histog*.png kuvia/prf_köppen_laatikko_*.png kuvia/prf_maa_histog*.png kuvia/prf_maa_laatikko_*.png kuvia/prf_metaani_kartta_jäätymiskausi*.png kuvia/prf_metaani_kartta_kokoaika*.png kuvia/prf_metaani_laatikko.png prf_maa.nc

../edgartno_lpx/flux1x1_1d.nc: ../edgartno_lpx/interpoloi_flux1x1.py
	cd ../edgartno_lpx/ && ./interpoloi_flux1x1.py

BAWLD1x1.nc: BAWLD1x1.py
	./BAWLD1x1.py

flux1x1_jäätymiskausi.nc: flux1x1_jäätymiskausi.py ../edgartno_lpx/flux1x1_1d.nc
	./flux1x1_jäätymiskausi.py

köppen1x1maski.nc: muunna_shapefile
	./muunna_shapefile -o $@

muunna_shapefile: muunna_shapefile.c köppentunnisteet.c
	gcc -Wall -o $@ muunna_shapefile.c -lshp -lnetcdf -lm -pthread -Ofast

muunna_shapefile0: muunna_shapefile.c köppentunnisteet.c
	gcc -Wall -o $@ muunna_shapefile.c -lshp -lnetcdf -lm -pthread -g

kuvia/LPX2019_flux1x1_kartta*.png: LPX2019_flux1x1_kartta.py
	./LPX2019_flux1x1_kartta.py -s

kuvia/köppen_kartta.png: köppen_kartta.py
	./köppen_kartta.py -s

kuvia/köppen_laatikko_*.png: köppen_laatikko.py
	./köppen_laatikko.py -s

kuvia/prf_ft_histog_*.png: prf_ft_histog.py prfdata_avg.nc
	./prf_ft_histog.py -s start
	./prf_ft_histog.py -s end

kuvia/prf_ft_laatikko_*.png: prf_ft_laatikko.py prfdata_avg.nc
	./prf_ft_laatikko.py -s start
	./prf_ft_laatikko.py -s end

kuvia/prf_kartta_mean.png: prf_kartta_mean.py
	./prf_kartta_mean.py -s

kuvia/prf_köppen_histog*.png: prf_köppen_histog.py ${prf_koppen_csv}
	./prf_köppen_histog.py -s

kuvia/prf_köppen_laatikko_*.png: prf_köppen_laatikko.py
	./prf_köppen_laatikko.py -s start
	./prf_köppen_laatikko.py -s end

kuvia/prf_maa_histog*.png: prf_maa_histog.py ${prf_maa_osuus_csv} ${prf_maa_doy_csv}
	./prf_maa_histog.py -s

kuvia/prf_maa_laatikko_*.png: prf_maa_laatikko.py ${prf_maa_DOY_csv}
	./prf_maa_laatikko.py -s start
	./prf_maa_laatikko.py -s end

kuvia/prf_metaani_laatikko.png: prf_metaani_laatikko.py
	./prf_metaani_laatikko.py -s

kuvia/prf_metaani_kartta_jäätymiskausi*.png: prf_metaani_kartta_jäätymiskausi.py flux1x1_jäätymiskausi.nc
	./prf_metaani_kartta_jäätymiskausi.py -s

kuvia/prf_metaani_kartta_kokoaika*.png: prf_metaani_kartta_kokoaika.py ../edgartno_lpx/flux1x1_1d.nc
	./prf_metaani_kartta_kokoaika.py -s

prfdata.nc: prfdata.py
	./prfdata.py

prf_maa.nc: prf_maa.py BAWLD1x1.nc prfdata.nc
	./prf_maa.py

${prf_koppen_csv}: prf_köppen_data.py
	./prf_köppen_data.py -s

${prf_maa_DOY_csv}: prf_maa_data.py
	./prf_maa_data.py -s

${prf_maa_osuus_csv}: prf_maa_data.py
	./prf_maa_data.py -s

../edgartno_lpx/interpoloi_flux1x1.py: interpoloi_flux1x1.py
	cp interpoloi_flux1x1.py $@
BAWLD1x1.py: maalajit.py
	touch $@
LPX2019_flux1x1_kartta.py: config_muutt.py
	touch $@
köppen_kartta.py: köppen_laatikko.py
	touch $@
köppen_laatikko.py: talven_ajankohta.py
	touch $@
prf__histog.py: maalajit.py ikirluokat.py
	touch $@
prf_ft_histog.py: talven_ajankohta.py ikirluokat.py
	touch $@
prf_ft_laatikko.py: ikirluokat.py talven_ajankohta.py
	touch $@
prf_kartta_mean.py: prf.py
	touch $@
prf_köppen_histog.py: prf__histog.py
	touch $@
prf_köppen_laatikko.py: köppen_laatikko.py prf.py talven_ajankohta.py
	touch $@
prf_maa.py:
	touch $@
prf_maa_data.py: maalajit.py prf.py talven_ajankohta.py
	touch $@
prf_maa_histog.py: prf__histog.py
	touch $@
prf_maa_laatikko.py: prf.py maalajit.py
	touch $@
prf_metaani_kartta_*.py: prf_metaani_kartta.py
	touch $@
prf_metaani_kartta.py: prf.py
	touch $@
prf_metaani_laatikko.py: config_muutt.py prf.py
	touch $@
prf.py: ikirluokat.py
	touch $@
prfdata.py: prf.py
	touch $@
prfdata_avg.py: prf.py
	touch $@

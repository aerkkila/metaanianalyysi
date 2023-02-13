# pintaalat.py ja kaudet.c pitää olla ajettuina ennen tätä
all: vuotaul_00.target vuotaul_10.target vuotaul_01.target vuotaul_02.target vuojakaumadata.target vuojakaumadata_vuosittain.target vuosijainnit.nc kuvat taulukot.target
argv =

vuodata.out: vuotaul.c
	gcc -Wall -o $@ $< -lm `pkg-config --libs nctietue2` -Ofast
vvt.target: vvk vvw vvi vvt vvkk vvik
vvk: vuodata.out
	./$< vuosittain köpp $(argv)
vvi: vuodata.out
	./$< vuosittain ikir $(argv)
vvw: vuodata.out
	./$< vuosittain wetl $(argv)
vvt: vuodata.out
	./$< vuosittain totl $(argv)
vvkk: vuodata.out
	./$< vuosittain köpp kosteikko $(argv)
vvik: vuodata.out
	./$< vuosittain ikir kosteikko $(argv)

vt.target: vk vw vi vt vkk vik
vk: vuodata.out
	./$< köpp $(argv)
vi: vuodata.out
	./$< ikir $(argv)
vw: vuodata.out
	./$< wetl $(argv)
vt: vuodata.out
	./$< totl $(argv)
vkk: vuodata.out
	./$< köpp kosteikko $(argv)
vik: vuodata.out
	./$< ikir kosteikko $(argv)

vuotaul_00.target: vuotaul_köppen_pri.csv vuotaul_köppen_post.csv vuotaul_ikir_pri.csv vuotaul_ikir_post.csv vuotaul_wetland_pri.csv vuotaul_wetland_post.csv
	cat vuotaulukot/*_pri_*.csv > vuotaul_pri.csv
	cat vuotaulukot/*_post_*.csv > vuotaul_post.csv
vuotaul_00.out: vuotaul_yleinen.c
	gcc -Wall -g -O2 vuotaul_yleinen.c -o $@ `pkg-config --libs nctietue2` -lm -DKOSTEIKKO=0 -Dkosteikko_kahtia=0
vuotaul_wetland_post.csv: vuotaul_00.out
	./vuotaul_00.out wetl post
	./vuotaul_00.out wetl post
vuotaul_wetland_pri.csv: vuotaul_00.out
	./vuotaul_00.out wetl pri
	./vuotaul_00.out wetl pri
vuotaul_köppen_post.csv: vuotaul_00.out
	./vuotaul_00.out köpp post
	./vuotaul_00.out köpp post
vuotaul_köppen_pri.csv: vuotaul_00.out
	./vuotaul_00.out köpp pri
	./vuotaul_00.out köpp pri
vuotaul_ikir_post.csv: vuotaul_00.out
	./vuotaul_00.out ikir post
	./vuotaul_00.out ikir post
vuotaul_ikir_pri.csv: vuotaul_00.out
	./vuotaul_00.out ikir pri
	./vuotaul_00.out ikir pri

# calculates climate and permafrost class data with only their wetland areas into vuotaulukot/*k1.csv
vuotaul_10.target: vuotaul_köppen_post10.csv vuotaul_ikir_post10.csv
vuotaul_10.out: vuotaul_yleinen.c
	gcc -Wall -g -O2 vuotaul_yleinen.c -o $@ `pkg-config --libs nctietue2` -lm -DKOSTEIKKO=1 -Dkosteikko_kahtia=0
vuotaul_köppen_post10.csv: vuotaul_10.out
	./vuotaul_10.out köpp post
	./vuotaul_10.out köpp post
vuotaul_ikir_post10.csv: vuotaul_10.out
	./vuotaul_10.out ikir post
	./vuotaul_10.out ikir post

# calculates wetland data without the mixed area into vuotaulukot/kahtia/*
vuotaul_01.target: vuotaul_wetland_post01.csv
vuotaul_01.out: vuotaul_yleinen.c
	gcc -Wall -g -O2 vuotaul_yleinen.c -o $@ `pkg-config --libs nctietue2` -lm -DKOSTEIKKO=0 -Dkosteikko_kahtia=1
vuotaul_wetland_post01.csv: vuotaul_01.out
	./vuotaul_01.out wetl post
	./vuotaul_01.out wetl post

# calculates wetland data with only the mixed area into vuotaulukot/kahtia_keskiosa/*
vuotaul_02.target: vuotaul_wetland_post02.csv
vuotaul_02.out: vuotaul_yleinen.c
	gcc -Wall -g -O2 vuotaul_yleinen.c -o $@ `pkg-config --libs nctietue2` -lm -DKOSTEIKKO=0 -Dkosteikko_kahtia=2
vuotaul_wetland_post02.csv: vuotaul_02.out
	./vuotaul_02.out wetl post
	./vuotaul_02.out wetl post

# vuojakaumadata
# Jos tässä on optimointina -Ofast, saadaan muistialueen ylitys,
# koska silloin on käytössä -ffast-math, joka sisältää -ffinite-math-only,
# jolloin epälukujen tarkistus ei toimi.
# Olisi hyvä vaihtaa liukuluvut int16:en ja käyttää sovittua täyttöarvoa epälukujen sijaan.
vuojakaumadata.out: vuojakaumadata.c
	gcc -Wall $< -o $@ `pkg-config --libs nctietue2 gsl` -g -O3
vuojakauma_ikir: vuojakaumadata.out
	./$< ikir post
vuojakauma_köpp: vuojakaumadata.out
	./$< köpp post
vuojakauma_wetl: vuojakaumadata.out
	./$< wetl post
vuojakauma_köppkost: vuojakaumadata.out
	./$< köpp post kost
vuojakauma_ikirkost: vuojakaumadata.out
	./$< ikir post kost
vuojakaumadata.target: vuojakauma_ikir vuojakauma_köpp vuojakauma_wetl vuojakauma_ikirkost vuojakauma_köppkost

# vuojakaumadata vuosittain
vuojakaumadata_vuosittain.out: vuojakaumadata.c
	gcc -Wall $< -o $@ `pkg-config --libs nctietue2 gsl` -g -O3 -DVUODET_ERIKSEEN=1
vuojakauma_vuosittain_ikir: vuojakaumadata_vuosittain.out
	./$< ikir post
vuojakauma_vuosittain_köpp: vuojakaumadata_vuosittain.out
	./$< köpp post
vuojakauma_vuosittain_wetl: vuojakaumadata_vuosittain.out
	./$< wetl post
vuojakaumadata_vuosittain.target: vuojakauma_vuosittain_ikir vuojakauma_vuosittain_köpp vuojakauma_vuosittain_wetl
	cat vuojakaumadata/vuosittain/emissio_*_post.csv > emissio_vuosittain.csv

vuosijainnit.nc: vuosijainnit.out
	./$<
vuosijainnit.out: vuosijainnit.c
	gcc -Wall -o $@ $< `pkg-config --libs nctietue2` -lm -O3 -g

kuvat: vuosijainnit.nc
	./köppikir_kartta.py -s
	./köppikir_kartta.py ikir -s
	./kaudet_laatikko.py -s
	./permafrost_wetland_kartta.py -s
	./xvuo_laatikko.py -s
	./vuojakaumalaatikko.py -s
	./vuojakaumalaatikko_vuosittain.py -s
	./vuosijainnit.py -s

vuotaul.target:
	gcc vuotaul_latex.c -O2 -o vuotaul.out
	./vuotaul.out
	gcc vuotaul_latex.c -DKOST_KAHTIA=1 -O2 -o vuotaul.out
	./vuotaul.out
	gcc vuotaul_latex.c -DKOST_KAHTIA=2 -O2 -o vuotaul.out
	./vuotaul.out
	gcc vuotaul_latex.c -DKOSTEIKKO=1 -O3 -o vuotaul.out
	./vuotaul.out

taulukot.target: vuotaul.target
	./köppikir_taulukko.py
	gcc lattaul.c -O1 -o vuotaul.out
	./vuotaul.out

# Näitä ei sisälly all-kohteeseen
päivät_vuosittain.out: päivät_vuosittain.c
	gcc -Wall $< -o $@ `pkg-config --libs nctietue2 gsl` -lm -g -O3
päivät_vuosittain_ikir: päivät_vuosittain.out
	./päivät_vuosittain.out kaikki_muuttujat ikir
päivät_vuosittain_köpp: päivät_vuosittain.out
	./päivät_vuosittain.out kaikki_muuttujat köpp
päivät_vuosittain_wetl: päivät_vuosittain.out
	./päivät_vuosittain.out kaikki_muuttujat wetl
päivät_vuosittain.target: päivät_vuosittain_ikir päivät_vuosittain_köpp päivät_vuosittain_wetl
	cat kausidata2301/*_*.csv > kausidata2301/data.csv

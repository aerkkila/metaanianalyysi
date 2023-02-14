# pintaalat.py ja kaudet.c pitää olla ajettuina ennen tätä
#all: vuotaul_00.target vuotaul_10.target vuotaul_01.target vuotaul_02.target vuojakaumadata.target vuojakaumadata_vuosittain.target vuosijainnit.nc kuvat taulukot.target
all: vt.target vtpri.target vuojakaumadata.target vuojakaumadata_vuosittain.target vuosijainnit.nc kuvat.target taulukot.target
argv =

vuodata.out: vuodata.c
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

vt.target: vk vw vi vt vkk vik vwm vwp
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
vwm: vuodata.out
	./$< wetl temperate $(argv)
vwp: vuodata.out
	./$< wetl nontemperate $(argv)

vtpri.target: vkpri vwpri vipri vtpri vkkpri vikpri vwmpri vwppri
vkpri: vuodata.out
	./$< köpp pri $(argv)
vipri: vuodata.out
	./$< ikir pri $(argv)
vwpri: vuodata.out
	./$< wetl pri $(argv)
vtpri: vuodata.out
	./$< totl pri $(argv)
vkkpri: vuodata.out
	./$< köpp kosteikko pri $(argv)
vikpri: vuodata.out
	./$< ikir kosteikko pri $(argv)
vwmpri: vuodata.out
	./$< wetl temperate pri $(argv)
vwppri: vuodata.out
	./$< wetl nontemperate pri $(argv)

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

kuvat.target: vuosijainnit.nc
	./köppikir_kartta.py -s
	./köppikir_kartta.py ikir -s
	./kaudet_laatikko.py -s
	./permafrost_wetland_kartta.py -s
	./vuojakaumalaatikko.py -s
	./vuojakaumalaatikko_vuosittain.py -s -nf
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
	gcc lattaul.c -O1 -o lattaul.out
	./lattaul.out

# Näitä ei sisälly all-kohteeseen
# Lienevät vanhentuneita
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

kosteikko = 0
opt = 2

yleiskosteikko.out: yleiskosteikko.c
	gcc -Wall ${@:.out=.c} -o $@ `pkg-config --libs nctietue2 gsl` -g -O2

vuojakaumadata.out: vuojakaumadata.c
	gcc -Wall vuojakaumadata.c -o $@ `pkg-config --libs nctietue2 gsl` -g -O3
vuojakauma_ikir: vuojakaumadata.out
	./vuojakaumadata.out ikir post
vuojakauma_köpp: vuojakaumadata.out
	./vuojakaumadata.out köpp post
vuojakauma_wetl: vuojakaumadata.out
	./vuojakaumadata.out wetl post
vuojakaumadata.target: vuojakauma_ikir vuojakauma_köpp vuojakauma_wetl

vuojakauma_pri_ikir: vuojakaumadata.out
	./vuojakaumadata.out ikir pri
vuojakauma_pri_köpp: vuojakaumadata.out
	./vuojakaumadata.out köpp pri
vuojakauma_pri_wetl: vuojakaumadata.out
	./vuojakaumadata.out wetl pri
vuojakaumadata_pri.target: vuojakauma_pri_ikir vuojakauma_pri_köpp vuojakauma_pri_wetl

vuojakaumadata_vuosittain.out: vuojakaumadata.c
	gcc -Wall vuojakaumadata.c -o $@ `pkg-config --libs nctietue2 gsl` -g -O3 -DVUODET_ERIKSEEN=1
vuojakauma_vuosittain_ikir: vuojakaumadata_vuosittain.out
	./vuojakaumadata_vuosittain.out ikir post
vuojakauma_vuosittain_köpp: vuojakaumadata_vuosittain.out
	./vuojakaumadata_vuosittain.out köpp post
vuojakauma_vuosittain_wetl: vuojakaumadata_vuosittain.out
	./vuojakaumadata_vuosittain.out wetl post
vuojakaumadata_vuosittain.target: vuojakauma_vuosittain_ikir vuojakauma_vuosittain_köpp vuojakauma_vuosittain_wetl
	cat vuojakaumadata/vuosittain/emissio_*_post.csv > emissio_vuosittain.csv

vuojakauma_vuosittain_pri_ikir: vuojakaumadata_vuosittain.out
	./vuojakaumadata_vuosittain.out ikir pri
vuojakauma_vuosittain_pri_köpp: vuojakaumadata_vuosittain.out
	./vuojakaumadata_vuosittain.out köpp pri
vuojakauma_vuosittain_pri_wetl: vuojakaumadata_vuosittain.out
	./vuojakaumadata_vuosittain.out wetl pri
vuojakaumadata_vuosittain_pri.target: vuojakauma_vuosittain_pri_ikir vuojakauma_vuosittain_pri_köpp vuojakauma_vuosittain_pri_wetl

alkupäivät_vuosittain.out: kertajakaumadata.c
	gcc -Wall kertajakaumadata.c -o $@ `pkg-config --libs nctietue2 gsl` -lm -g -O3 -DVUODET_ERIKSEEN=1
alkupäivät_vuosittain_ikir: alkupäivät_vuosittain.out
	./alkupäivät_vuosittain.out ikir post
alkupäivät_vuosittain_köpp: alkupäivät_vuosittain.out
	./alkupäivät_vuosittain.out köpp post
alkupäivät_vuosittain_wetl: alkupäivät_vuosittain.out
	./alkupäivät_vuosittain.out wetl post
alkupäivät_vuosittain.target: alkupäivät_vuosittain_ikir alkupäivät_vuosittain_köpp alkupäivät_vuosittain_wetl
	cat kausijakaumadata/alkupäivät_*.csv > alkupäivät_vuosittain.csv

wetlandsumma.out: wetlandsumma.c
	gcc -Wall wetlandsumma.c -o $@ `pkg-config --libs nctietue` -lm -O3

kost_kahtia = 0
vuotaul_yleinen.out: vuotaul_yleinen.c
	gcc -Wall -g -O2 vuotaul_yleinen.c -o $@ `pkg-config --libs nctietue2` -lm -DKOSTEIKKO=${kosteikko} -Dkosteikko_kahtia=${kosteikko_kahtia}
vuotaul_wetland_post.csv: vuotaul_yleinen.out
	./vuotaul_yleinen.out wetl post
vuotaul_wetland_pri.csv: vuotaul_yleinen.out
	./vuotaul_yleinen.out wetl pri
vuotaul_köppen_post.csv: vuotaul_yleinen.out
	./vuotaul_yleinen.out köpp post
vuotaul_köppen_pri.csv: vuotaul_yleinen.out
	./vuotaul_yleinen.out köpp pri
vuotaul_ikir_post.csv: vuotaul_yleinen.out
	./vuotaul_yleinen.out ikir post
vuotaul_ikir_pri.csv: vuotaul_yleinen.out
	./vuotaul_yleinen.out ikir pri
vuotaul_yleinen.target: vuotaul_köppen_pri.csv vuotaul_köppen_post.csv vuotaul_ikir_pri.csv vuotaul_ikir_post.csv vuotaul_wetland_pri.csv vuotaul_wetland_post.csv
	cat vuotaulukot/*_pri_*.csv > vuotaul_pri.csv
	cat vuotaulukot/*_post_*.csv > vuotaul_post.csv

vuotaul_latex.out: vuotaul_latex.c #vuotaul_yleinen.target
	gcc vuotaul_latex.c -o $@ -g -Wall -O${opt} -DKOSTEIKKO=${kosteikko} -DKOST_KAHTIA=${kost_kahtia}

vuotaul_csv: vuotaul_latex.out
	./vuotaul_latex.out

FT2kaudet.out: FT2kaudet.c
	gcc -Wall -O3 -o $@ FT2kaudet.c `pkg-config --libs nctietue`

kaudet1.nc: FT2kaudet.out
	./FT2kaudet.out ../FT1x1_1.nc $@

kaudet2.nc: FT2kaudet.out
	./FT2kaudet.out ../FT1x1_2.nc $@

kaudet12: kaudet1.nc kaudet2.nc

kausista_pituudet.out: kausista_pituudet.c
	gcc -Wall -g -Og -o $@ kausista_pituudet.c `pkg-config --libs nctietue` -lm

kausien_pituudet1.nc: kausista_pituudet.out kaudet1.nc
	./kausista_pituudet.out kaudet1.nc $@

kausien_pituudet2.nc: kausista_pituudet.out kaudet2.nc
	./kausista_pituudet.out kaudet2.nc $@

kausien_pituudet: kausien_pituudet1.nc kausien_pituudet2.nc

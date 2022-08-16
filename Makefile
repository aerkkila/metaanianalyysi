tehoisa_kosteikko.out: tehoisa_kosteikko.c
	gcc -Wall tehoisa_kosteikko.c -o $@ `pkg-config --libs nctietue2 gsl` -g -Og

vuojakaumadata.out: vuojakaumadata.c
	gcc -Wall vuojakaumadata.c -o $@ `pkg-config --libs nctietue2 gsl` -lm -g -O3
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

vuojakaumadata_vuosittain.out: vuojakaumadata_vuosittain.c
	gcc -Wall vuojakaumadata_vuosittain.c -o $@ `pkg-config --libs nctietue2 gsl` -lm -g -O3
vuojakauma_vuosittain_ikir: vuojakaumadata_vuosittain.out
	./vuojakaumadata_vuosittain.out ikir post
vuojakauma_vuosittain_köpp: vuojakaumadata_vuosittain.out
	./vuojakaumadata_vuosittain.out köpp post
vuojakauma_vuosittain_wetl: vuojakaumadata_vuosittain.out
	./vuojakaumadata_vuosittain.out wetl post
vuojakaumadata_vuosittain.target: vuojakauma_vuosittain_ikir vuojakauma_vuosittain_köpp vuojakauma_vuosittain_wetl
	cat vuojakaumadata_vuosittain/summat_ft[21]*.csv > summat_vuosittain_kaikki.csv
	cat vuojakaumadata_vuosittain/summat_ft2*_post*.csv > summat_vuosittain.csv

vuojakauma_vuosittain_pri_ikir: vuojakaumadata_vuosittain.out
	./vuojakaumadata_vuosittain.out ikir pri
vuojakauma_vuosittain_pri_köpp: vuojakaumadata_vuosittain.out
	./vuojakaumadata_vuosittain.out köpp pri
vuojakauma_vuosittain_pri_wetl: vuojakaumadata_vuosittain.out
	./vuojakaumadata_vuosittain.out wetl pri
vuojakaumadata_vuosittain_pri.target: vuojakauma_vuosittain_pri_ikir vuojakauma_vuosittain_pri_köpp vuojakauma_vuosittain_pri_wetl


wetlandsumma.out: wetlandsumma.c
	gcc -Wall wetlandsumma.c -o $@ `pkg-config --libs nctietue` -lm -O3

vuotaul_yleinen.out: vuotaul_yleinen.c
	gcc -Wall -g -O3 vuotaul_yleinen.c -o $@ `pkg-config --libs nctietue2` -lm

vuotaul_wetland_post.csv: vuotaul_yleinen.out
	./vuotaul_yleinen.out wetl post
	cat vuotaulukot/wetlandvuo_post*.csv > vuotaul_wetland_post.csv

vuotaul_wetland_pri.csv: vuotaul_yleinen.out
	./vuotaul_yleinen.out wetl pri
	cat vuotaulukot/wetlandvuo_pri*.csv > vuotaul_wetland_pri.csv

vuotaul_köppen_post.csv: vuotaul_yleinen.out
	./vuotaul_yleinen.out köpp post
	cat vuotaulukot/köppenvuo_post*csv > vuotaul_köppen_post.csv

vuotaul_köppen_pri.csv: vuotaul_yleinen.out
	./vuotaul_yleinen.out köpp pri
	cat vuotaulukot/köppenvuo_pri*csv > vuotaul_köppen_pri.csv

vuotaul_ikir_post.csv: vuotaul_yleinen.out
	./vuotaul_yleinen.out ikir post
	cat vuotaulukot/ikirvuo_post*csv > vuotaul_ikir_post.csv

vuotaul_ikir_pri.csv: vuotaul_yleinen.out
	./vuotaul_yleinen.out ikir pri
	cat vuotaulukot/ikirvuo_pri*csv > vuotaul_ikir_pri.csv

vuotaul_yleinen.target: vuotaul_köppen_pri.csv vuotaul_köppen_post.csv vuotaul_ikir_pri.csv vuotaul_ikir_post.csv vuotaul_wetland_pri.csv vuotaul_wetland_post.csv

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

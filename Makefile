wetlandsumma.out: wetlandsumma.c
	gcc -Wall wetlandsumma.c -o $@ `pkg-config --libs nctietue` -lm -O3

vuotaul_yleinen.out: vuotaul_yleinen.c
	gcc -Wall -g -O2 vuotaul_yleinen.c -o $@ `pkg-config --libs nctietue2` -lm

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

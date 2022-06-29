wetlandsumma.out: wetlandsumma.c
	gcc -Wall wetlandsumma.c -o $@ `pkg-config --libs nctietue` -lm -O3

vuotaul_wetland.out: vuotaul_wetland.c
	gcc -Wall -g -O2 vuotaul_wetland.c -o $@ `pkg-config --libs nctietue` -lm

vuotaul_wetland_post.csv: vuotaul_wetland.out
	./vuotaul_wetland.out 0 post
	./vuotaul_wetland.out 1 post
	./vuotaul_wetland.out 2 post
	cat vuotaulukot/wetlandvuo_post*.csv > vuotaul_wetland_post.csv

vuotaul_wetland_pri.csv: vuotaul_wetland.out
	./vuotaul_wetland.out 0 pri
	./vuotaul_wetland.out 1 pri
	./vuotaul_wetland.out 2 pri
	cat vuotaulukot/wetlandvuo_pri*.csv > vuotaul_wetland_pri.csv

vuotaul_wetland.target: vuotaul_wetland_pri.csv vuotaul_wetland_post.csv

vuotaul_binjako.out: vuotaul_binjako.c
	gcc -Wall -g -Og vuotaul_binjako.c -o $@ `pkg-config --libs nctietue` -lm

vuotaul_köppen_pri.csv: vuotaul_binjako.out
	./vuotaul_binjako.out köpp pri
	cat vuotaulukot/köppenvuo_pri*csv > vuotaul_köppen_pri.csv

vuotaul_köppen_post.csv: vuotaul_binjako.out
	./vuotaul_binjako.out köpp post
	cat vuotaulukot/köppenvuo_post*csv > vuotaul_köppen_post.csv

vuotaul_ikir_pri.csv: vuotaul_binjako.out
	./vuotaul_binjako.out ikir pri
	cat vuotaulukot/ikirvuo_pri*csv > vuotaul_ikir_pri.csv

vuotaul_ikir_post.csv: vuotaul_binjako.out
	./vuotaul_binjako.out ikir post
	cat vuotaulukot/ikirvuo_post*csv > vuotaul_ikir_post.csv

vuotaul_binjako.target: vuotaul_köppen_pri.csv vuotaul_köppen_post.csv vuotaul_ikir_pri.csv vuotaul_ikir_post.csv

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

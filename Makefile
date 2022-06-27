wetlandsumma.out: wetlandsumma.c
	gcc -Wall wetlandsumma.c -o $@ `pkg-config --libs nctietue` -lm -O3

wetlandvuotaul.out: wetlandvuotaul.c
	gcc -Wall -g -O2 wetlandvuotaul.c -o $@ `pkg-config --libs nctietue` -lm

wetlandvuotaul_post.csv: wetlandvuotaul.out
	./wetlandvuotaul.out 0 post
	./wetlandvuotaul.out 1 post
	./wetlandvuotaul.out 2 post
	cat wetlandvuotaulukot/wetlandvuo_post*.csv > wetlandvuotaul_post.csv

wetlandvuotaul_pri.csv: wetlandvuotaul.out
	./wetlandvuotaul.out 0 pri
	./wetlandvuotaul.out 1 pri
	./wetlandvuotaul.out 2 pri
	cat wetlandvuotaulukot/wetlandvuo_pri*.csv > wetlandvuotaul_pri.csv

wetlandvuotaul.target: wetlandvuotaul_pri.csv wetlandvuotaul_post.csv

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

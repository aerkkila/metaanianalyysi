wetlandsumma.out: wetlandsumma.c
	gcc -Wall wetlandsumma.c -o $@ `pkg-config --libs nctietue` -lm -O3

wetlandvuotaul.out: wetlandvuotaul.c
	gcc -Wall -g -O2 wetlandvuotaul.c -o $@ `pkg-config --libs nctietue` -lm

wetlandvuotaul.csv: wetlandvuotaul.out
	./wetlandvuotaul.out 0
	./wetlandvuotaul.out 1
	./wetlandvuotaul.out 2
	cat wetlandvuotaulukot/*.csv > wetlandvuotaul.csv

wetlandvuosumma: wetlandvuosumma.csv
	emacs -nw wetlandvuosumma.csv

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

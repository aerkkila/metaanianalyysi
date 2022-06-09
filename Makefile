wetlandsumma.out: wetlandsumma.c
	gcc wetlandsumma.c -o $@ -lnctietue -lSDL2 -lpng -lnetcdf -lm -O3

wetlandvuosumma.out: wetlandvuosumma.c
	gcc -g -Og wetlandvuosumma.c -o $@ -lnctietue -lSDL2 -lpng -lnetcdf -lm

wetlandvuosumma.csv: wetlandvuosumma.out
	./wetlandvuosumma.out

wetlandvuosumma: wetlandvuosumma.csv
	emacs -nw wetlandvuosumma.csv

FT2kaudet.out: FT2kaudet.c
	gcc -g -Og -o $@ FT2kaudet.c -lnctietue -lnetcdf -lpng -lSDL2

kaudet1.nc: FT2kaudet.out
	./FT2kaudet.out ../FT1x1_1.nc $@

kaudet2.nc: FT2kaudet.out
	./FT2kaudet.out ../FT1x1_2.nc $@

kaudet_uusi: kaudet1.nc kaudet2.nc

kausista_pituudet.out: kausista_pituudet.c
	gcc -g -Og -o $@ kausista_pituudet.c -lnctietue -lnetcdf -lpng -lSDL2

kausien_pituudet1.nc: kausista_pituudet.out kaudet1.nc
	./kausista_pituudet.out kaudet1.nc $@

kausien_pituudet2.nc: kausista_pituudet.out kaudet2.nc
	./kausista_pituudet.out kaudet2.nc $@

kausien_pituudet: kausien_pituudet1.nc kausien_pituudet2.nc

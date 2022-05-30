wetlandsumma.out: wetlandsumma.c
	gcc wetlandsumma.c -o $@ -lnctietue -lSDL2 -lpng -lnetcdf -lm -O3

wetlandvuosumma.out: wetlandvuosumma.c
	gcc -g wetlandvuosumma.c -o $@ -lnctietue -lSDL2 -lpng -lnetcdf -lm

wetlandvuosumma.csv: wetlandvuosumma.out
	./wetlandvuosumma.out

näytä: wetlandvuosumma.csv
	emacs -nw wetlandvuosumma.csv

all: FT1x1.nc FT1x1_2.nc

koordind.out: koordind.c
	 gcc -O3 koordind.c -o koordind.out -lnctietue -lSDL2 -lpng -lnetcdf

koordind.bin: koordind.out
	./koordind.out

muunna.out: muunna.c
	 gcc -g muunna.c -o muunna.out -lnctietue -lSDL2 -lpng -lnetcdf

FT1x1.nc: muunna.out koordind.bin
	./muunna.out

FT1x1_2.nc: muunna.out koordind.bin
	./muunna.out 2

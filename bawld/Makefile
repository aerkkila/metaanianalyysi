all: bawld.nc

lisäluokat.out: lisäluokat.c
	gcc -o $@ $< -g -Wall `pkg-config --libs nctietue2`

bawld.out: bawld.c bawldtunnisteet.h
	gcc -o $@ $< -g -Wall -lshp -lnetcdf -lm -lproj -pthread -Ofast

bawld.nc: bawld.out lisäluokat.out
	./bawld.out -j 4
	./lisäluokat.out bawld.nc

all: bawld.nc
bawld.nc: data bawld.out lisäluokat.out
	./bawld.out -j 4
	./lisäluokat.out bawld.nc

lisäluokat.out: lisäluokat.c
	gcc -o $@ $< -g -Wall -lnctietue3

bawld.out: bawld.c bawldtunnisteet.h
	gcc -o $@ $< -g -Wall -lshp -lnetcdf -lm -lproj -pthread -Ofast

data:
	if [ ! -e data.zip ]; then curl -o data.zip https://arcticdata.io/metacat/d1/mn/v2/object/urn%3Auuid%3Af623f043-d755-4c3a-bf54-cb8d36b0bda3; fi
	unzip -d data data.zip

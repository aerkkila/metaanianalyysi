all: ikirdata.nc

raaka: lataa.sh
	./$<

muunnos.out: luo_muunnos.c muunnosalue.h
	gcc -Wall -Wno-builtin-declaration-mismatch $< -o $@ -lnctietue3 -lproj -g

osuus.out: osuus.c muunnosalue.h
	gcc -Wall $< -o $@ -lnctietue3 -lnetcdf -Ofast

muunnosindeksit.bin: muunnos.out raaka
	./$<

ikirdata.nc: osuus.out muunnosindeksit.bin raaka
	./$<

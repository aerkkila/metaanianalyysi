all: landmask.nc

ne_10m_land.zip:
	curl -LO https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/physical/ne_10m_land.zip

ne_10m_lakes.zip:
	curl -LO https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/physical/ne_10m_lakes.zip

ne_10m_land: ne_10m_land.zip
	mkdir -p $@
	unzip -d $@ $<

ne_10m_lakes: ne_10m_lakes.zip
	mkdir -p $@
	unzip -d $@ $<

muunnosalue.h:
	ln -s ../$@ $@

landmask.out: landmask.c muunnosalue.h
	gcc -Wall -g -o $@ $< -lshp -lnetcdf -lm -lproj -lnctietue3 -Ofast

landmask.nc: landmask.out ne_10m_land
	./landmask.out

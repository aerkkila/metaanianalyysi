muunna_shapefile: muunna_shapefile.c köppentunnisteet.c
	gcc -o muunna_shapefile muunna_shapefile.c -lshp -lnetcdf -lm -pthread -Ofast

muun_shp_debug: muunna_shapefile.c köppentunnisteet.c
	gcc -o muun_shp_debug muunna_shapefile.c -lshp -lnetcdf -lm -pthread -g

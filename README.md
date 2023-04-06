## Codes used to write a publication about environmental methane drivers.
Most C-codes in this repository use this library github.com/aerkkila/nctietue3.git to handle netcdf files.
They are compiled with argument -lnctietue3.

1. **Following codes create the data that rest of the codes need. These may read external data which is not in this repository.**
   - **bawld/bawld.c** &rarr; BAWLD1x1<area>.nc \
	   BAWLD classification
   - **ikirdata<area>.py** &rarr; ikirdata<area>.nc, ikirdata<area>.npy \
	   permafrost classification
   - **smoskoodit/kaudet<area>.c* &rarr; kaudet<area>.nc, kausien_päivät.nc, kausien_päivät_int16.nc \
	   ongoing season (kaudet<area>.nc) and season start and end dates (kausien_päivät.nc)
   - **pintaalat<area>.py** &rarr; pintaalat<area>.npy \
	   a simple code: calculate area of each grid cell
   - **köppen.c** &rarr; köppen1x1maski<area>.nc \
	   Reads shapefile of köppen classification and outputs netcdf file.
   - **köppenmaski<area>.py** &rarr; köppenmaski<area>.npy, köppenmaski<area>.txt \
	   Climate class for each grid cell.
   - **pintaalat<area>.c** &rarr pintaalat<area>.h, pintaalat<area>.py \
   	   Creates surface areas on different latitudes using proj-library. \
	   Outputs the array as C and python code which can be included into C or Python codes.

2. **Following codes process data further from part 1** These make the hard work.
   - **vuojakaumadata<area>.c** &rarr; vuojakaumadata/\*.bin, vuojakaumadata/vuosittain/\*.bin, vuojakaumadata/vuosittain/*.csv \
	   Calculate distribution of methane fluxes in different areas and seasons. \
	   If compiled with -DVUODET_ERIKSEEN=1 calculates all years separately \
	   and makes csv-tables of yearly seasonal emission sums.
   - **päivät_vuosittain.c** &rarr; kausidata2301/* \
	   Like vuojakaumadata<area>.c but for season start days
	   which are read straight from kausien_päivät.nc and therefore is much simpler.
   - **vuodata.c** &rarr; vuodata$(yymm)/\*.csv \
	   Calculate average methane fluxes and many other things in different areas and seasons. \
	   This replaces the ugly code in vuotaul_yleinen.c.
   - **wregressio/** \
	   Contains its own readme.

3. **Following codes make final things using the preprocessed data from previous parts.**
   - **bawld_wetlosuuskartta.py** &rarr; bawld_wetlosuuskartta.png \
	   map of wetland subcategories as fraction of total wetland
   - **ikir_metaani_kartta.py** &rarr; ikir_metaani_kartta_['pri','post']\_{prf-class}_{season}_ft[012].png \
	   Season average methane flux on map. Different map for each permafrost region, season and prior/posterior data.
   - **kaudet_laatikko.py** &rarr; kausilaatikko_{season}\_['length','start']\_ikirköpp.png \
	   Boxplot of season start day or length in different climate and permafrost classifications.
   - **aluejaot.py** &rarr; aluejaot.png \
	   Map of used climate, permafrost classification and wetland classifications
   - **yhdistelmäalueet.py** &rarr; yhdistelmäalueet.tex \
	   Latex table about how much climate and permafrost classifications and wetland overlap.
   - **vuotaul_latex.c** &rarr; vuosummat['',_tiivistelmä]_['pri','post']['',_k1].tex \
	   latex table about average fluxes and season part of whole year emission \
	   Reads vuotaulukot/\*.csv.
   - **lattaul.c** &rarr; lattaul.tex
	   Latex table about average latitudes of different areas.
   - **vuojakaumalaatikko<area>.py** &rarr; vuojakaumalaatikko_['pri','post']_[01].png \
	   boxplot of methane fluxes in different areas and seasons
   - **vuojakaumalaatikko_vuosittain.py** &rarr; jakaumat_vuosittain/*, vuosittaisvaihtelu.tex, kaudet_vuosittain/*
	   Yearly boxplots of methane fluxex in different areas and seasons. \
	   Years in same figure, areas and seasons separately. \
	   Makes also a table about relative standard deviation of annual averages. \
	   Can be run with argument päivä to make similar figures of season start days.

**Other**
   - **vanhoja**, **puolivanhoja**, **säiliö** \
   	old codes which could have been removed but has been archived instead

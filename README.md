## Codes used to analyze methane flux modelling results
Most C-codes in this repository use this library github.com/aerkkila/nctietue2.git to handle netcdf files.
They should be compiled with argument \`pkg-config --libs nctietue2\`

1. **Following codes create the data that rest of the codes need. These may read external data which is not in this repository.**
   - **aluemaski<area>.py** &rarr; aluemaski<area>.nc \
	   a simple code: mask of area that should be used
   - **BAWLD<area>.py** &rarr; BAWLD05x05<area>.nc, BAWLD1x1<area>.nc \
	   BAWLD classification
   - **ikirdata<area>.py** &rarr; ikirdata<area>.nc, ikirdata<area>.npy \
	   permafrost classification
   - **kaudet<area>.py** &rarr; kaudet[012]<area>.nc, kausien_pituudet[012]<area>.nc \
	   season classification (kaudet<area>.nc) \
	   season lengths and start dates (kausien_pituudet<area>.nc) \
	   number is for three different freeze/thaw datasets
   - **pintaalat<area>.py** &rarr; pintaalat<area>.npy \
	   a simple code: calculate area of each grid cell
   - **muunna_shapefile.c** &rarr; köppen1x1maski<area>.nc \
	   Reads shapefile of köppen classification and outputs netcdf file.
	   Works also as a general converter from shapefile to netcdf.
   - **yleiskosteikko<area>.c** &rarr; yleiskosteikko<area>.nc \
	   Reads three wetland classes used in the model and creates a combination of them that that best explains the modelled flux.

2. **Following codes process data further from part 1**
   - **köppenmaski<area>.py** &rarr; köppenmaski<area>.npy, köppenmaski<area>.txt \
	   Climate class for each grid cell.
   - **vuojakaumadata<area>.c** &rarr; vuojakaumadata/\*.bin, vuojakaumadata/vuosittain/\*.bin, vuojakaumadata/vuosittain/*.csv \
	   Calculate distribution of methane fluxes in different areas and seasons. \
	   If compiled with -DVUODET_ERIKSEEN=1 calculates all years separately \
	   and makes csv-tables of yearly seasonal emission sums.
   - **kertajakaumadata<area>.c** &rarr; kausijakaumadata/* \
	   Like vuojakaumadata<area>.c but for season start days or similar with only 1 value per season in a cell. \
	   Only tested with -DVUODET_ERIKSEEN=1.
   - **vuotaul_yleinen.c** &rarr; vuotaulukot/\*.csv \
	   Calculate average methane fluxes in different areas and seasons.

3. **Following codes make final things using the preprocessed data from previous parts.**
   - **bawld_wetlosuuskartta.py** &rarr; bawld_wetlosuuskartta.png \
	   map of wetland subcategories as fraction of total wetland
   - **ikir_alkuloppu.py** &rarr; ikir[0123]_{season}_start.png \
	   histogram of frequency of season start dates in different permafrost regions
   - **ikir_metaani_kartta.py** &rarr; ikir_metaani_kartta_['pri','post']\_{prf-class}_{season}_ft[012].png \
	   Season average methane flux on map. Different map for each permafrost region, season and prior/posterior data.
   - **jäätym_histog.py** &rarr; ikir[0123]\_freezing_['start','end','length']_ft[012]<area>.png (deprecated?) \
	   like ikir_alkuloppu.py but only freezing period including its length and different ft-data
   - **jäätym_laatikko.py** &rarr; freezing-['start','end','length']_['ikir','kopp']_laatikko<area>.png (deprecated?) \
	   boxplot of freezing period dates in different permafrost or climate areas and with different ft-data
   - **kaudet_laatikko.py** &rarr; kausilaatikko_{season}\_['length','start']\_ikirköpp.png \
	   Boxplot of season start day or length in different climate and permafrost classifications.
   - **köppikir_kartta.py** &rarr; ['köppen','ikir']\_kartta.png \
	   Map of used climate or permafrost classification
   - **köppikir_taulukko.py** &rarr; köppikir<area>.tex \
	   Latex table about how much climate and permafrost classifications overlap
   - **prf_kasvil_taulukko.py** &rarr; prf_kasvil_taulukko_['1000km2','prosentti'].csv \
	   csv-table about how much permafrost region and BAWLD classes overlap (*has to be updated*)
   - **vuotaul_latex.c** &rarr; vuosummat['',_tiivistelmä]_['pri','post']['',_k1].tex \
	   latex table about average fluxes and season part of whole year emission
   - **vuojakaumalaatikko<area>.py** &rarr; vuojakaumalaatikko_['pri','post']_[01].png \
	   boxplot of methane fluxes in different areas and seasons
   - **vuojakaumalaatikko_vuosittain.py** &rarr; jakaumat_vuosittain/*, vuosittaisvaihtelu.tex, kaudet_vuosittain/*
	   Yearly boxplots of methane fluxex in different areas and seasons. \
	   Years in same figure, areas and seasons separately. \
	   Makes also a table about relative standard deviation of annual averages.
	   Can be run with argument päivä to make similar figures of season start days.

**Other**
- **köppenpintaalat<area>.c** areas of climate classes

**Undocumented** \
FT2kaudet<area>.c, onko_kausi_yhtenäinen.c wetlandsumma<area>.c interpoloi_flux1x1.py, vuojakauman_piirtäjä.py, [Wwx]\*.py

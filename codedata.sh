#!/bin/sh

k0=$HOME/codes_and_data
k1=$HOME/codes_and_small_data
[ "$1" = 'rm' ] && rm -rf $k0 $k1
kansio=$k0
mkdir -p $kansio/kuvia

kansio=$k0/nctietue3
mkdir -p $kansio
cd $kansio
git -C ~/nctietue3 archive master | tar -x -C $kansio
sed -i "s/^CFLAGS\(\W*=.*\)$/CFLAGS\1 -O2/" config.mk
cd -

kansio=$k0/article_source
mkdir -p $kansio
git -C ~/metaanijulkaisu archive master | tar -x -C $kansio
( cd $kansio; latexpand --keep-includes template.tex |cat -s > tmp.tex; mv tmp.tex template.tex ) # poistaa kommentit

kansio=$k0
cp -l \
    laatikkokuvaaja.py \
    luokat.py \
    LICENSE \
    $kansio

cp -lr \
    ikirdata.nc \
    köppen1x1maski.nc \
    köppenmaski.npy \
    köppenmaski.txt \
    aluemaski.nc \
    pintaalat.py \
    pintaalat.h \
    vuodata \
    vuojakaumadata \
    kausien_päivät.nc \
    kausien_päivät_int16.nc \
    BAWLD1x1.nc \
    flux1x1.nc \
    vuosijainnit.nc \
    $kansio

rm -rf $kansio/vuodata/vuosittain
rm -rf $kansio/vuojakaumadata/vuosittain

nimet0=
nimet1=
kopioi() {
    set $nimet1
    for a in $nimet0; do
	cp $a $kansio/$1
	shift
    done
}

nimet0='
aluejaot.py
kaudet_laatikko.py
vuojakaumat.py
vuosijainnit.py
ttesti_luokat.py
ttesti.py
'
nimet1='
fig01.py
fig02,03.py
fig04,05.py
fig06.py
ttest_categ.py
ttest_areas.py
'
kopioi

nimet0='
yhdistelmäalueet.py
lattaul.c
vuotaul_latex.c
'
nimet1='
table01.py
table02.c
latextable.c
'
kopioi

cat >$k0/table03,A2.sh <<-EOF
	#!/bin/sh
	gcc latextable.c -O2
	./a.out
	mv vuosummat_post.tex table03.tex
	mv vuosummat_pri.tex tableA2.tex
EOF
cat >$k0/table04,A3.sh <<-EOF
	#!/bin/sh
	gcc latextable.c -DKOSTEIKKO -O2
	./a.out
	mv vuosummat_post_k1.tex table04.tex
	mv vuosummat_pri_k1.tex tableA3.tex
EOF
cat >$k0/table05,A4.sh <<-EOF
	#!/bin/sh
	gcc latextable.c -DLAUHKEUS=2 -O2
	./a.out
	mv vuosummat_lauhkea_pri.tex tableA4.tex
	mv vuosummat_lauhkea.tex table05.tex
EOF
cat >$k0/tableA1,A5.sh <<-EOF
	#!/bin/sh
	gcc latextable.c -DLAUHKEUS=1 -O2
	./a.out
	mv vuosummat_epälauhkea.tex tableA1.tex
	mv vuosummat_epälauhkea_pri.tex tableA5.tex
EOF

kansio=$k0/fig07,AppendixB
mkdir -p $kansio
cd wregressio
cp laske.sh Makefile virhepalkit.pyx setup.py virhepalkit.py piirrä.py taulukko_rajat.c wregressio.c yhdistä.sh $kansio
cp -r tallenteet sovitteet.txt $kansio
cd ..
cat >$kansio/README <<EOF
By default, saved figures go to ../kuvia.
Everything in this directory can be run automatically using laske.sh
in which case, the rest of this file is not needed to read.

make compiles wregressio.c into wregressio.out and virhepalkit.pyx into shared object
wregressio.out conducts the linear regression and calls piirrä.py to draw the figures in Appendix B.
Command line arguments to wregressio.out include:
    -k [0123] // which season is calculated
    -s        // save: replaces stdout with a file and changes output a little
    -p -s     // passes argument -s to python program piirrä.py to save the drawn figures
    -i        // get results for cold wetland areas instead of warm

After wregressio.out one should run 'cat tallenteet/* > sovitteet.txt' to combine the files that wregressio.out created.

Thereafter one can run the rest of codes:
virhepalkit.py to create figure 7. That uses virhepalkit.pyx to read sovitteet.txt.
taulukko_rajat.c to create table B1. This can be compiled normally without additional arguments.
yhdistä.sh to combine single figures into panels.
EOF

kansio=$k0/create_ikirdata
mkdir -p $kansio
git -C create_ikirdata archive master | tar -x -C $kansio

kansio=$k0/create_köppen
mkdir -p $kansio
cp köppenmaski.py $kansio
kansio=$kansio/create_köppen1x1maski
mkdir -p $kansio
cp köppen.c köppentunnisteet.h $kansio
cat >$kansio/Makefile <<EOF
all: köppen1x1maski.nc

köppen1x1maski.nc: köppen.out köppen_shp
	./\$<

köppen.out: köppen.c köppentunnisteet.h
	gcc -o \$@ -Ofast ./\$< -lnetcdf -lshp -pthread -lm

1976-2000_GIS.zip:
	curl -LO https://koeppen-geiger.vu-wien.ac.at/data/1976-2000_GIS.zip

köppen_shp: 1976-2000_GIS.zip
	mkdir -p köppen_shp
	unzip -d köppen_shp 1976-2000_GIS.zip
EOF

cat >$kansio/README <<EOF
By running make, the data are automatically downloaded from the following url:
https://koeppen-geiger.vu-wien.ac.at/data/1976-2000_GIS.zip
If that does not work, try to download that using a web browser and thereafter, run make.

köppen.c reads the shapefile and outputs netcdf file.
Shapelib and netcdf have to be installed.

Reference:
Kottek, M., J. Grieser, C. Beck, B. Rudolf, and F. Rubel, 2006: World Map of the Köppen-Geiger climate classification updated. Meteorol. Z., 15, 259-263. DOI: 10.1127/0941-2948/2006/0130.
EOF

kansio=$k0/create_pintaalat
mkdir -p $kansio
cp pintaalat.c $kansio
cat >$kansio/README <<EOF
This code (pintaalat.c) creates a C-header and a python file
with surface areas on a grid cell in each used latitude.
They are included into all of the codes which deal with surface areas.
Compile with -lproj -lnctietue3.
EOF

kansio=$k0/create_vuodata
mkdir -p $kansio
cp vuodata.c $kansio
cat >$kansio/README <<EOF
This code (vuodata.c) calculates average metahne fluxes and emissions in different areas and seasens.
Those are read by the codes which create the published tables.
All used data are created by running make.

Files with _k1.csv in the end are created using only wetland area.
Files with _k0.csv in the end are created using all area.
In the wetland files, _k0 does not mean anything.
EOF

cat >$kansio/Makefile <<EOF
all: vt.target vtpri.target

vuodata.out: vuodata.c
	gcc -Wall -o \$@ \$< -lm -lnctietue3 -Ofast

vt.target: vk vw vi vt vkk vik vwm vwp
vk: vuodata.out
	./\$< köpp \$(argv)
vi: vuodata.out
	./\$< ikir \$(argv)
vw: vuodata.out
	./\$< wetl \$(argv)
vt: vuodata.out
	./\$< totl \$(argv)
vkk: vuodata.out
	./\$< köpp kosteikko \$(argv)
vik: vuodata.out
	./\$< ikir kosteikko \$(argv)
vwm: vuodata.out
	./\$< wetl temperate \$(argv)
vwp: vuodata.out
	./\$< wetl nontemperate \$(argv)

vtpri.target: vkpri vwpri vipri vtpri vkkpri vikpri vwmpri vwppri
vkpri: vuodata.out
	./\$< köpp pri \$(argv)
vipri: vuodata.out
	./\$< ikir pri \$(argv)
vwpri: vuodata.out
	./\$< wetl pri \$(argv)
vtpri: vuodata.out
	./\$< totl pri \$(argv)
vkkpri: vuodata.out
	./\$< köpp kosteikko pri \$(argv)
vikpri: vuodata.out
	./\$< ikir kosteikko pri \$(argv)
vwmpri: vuodata.out
	./\$< wetl temperate pri \$(argv)
vwppri: vuodata.out
	./\$< wetl nontemperate pri \$(argv)
EOF

kansio=$k0/create_vuosijainnit
mkdir -p $kansio
cp vuosijainnit.c $kansio
cat >$kansio/Makefile <<EOF
all: vuosijainnit.nc
vuosijainnit.out: vuosijainnit.c
	gcc -Wall -o \$@ \$< -lnctietue3 -lm -Ofast -g
vuosijainnit.nc: vuosijainnit.out
	./\$<
EOF

kansio=$k0/create_vuojakaumadata
mkdir -p $kansio
cp vuojakaumadata.c $kansio
cat >$kansio/README <<EOF
This code, vuojakaumadata.c, calculates the cumulative probability distribution of methane fluxes on different areas and seasons.
Created directory vuojakaumadata/kost contains results for wetland areas only.
All data are created by running make.
The created data are needed by the code which draws boxplots about methane emission distributions.
EOF
cat >$kansio/Makefile <<EOF
all: vuojakauma_ikir vuojakauma_köpp vuojakauma_wetl ipk kpk

vuojakaumadata.out: vuojakaumadata.c
	gcc -Wall \$< -o \$@ \`pkg-config --libs gsl\` -lnctietue3 -g -O3

vuojakauma_ikir: vuojakaumadata.out
	./\$< ikir post
vuojakauma_köpp: vuojakaumadata.out
	./\$< köpp post
vuojakauma_wetl: vuojakaumadata.out
	./\$< wetl post
ipk: vuojakaumadata.out
	./\$< ikir post kost
kpk: vuojakaumadata.out
	./\$< köpp post kost
EOF

kansio=$k0/create_kausien_päivät
mkdir -p $kansio/ft_percent
a=/home/aerkkila/smos_uusi/
cp $a/kaudet.c $kansio/kausien_päivät.c
cp -l $HOME/smos_uusi/ft_percent/frozen_percent_pixel_*.nc $kansio/ft_percent
cp -l $HOME/smos_uusi/ft_percent/partly_frozen_percent_pixel_*.nc $kansio/ft_percent
kansio=$kansio/create_ft_percent
mkdir -p $kansio
cp $a/ft_percents_pixel_ease.c $kansio
cp -l $a/EASE_2_l*.nc $kansio
#cp -l $HOME/smos_uusi/FT_720_*.nc $kansio/data # isoja
cat >$kansio/README <<EOF
This code, ft_percent_pixel_ease.c, is used to convert from EASE2 coordinates to latlon coordinates
and to calculate the fraction of each FT category (../ft_percent/*) in latlon grid cells.

The code reads annual data files named as FT_720_yyyy.nc
which must be first created using the codes in create_data.
EOF

kansio=$kansio/create_data
mkdir -p $kansio
cp $HOME/smos_uusi/yhdistä_vuosittain.c $kansio
cat >$kansio/README <<EOF
This is a code that was used to combine each year into one file
and fill missing dates with values read from previous existing date.

Data can be downloaded from 
https://nsdc.fmi.fi/services/SMOSService/
(Rautiainen, K., Parkkinen, T., Lemmetyinen, J., Schwank, M., Wiesmann, A., Ikonen, J., Derksen, C., Davydov, S., Davydova, A., Boike, J., Langer, M., Drusch, M., and Pulliainen, J. 2016. SMOS prototype algorithm for detecting autumn soil freezing, Remote Sensing of Environment, 180, 346-360. DOI: 10.1016/j.rse.2016.01.012).

Downloaded data files should be in netcdf form and renamed as FT_yyyymmdd.nc.
Something like 'mmv "W_XX-ESA,SMOS,NH_25KM_EASE2_*_[or]_*.nc" FT_#1.nc' should rename the files correctly.
EOF

kansio=$k0/create_BAWLD1x1
mkdir -p $kansio
cp bawld/*.[ch] bawld/Makefile $kansio
cat > $kansio/README <<EOF
Data is created by running make.

Used data is BAWLD_V1___Shapefile.zip from https://doi.org/10.18739/A2C824F9X (Olefeldt et al., 2021) which should be extracted into directory called data.
Makefile downloads and extracts it automatically.

Reference:
Olefeldt, D., Hovemyr, M., Kuhn, M. A., Bastviken, D., Bohn, T. J., Connolly, J., Crill, P., Euskirchen, E. S., Finkelstein, S. A., Genet, H., Grosse, G., Harris, L. I., Heffernan, L., Helbig, M., Hugelius, G., Hutchins, R., Juutinen, S., Lara, M. J., Malhotra, A., Manies, K., McGuire, A. D., Natali, S. M., O'Donnell, J. A., Parmentier, F.-J. W., Räsänen, A., Schädel, C., Sonnentag, O., Strack, M., Tank, S. E., Treat, C., Varner, R. K., Virtanen, T., Warren, R. K., and Watts, J. D.: The Boreal–Arctic Wetland and Lake Dataset (BAWLD), Earth Syst. Sci. Data, 13, 5127–5149, https://doi.org/10.5194/essd-13-5127-2021, 2021.
EOF

cat > $k0/create_links.sh <<EOF
#!/bin/sh
( cd create_köppen;         ln -s ../köppen1x1maski.nc . )
( cd create_köppen/create_köppen1x1maski; ln -s ../../aluemaski.nc . )
( cd create_vuodata;        ln -s ../köppenmaski.txt ../ikirdata.nc ../BAWLD1x1.nc ../flux1x1.nc ../kausien_päivät_int16.nc ../pintaalat.h ../aluemaski.nc . )
( cd create_vuojakaumadata; ln -s ../köppenmaski.txt ../ikirdata.nc ../BAWLD1x1.nc ../flux1x1.nc ../kausien_päivät.nc ../pintaalat.h ../aluemaski.nc . )
( cd create_kausien_päivät; ln -s ../aluemaski.nc . )
( cd create_BAWLD1x1;       ln -s ../aluemaski.nc . )
( cd create_ikirdata;       ln -s ../luokat.py . )
( cd create_vuosijainnit;   ln -s ../aluemaski.nc ../flux1x1.nc ../BAWLD1x1.nc ../kausien_päivät_int16.nc ../pintaalat.h . )
( cd create_pintaalat;      ln -s ../aluemaski.nc . )
EOF
for f in `find $k0 -type f`; do head -1 $f | grep -q "^#!" && chmod 755 $f; done # suoritettaviin tiedostoihin suoritusoikeus

cat > $k0/README.rst <<EOF
=======
License
=======
These codes are under GPL3 license. They can be freely edited and shared as long as the same license is used.
See file called LICENSE for more information.

============================
Installation and compilation
============================
The codes work at least on Linux. Many of the C-codes and shell scripts are likely to work only on Unix-like operating systems.
It is necessary to run create_links.sh before attempting to run most codes elsewhere than in this root directory.
It is also necessary to install nctietue3-library (see next paragraph) before running some of the C-codes.

To install nctietue3-library, go to nctietue3 directory which is included here and then it can be installed normally with:
>>> make
>>> make install # as root
To remove the library, run:
>>> make uninstall # as root
To install without root privilidges, change variable 'prefix' in config.mk to \$HOME/.local.

If nctietue3 was installed without root privilidges to \$HOME/.local,
one may have to edit the C-codes replacing '#include <nctietue3.h>' with '#include "\$HOME/.local/include/nctietue3.h"'.
or pass argument '-I/\$HOME/.local/include' to the compiler.

If neither a README-file nor a Makefile is given for a C-file, default to compiling with:
>>> gcc file.c -O2
If necessary, add '-lnctietue3'.
If a Makefile is given, compile with:
>>> make

Possible issues:
----------------
Optimization level -Ofast cannot be used in vuojakaumadata.c due to -ffinite-math-only optimization.

Most C codes use non-ascii utf8 characters in variable names
which old compiler versions cannot compile (for gcc, version < 10.1).
Also old Python versions may not work due to utf8 variable names.

Some of the terminal outputs contain ansi escape sequences.
If the terminal does not support them, the output will look different than intended.

=====
Usage
=====
The root directory contains all codes that make the final results used in the article.
Codes needed to create \$data are one level deeper in directory called create_\$data.

By default, those Python codes that create a figure will show the figures but will not save them.
To save them, run with argument '-s'. The saved figures will go to the directory called 'kuvia'.
A command line program 'gm' (graphicsmagick) should be installed since some of the codes use that to join the created images into a panel after saving them first as separate files.

Statistical significances
-------------------------
Some statistical significances were only mentioned in the text and not shown in any table or figure.
A guide to calculate those:

"The difference between the sporadic permafrost and non-permafrost regions was significant in summer and in the freezing period (p < 0.001)."
>>> ./ttest_categ.py ikir

"Permafrost bogs had much smaller fluxes -- and was the only class that differed significantly from other classes in summer (p < 0.01)."
"Tundra wetlands had the largest fluxes in both summer and winter. In winter they differed almost significantly from fens (p $\approx$ 0.05)."
>>> ./ttest_categ.py temperate

"Differences between corresponding (same wetland class and season) average fluxes in temperate and warm wetland areas were significant during summer and freezing period (p < 0.01). Marshes in summer were an exception where the difference was not significant."
>>> ./ttest_areas.py

"in a t-test with equal variances and using the whole study area, bogs had significantly (p < 0.05) larger flux than fens in winter."
>>> ./ttest_categ.py sama

File names:
-----------
aluemaski			region mask
ikirdata                        permafrost data
kaudet                          seasons
kausien_päivät			start and end days of seasons
laatikkokuvaaja.py		a module for making whisker plots
pintaalat			surface areas
vuo				flux
vuojakaumadata			flux distribution data
vuotaulukot			flux tables
EOF

# Lopuksi koodit ilman suuria tiedostoja
cp -rl $k0 $k1
rm -r $k1/flux1x1.nc $k1/create_kausien_päivät/ft_percent $k1/create_kausien_päivät/create_ft_percent/EASE*.nc

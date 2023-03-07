#!/bin/sh
kansio=$HOME
#lsblk |grep -q $kansio || { echo ei kovalevyä; exit 1; }

if [ $1 = 'rm' ]; then
    rm -rf ~/codedata
    rm -rf ~/codedata1
fi
kansio=${kansio}/codedata
k0=$kansio
mkdir -p $kansio/kuvia

kansio=$k0/nctietue3
mkdir -p $kansio
cd $kansio
git -C ~/nctietue3 archive master | tar -x -C $kansio
rm -rf .gitignore
echo See the second paragraph at ../README. > README

kansio=$k0/latex_source_of_the_article
mkdir -p $kansio
git -C ~/metaanijulkaisu archive master | tar -x -C $kansio

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
    aluemaski.nc \
    pintaalat.npy \
    vuotaulukot \
    vuojakaumadata \
    kausien_päivät.nc \
    kausien_päivät_int16.nc \
    BAWLD1x1.nc \
    flux1x1.nc \
    vuosijainnit.nc \
    $kansio

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
kosteikkoalueet.py
vuojakaumalaatikko.py
vuosijainnit.py
ttesti_luokat.py
ttesti.py
'
nimet1='
fig01.py
fig02,3.py
fig04.py
fig05,6.py
fig07.py
ttest_wetlcateg.py
ttest_mixed-pure.py
'
kopioi

nimet0='
yhdistelmäalueet.py
lattaul.c
vuotaul_latex.c
vuojakaumalaatikko_vuosittain.py
'
nimet1='
table01.py
table02.c
latextable.c
table08.py
'
kopioi

cat >$k0/table03.sh <<-EOF
	\#!/bin/sh
	gcc latextable.c -O2
	./a.out
EOF
cat >$k0/table04.sh <<-EOF
	\#!/bin/sh
	gcc latextable.c -DKOSTEIKKO -O2
	./a.out
EOF
cat >$k0/table05.sh <<-EOF
	\#!/bin/sh
	gcc latextable.c -DLAUHKEUS=1 -O2
	./a.out
EOF
cat >$k0/table06.sh <<-EOF
	\#!/bin/sh
	gcc latextable.c -DLAUHKEUS=2 -O2
	./a.out
EOF

kansio=$k0/table07+figure08+appendixB
mkdir -p $kansio
cd wregressio
cp laske.sh Makefile virhepalkit.pyx setup.py virhepalkit.py piirrä.py taulukko_rajat.c wregressio.c $kansio
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
virhepalkit.py to create figure 8. That uses virhepalkit.pyx to read sovitteet.txt.
taulukko_rajat.c to create table 7. This can be compiled normally without additional arguments.
EOF

kansio=$k0/create_ikirdata
mkdir -p $kansio
cp ikirdata.py $kansio
cp /media/levy/Tyotiedostot/PermafrostExtent/PRF_Extent20*_1x1.tif $kansio
ed -s $kansio/ikirdata.py <<EOF
/from config import
.d
,s/kansio *=.*/kansio = '.\\/'/
w
q
EOF

kansio=$k0/create_köppen
mkdir -p $kansio
cp köppenmaski.py $kansio
kansio=$kansio/create_köppen1x1maski
mkdir -p $kansio
cp köppen.c köppentunnisteet.h $kansio
cp -r köppen_shp $kansio
cat >$kansio/Makefile <<EOF
all: a.out
	./a.out

a.out:
	gcc -o $@ -O3 köppen.c -lnetcdf -lshp -pthread -lm
EOF

kansio=$k0/create_pintaalat
mkdir -p $kansio
cp pintaalat.py $kansio

kansio=$k0/create_vuodata
mkdir -p $kansio
cp vuodata.c $kansio
cat >$kansio/Makefile <<EOF
all: vt.target vtpri.target vvt.target

vuodata.out: vuodata.c
	gcc -Wall -o \$@ \$< -lm -lnctietue3 -Ofast
vvt.target: vvk vvw vvi vvt vvkk vvik
vvk: vuodata.out
	./\$< vuosittain köpp \$(argv)
vvi: vuodata.out
	./\$< vuosittain ikir \$(argv)
vvw: vuodata.out
	./\$< vuosittain wetl \$(argv)
vvt: vuodata.out
	./\$< vuosittain totl \$(argv)
vvkk: vuodata.out
	./\$< vuosittain köpp kosteikko \$(argv)
vvik: vuodata.out
	./\$< vuosittain ikir kosteikko \$(argv)

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
cat >$kansio/Makefile <<EOF
all: total annually
total: vuojakauma_ikir vuojakauma_köpp vuojakauma_wetl
annually: vuojakauma_vuosittain_ikir vuojakauma_vuosittain_köpp vuojakauma_vuosittain_wetl

vuojakaumadata.out: vuojakaumadata.c
	gcc -Wall \$< -o \$@ \`pkg-config --libs gsl\` -lnctietue3 -g -O3

vuojakauma_ikir: vuojakaumadata.out
	./\$< ikir post
vuojakauma_köpp: vuojakaumadata.out
	./\$< köpp post
vuojakauma_wetl: vuojakaumadata.out
	./\$< wetl post

vuojakaumadata_vuosittain.out: vuojakaumadata.c
	gcc -Wall \$< -o \$@ \`pkg-config --libs gsl\` -lnctietue3 -g -O3 -DVUODET_ERIKSEEN=1
vuojakauma_vuosittain_ikir: vuojakaumadata_vuosittain.out
	./\$< ikir post
vuojakauma_vuosittain_köpp: vuojakaumadata_vuosittain.out
	./\$< köpp post
vuojakauma_vuosittain_wetl: vuojakaumadata_vuosittain.out
	./\$< wetl post
vuojakaumadata_vuosittain.target: vuojakauma_vuosittain_ikir vuojakauma_vuosittain_köpp vuojakauma_vuosittain_wetl
	cat vuojakaumadata/vuosittain/emissio_*_post.csv > emissio_vuosittain.csv
EOF

kansio=$k0/create_kaudet
mkdir -p $kansio/ft_percent
a=/home/aerkkila/smos_uusi/
cp $a/kaudet.c $kansio
cp -l $HOME/smos_uusi/ft_percent/frozen_percent_pixel_*.nc $kansio/ft_percent
cp -l $HOME/smos_uusi/ft_percent/partly_frozen_percent_pixel_*.nc $kansio/ft_percent
kansio=$kansio/create_ft_percent
mkdir -p $kansio
cp $a/ft_percents_pixel_ease.c $kansio
cp -l $a/EASE_2_l*.nc $kansio
#cp -l $HOME/smos_uusi/FT_720_*.nc $kansio/data # isoja
cat >$kansio/README <<EOF
The code reads annual data files named as FT_720_yyyy.nc.
To run the codes, go to ./create data first.
and compile and run yhdistä_vuosittain.c to turn the files into requested format.
EOF

kansio=$kansio/create_data
mkdir -p $kansio
cp $HOME/smos_uusi/yhdistä_vuosittain.c $kansio
cat >$kansio/README <<EOF
This is the code that was used to combine each year into one file
and fill missing dates with values read from previous existing date.

Data can be downloaded from 
https://nsdc.fmi.fi/services/SMOSService/
(Rautiainen, K., Parkkinen, T., Lemmetyinen, J., Schwank, M., Wiesmann, A., Ikonen, J., Derksen, C., Davydov, S., Davydova, A., Boike, J., Langer, M., Drusch, M., and Pulliainen, J. 2016. SMOS prototype algorithm for detecting autumn soil freezing, Remote Sensing of Environment, 180, 346-360. DOI: 10.1016/j.rse.2016.01.012).
Probably that data is not exactly the same which was used in the article so results may differ slightly if someone recreates the result from there.

Downloaded data files should be in netcdf form and renamed as FT_yyyymmdd.nc.
Something like 'mmv "W_XX-ESA,SMOS,NH_25KM_EASE2_*_[or]_*.nc" FT_#1.nc' should rename the files correctly.
EOF

kansio=$k0/create_BAWLD1x1
mkdir -p $kansio
cp bawld/*.[ch] bawld/Makefile $kansio
cat > $kansio/README <<EOF
Used data is BAWLD_V1___Shapefile.zip from https://doi.org/10.18739/A2C824F9X (Olefeldt et al., 2021) which should be extracted into directory called data.
Makefile downloads and extracts it automatically.
User may want to edit Makefile to give wanted number of threds as an argument to bawld.out on line 3.

Olefeldt, D., Hovemyr, M., Kuhn, M. A., Bastviken, D., Bohn, T. J., Connolly, J., Crill, P., Euskirchen, E. S., Finkelstein, S. A., Genet, H., Grosse, G., Harris, L. I., Heffernan, L., Helbig, M., Hugelius, G., Hutchins, R., Juutinen, S., Lara, M. J., Malhotra, A., Manies, K., McGuire, A. D., Natali, S. M., O'Donnell, J. A., Parmentier, F.-J. W., Räsänen, A., Schädel, C., Sonnentag, O., Strack, M., Tank, S. E., Treat, C., Varner, R. K., Virtanen, T., Warren, R. K., and Watts, J. D.: The Boreal–Arctic Wetland and Lake Dataset (BAWLD), Earth Syst. Sci. Data, 13, 5127–5149, https://doi.org/10.5194/essd-13-5127-2021, 2021.
EOF

cat > $k0/create_links.sh <<EOF
#!/bin/sh
( cd create_köppen;         ln -s ../köppen1x1maski.nc . )
( cd create_köppen/create_köppen1x1maski; ln -s ../../aluemaski.nc . )
( cd create_vuodata;        ln -s ../köppenmaski.txt ../ikirdata.nc ../BAWLD1x1.nc ../flux1x1.nc ../kausien_päivät_int16.nc . )
( cd create_vuojakaumadata; ln -s ../köppenmaski.txt ../ikirdata.nc ../BAWLD1x1.nc ../flux1x1.nc ../kausien_päivät.nc . )
( cd create_kaudet;         ln -s ../aluemaski.nc . )
( cd create_kaudet/create_ft_percent/create_data; ln -s ../../../aluemaski.nc . )
( cd create_BAWLD1x1;       ln -s ../aluemaski.nc . )
( cd create_vuosijainnit;   ln -s ../aluemaski.nc ../flux1x1.nc ../BAWLD1x1.nc ../kausien_päivät.nc . )
EOF
for f in `find $k0 -type f`; do head -1 $f | grep -q "^#!" && chmod 755 $f; done # suoritettaviin tiedostoihin suoritusoikeus

cat > $k0/README <<EOF
Many of the C-codes will probably only work on Unix-like operating systems.
It is necessary to run create_links.sh before attempting to run most codes elsewhere than in the root directory.
It is also necessary to install nctietue3-library (see next paragraph) before running some of the C-codes.

Go to nctietue3 directory which is included here and then it can be installed normally with:
    make
    make install # as root
To remove the library, run:
    make uninstall # as root
To install without root privilidges, change variable prefix in config.mk to \$HOME/.local.
In that case one may have to replace '#include <nctietue3.h>' with '#include "path_to_nctietue3/nctietue3.h"' in the C-codes.

The root directory contains all codes that make the final results used in the article.
Codes needed to create \$data are one level deeper in directory called create_\$data.

Compilation of C-codes:
Sometimes a Makefile is given.
If nctietue3-library is used in C code, it should be compiled with argument -lnctietue3.
Optimization level -Ofast cannot be used in vuojakaumadata.c.
Most C codes use non-ascii utf8 characters in variable names
which old compiler versions cannot compile (for gcc, version ≥ 10.1).

Understanding file names:
aluemaski			region mask
ikirdata                        permafrost data
kaudet                          seasons
kausien_päivät			start and end days of seasons
laatikkokuvaaja.py		a module for making whisker plots
pintaalat			surface areas
ttest_wetlcateg.py		t-tests in section Results: Total emission and average flux
vuo				flux
vuojakaumadata			flux distribution data
vuotaulukot			flux tables
vuosittain			annually
EOF

# Lopuksi koodit ilman suuria tiedostoja
k1=$HOME/codedata1
cp -rl $k0 $k1
rm -r $k1/flux1x1.nc $k1/create_kaudet/ft_percent $k1/create_kaudet/create_ft_percent/EASE*.nc

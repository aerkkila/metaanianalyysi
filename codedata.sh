#!/bin/sh
kansio=/media/levy
lsblk |grep -q $kansio || { echo ei kovalevyä; exit 1; }

kansio=${kansio}/codedata
k0=$kansio
mkdir -p $kansio

cp \
    laatikkokuvaaja.py \
    luokat.py \
    LICENSE \
    $kansio

cp -ur \
    ikirdata.nc \
    köppen1x1maski.nc \
    köppenmaski.npy \
    aluemaski.nc \
    pintaalat.npy \
    vuotaulukot \
    kaudet.nc \
    BAWLD1x1.nc \
    flux1x1.nc \
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
köppikir_kartta.py
kaudet_laatikko.py
bawld_ikir_kartta.py
xvuo_laatikko.py
vuojakaumalaatikko.py
vuojakaumalaatikko_vuosittain.py
ttesti_luokat.py
ttesti.py
'
nimet1='
fig_1,2.py
fig_3,4.py
fig_5.py
fig_6.py
fig_7.py
fig_11.py
ttest_wcateg.py
ttest_mixed-pure.py
'
kopioi

nimet0='
köppikir_taulukko.py
lattaul.c
vuotaul_latex.c
vuojakaumalaatikko_vuosittain.py
'
nimet1='
table_1.py
table_2.c
table_3,4,5,6.c
table_8.py
'
kopioi

kansio=$k0/table_7__figure_8,9,10
regrdir=$kansio
mkdir -p $kansio
cd wregressio
nimet0='
wregressio.c
taulukko_rajat.c
virhepalkit.pyx
setup.py
virhepalkit.py
piirrä.py
Makefile
laske.sh
'
nimet1='
fig_8,9.c
table_7.c
virhepalkit.pyx
setup.py
fig_10.py
piirrä.py
Makefile
run.sh
'
kopioi
cd ..

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
cp muunna_shapefile.c köppentunnisteet.c $kansio
cp -r köppen_shp $kansio
cat >$kansio/Makefile <<EOF
all: a.out
	./a.out

a.out:
	gcc -o $@ -O3 muunna_shapefile.c -lnetcdf -lshp -pthread -lm
EOF

kansio=$k0/create_pintaalat
mkdir -p $kansio
cp pintaalat.py $kansio

kansio=$k0/create_vuotaulukot
mkdir -p $kansio
cp vuotaul_yleinen.c $kansio
cat >$kansio/Makefile <<EOF
all: vuotaul_00.target vuotaul_10.target vuotaul_01.target vuotaul_02.target

vuotaul_00.target: vuotaul_köppen_pri.csv vuotaul_köppen_post.csv vuotaul_ikir_pri.csv vuotaul_ikir_post.csv vuotaul_wetland_pri.csv vuotaul_wetland_post.csv
	cat vuotaulukot/*_pri_*.csv > vuotaul_pri.csv
	cat vuotaulukot/*_post_*.csv > vuotaul_post.csv
vuotaul_00.out:
	gcc -Wall -g -O2 vuotaul_yleinen.c -o \$@ \`pkg-config --libs nctietue2\` -lm -DKOSTEIKKO=0 -Dkosteikko_kahtia=0
vuotaul_wetland_post.csv: vuotaul_00.out
	./vuotaul_00.out wetl post
vuotaul_wetland_pri.csv: vuotaul_00.out
	./vuotaul_00.out wetl pri
vuotaul_köppen_post.csv: vuotaul_00.out
	./vuotaul_00.out köpp post
vuotaul_köppen_pri.csv: vuotaul_00.out
	./vuotaul_00.out köpp pri
vuotaul_ikir_post.csv: vuotaul_00.out
	./vuotaul_00.out ikir post
vuotaul_ikir_pri.csv: vuotaul_00.out
	./vuotaul_00.out ikir pri

# calculates climate and permafrost class data with only their wetland areas into vuotaulukot/*k1.csv
vuotaul_10.target: vuotaul_köppen_post10.csv vuotaul_ikir_post10.csv
vuotaul_10.out:
	gcc -Wall -g -O2 vuotaul_yleinen.c -o \$@ \`pkg-config --libs nctietue2\` -lm -DKOSTEIKKO=1 -Dkosteikko_kahtia=0
vuotaul_köppen_post10.csv: vuotaul_10.out
	./vuotaul_10.out köpp post
vuotaul_ikir_post10.csv: vuotaul_10.out
	./vuotaul_10.out ikir post

# calculates wetland data without the mixed area into vuotaulukot/kahtia/*
vuotaul_01.target: vuotaul_wetland_post01.csv
vuotaul_01.out:
	gcc -Wall -g -O2 vuotaul_yleinen.c -o \$@ \`pkg-config --libs nctietue2\` -lm -DKOSTEIKKO=0 -Dkosteikko_kahtia=1
vuotaul_wetland_post01.csv: vuotaul_01.out
	./vuotaul_01.out wetl post

# calculates wetland data with only the mixed area into vuotaulukot/kahtia_keskiosa/*
vuotaul_02.target: vuotaul_wetland_post02.csv
vuotaul_02.out:
	gcc -Wall -g -O2 vuotaul_yleinen.c -o \$@ \`pkg-config --libs nctietue2\` -lm -DKOSTEIKKO=0 -Dkosteikko_kahtia=2
vuotaul_wetland_post02.csv: vuotaul_02.out
	./vuotaul_02.out wetl post
EOF

kansio=$k0/create_kaudet
mkdir -p $kansio/data
a=/media/levy/smos_uusi/data2
cp kaudet.py $kansio 
cp $a/freezing_start_doy* $a/winter_start_doy* $a/winter_end_doy* $kansio/data
#pitää vielä muokata koodia, että tuo kansio on siellä
kansio=$kansio/create_data
mkdir -p $kansio/data
cp  /media/levy/smos_uusi/calculate_DOY_of_winter_end_start.py \
    /media/levy/smos_uusi/calculate_DOY_of_start_of_freezing.py \
    $kansio
cp -u /media/levy/smos_uusi/data2/frozen_percent_pixel_*.nc $kansio/data
kansio=$kansio/create_data
mkdir -p $kansio/data
cp /media/levy/smos_uusi/ft_percents_pixel_ease.c $kansio
cp /media/levy/Tyotiedostot/Carbon_tracker/EASE_2_l*.nc $kansio
cp -u /media/levy/smos_uusi/FT2_720_*.nc $kansio/data # 181 Mt kukin
kansio=$kansio/create_data
mkdir -p $kansio
cp /media/levy/smos_uusi/yhdistä_vuosittain.c $kansio
cat >$kansio/README <<EOF
Original data was given as a separate file for each day (time step)
and some days were missing.
This is the code that was used to combine each year into one file
and fill missing dates with values read from previous existing date.

Needed files are not given because together they are large
and almost the same as ../data.
EOF

kansio=$k0/create_BAWLD1x1
mkdir -p $kansio
cp -ur /media/levy/Tyotiedostot/MethEOWP730/BAWLD/ $kansio/data
cp BAWLD.py $kansio

cat > $k0/create_links.sh <<EOF
#!/bin/sh
( cd ${regrdir};            ln -s ../BAWLD1x1.nc ../flux1x1.nc ../kaudet.nc . )
( cd create_köppen;         ln -s ../köppen1x1maski.nc . )
( cd create_köppen/create_köppen1x1maski; ln -s ../../aluemaski.nc . )
( cd create_vuotaulukot;    ln -s ../köppenmaski.txt ../ikirdata.nc ../BAWLD1x1.nc ../flux1x1.nc ../kaudet.nc . )
( cd create_kaudet;         ln -s ../aluemaski.nc . )
( cd create_kaudet/create_data/create_data; ln -s ../../../aluemaski.nc . )
EOF

cat > $k0/README <<EOF
It is necessary to run create_links.sh before attempting to run most codes elsewhere than in the root directory.

The idea is that a directory always contains the data that is needed to run the codes
and if data was created using other codes, those codes and their data are given one directory deeper.
Codes that make data for other codes are in directories called create_*/.
The root directory contains all codes that make the final results used in the article.

If a file is needed in many levels, it is given in the uppermost directory
and it has to be linked to deeper directories to run those codes.
That is automated in file create_links.sh which puts needed links to right directories.

fig_11.py and table_8.py are the same file but given twice for naming reasons.

Dictionary:
aluemaski			a mask of used area
ikirdata                        permafrost data
kaudet                          seasons
laatikkokuvaaja.py		a module for making whisker plots
pintaalat			surface areas
vuo				flux
vuotaulukot			flux tables
EOF

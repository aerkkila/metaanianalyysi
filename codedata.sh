#!/bin/sh
kansio=$HOME
#lsblk |grep -q $kansio || { echo ei kovalevyä; exit 1; }

kansio=${kansio}/codedata
k0=$kansio
mkdir -p $kansio

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
    kaudet.nc \
    kausien_päivät.nc \
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
cp köppen.c köppentunnisteet.h $kansio
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

kansio=$k0/create_vuojakaumadata
mkdir -p $kansio
cp vuojakaumadata.c $kansio
cat >$kansio/Makefile <<EOF
all: total annually
total: vuojakauma_ikir vuojakauma_köpp vuojakauma_wetl
annually: vuojakauma_vuosittain_ikir vuojakauma_vuosittain_köpp vuojakauma_vuosittain_wetl

vuojakaumadata.out: vuojakaumadata.c
	gcc -Wall \$< -o \$@ \`pkg-config --libs nctietue2 gsl\` -g -O3

vuojakauma_ikir: vuojakaumadata.out
	./\$< ikir post
vuojakauma_köpp: vuojakaumadata.out
	./\$< köpp post
vuojakauma_wetl: vuojakaumadata.out
	./\$< wetl post

vuojakaumadata_vuosittain.out: vuojakaumadata.c
	gcc -Wall \$< -o \$@ \`pkg-config --libs nctietue2 gsl\` -g -O3 -DVUODET_ERIKSEEN=1
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
mkdir -p $kansio/data
a=/home/aerkkila/smos_uusi/
cp $a/kaudet.c $kansio
cp -l $HOME/smos_uusi/ft_percent/frozen_percent_pixel_*.nc $kansio/data
cp -l $HOME/smos_uusi/ft_percent/partly_frozen_percent_pixel_*.nc $kansio/data
kansio=$kansio/create_data
mkdir -p $kansio/data
cp $a/ft_percents_pixel_ease.c $kansio
cp -l $a/EASE_2_l*.nc $kansio
cp -l $HOME/smos_uusi/FT_720_*.nc $kansio/data # isoja
kansio=$kansio/create_data
mkdir -p $kansio
cp $HOME/smos_uusi/yhdistä_vuosittain.c $kansio
cat >$kansio/README <<EOF
Here should be a link if data gets published.

Original data was given as a separate file for each day (time step)
and some days were missing.
This is the code that was used to combine each year into one file
and fill missing dates with values read from previous existing date.

Needed files are not given because together they are large
and almost the same as ../data.
EOF

kansio=$k0/create_BAWLD1x1
mkdir -p $kansio
cp bawld/*.[ch] bawld/Makefile $kansio
cat > $kansio/README <<EOF
Used data is BAWLD_V1___Shapefile.zip from https://doi.org/10.18739/A2C824F9X (Olefeldt et al., 2021) which should be extracted into directory data. Makefile downloads and extracts it automatically.

Olefeldt, D., Hovemyr, M., Kuhn, M. A., Bastviken, D., Bohn, T. J., Connolly, J., Crill, P., Euskirchen, E. S., Finkelstein, S. A., Genet, H., Grosse, G., Harris, L. I., Heffernan, L., Helbig, M., Hugelius, G., Hutchins, R., Juutinen, S., Lara, M. J., Malhotra, A., Manies, K., McGuire, A. D., Natali, S. M., O'Donnell, J. A., Parmentier, F.-J. W., Räsänen, A., Schädel, C., Sonnentag, O., Strack, M., Tank, S. E., Treat, C., Varner, R. K., Virtanen, T., Warren, R. K., and Watts, J. D.: The Boreal–Arctic Wetland and Lake Dataset (BAWLD), Earth Syst. Sci. Data, 13, 5127–5149, https://doi.org/10.5194/essd-13-5127-2021, 2021.
EOF

cat > $k0/create_links.sh <<EOF
#!/bin/sh
( cd ${regrdir};            ln -s ../BAWLD1x1.nc ../flux1x1.nc ../kaudet.nc . )
( cd create_köppen;         ln -s ../köppen1x1maski.nc . )
( cd create_köppen/create_köppen1x1maski; ln -s ../../aluemaski.nc . )
( cd create_vuotaulukot;    ln -s ../köppenmaski.txt ../ikirdata.nc ../BAWLD1x1.nc ../flux1x1.nc ../kaudet.nc . )
( cd create_vuojakaumadata; ln -s ../köppenmaski.txt ../ikirdata.nc ../BAWLD1x1.nc ../flux1x1.nc ../kaudet.nc . )
( cd create_kaudet;         ln -s ../aluemaski.nc . )
( cd create_kaudet/create_data/create_data; ln -s ../../../aluemaski.nc . )
( cd create_BAWLD1x1;       ln -s ../aluemaski.nc . )
EOF
chmod 755 $k0/create_links.sh

cat > $k0/README <<EOF
It is necessary to run create_links.sh before attempting to run most codes elsewhere than in the root directory.

Each directory contains the data that is needed to run the codes
and if data was created using other codes, those codes and their data are given one directory deeper in create_data
The root directory contains all codes that make the final results used in the article.
C-source files will compile without any special arguments (e.g. cc file.c) if Makefile is not given in that directory.

If a file is needed in many directories, it is given only once
and it has to be linked to other directories to run those codes.
That is automated in file create_links.sh which puts needed links to right directories.

fig_11.py and table_8.py are the same file but given twice for naming reasons.

Dictionary:
aluemaski			region mask
ikirdata                        permafrost data
kaudet                          seasons
laatikkokuvaaja.py		a module for making whisker plots
pintaalat			surface areas
vuo				flux
vuojakaumadata			flux distribution data
vuotaulukot			flux tables
vuosittain			annually
EOF

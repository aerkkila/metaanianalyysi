#!/bin/sh
kansio=/media/levy
lsblk |grep -q $kansio || { echo ei kovalevyä; exit 1; }

kansio=${kansio}/codedata
mkdir -p $kansio

cp \
    laatikkokuvaaja.py \
    luokat.py \
    config.py \
    LICENSE \
    $kansio

cp -r \
    ikirdata.nc \
    köppen1x1maski.nc \
    aluemaski.nc \
    pintaalat.npy \
    vuotaulukot \
    kaudet2.nc \
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
wkahtia_kartta.py
xvuo_laatikko.py
vuojakaumalaatikko.py
vuojakaumalaatikko_vuosittain.py
'
nimet1='
fig_1,2.py
fig_3,4.py
fig_5.py
fig_6.py
fig_7.py
fig_11.py
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

regrdir=table_7__figure_8,9,10
mkdir -p $kansio/$regrdir
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
k0=$kansio
kansio=$kansio/$regrdir
kopioi
kansio=$k0
cd ..

cat > $kansio/create_links.sh <<EOF
#!/bin/sh
ln -s BAWLD1x1.nc flux1x1.nc kaudet2.nc ${regrdir}
EOF

cat > $kansio/README <<EOF
It is recommended to run create_links.sh before attempting to run codes in deeper directories than top level.

The idea is that a directory always contains the data that is needed to run the codes
and if data was created using other codes, those codes and their data are given one directory deeper
but always hierarchy is not that clear.
In such cases the directory contains a shell script that runs the codes in the right order.
If a file is needed in many levels, it is given in the uppermost directory
and user may have to create links or move files to run codes in deeper directories.
That is automated in file create_links.sh which puts needed links to right directories.

laatikkokuvaaja.py is a module for making whisker plots.
fig_11.py and table_8.py are the same file but given twice for naming reasons.
EOF

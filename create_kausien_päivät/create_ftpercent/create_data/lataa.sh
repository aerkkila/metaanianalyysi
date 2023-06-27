#!/bin/sh

nimi0=W_XX-ESA,SMOS,NH_25KM_EASE2_%i%02i%02i_o_v201_01_l3soilft.nc
url0=ftp://litdb.fmi.fi/outgoing/SMOS-FTService

lataa_kuukausi() {
    printf "%i/%02i, t = %i\n" $vuosi $kuukausi $(date +"%s")
    url=`printf %s/%i/%02i $url0 $vuosi $kuukausi`
    if [ $kuukausi = 12 ]; then
	loppu=31
    else
	seur_kk=`printf %i%02i01 $vuosi $((kuukausi+1))`
	loppu=`date -d "$seur_kk -1 day" +%d`
    fi

    for d in `seq 1 $loppu`; do
	tied=`printf $nimi0 $vuosi $kuukausi $d`
	[ -f $tied ] && continue
	printf "$d\r"
	cd tmp # vältetään keskeneräiset tiedostot
	ftp -V $url/$tied && mv $tied .. || printf "%i%02i%02i\n" $vuosi $kuukausi $d >>../../puuttuvat.txt
	cd ..
    done
}

mkdir -p raaka
rm -r raaka/tmp puuttuvat.txt
mkdir raaka/tmp
cd raaka

vuosi=2010
for kuukausi in `seq 7 12`; do
    lataa_kuukausi
done

for vuosi in `seq 2011 2020`; do
    for kuukausi in `seq 1 12`; do
	lataa_kuukausi
    done
done

vuosi=2021
for kuukausi in `seq 1 8`; do
    lataa_kuukausi
done

cd ..
rm -r raaka/tmp

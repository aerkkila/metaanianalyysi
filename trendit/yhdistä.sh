#!/bin/bash
kansio='kuvat'
kaudet='summer freezing winter whole_year'
lajit1='bog,fen,marsh permafrost_bog,tundra_wetland,wetland'
lajit2='nonpermafrost,sporadic discontinuous,continuous'
lajit3='Db,Dc Dd,ET'

muuttuja=
luku=

luokat() {
    kmnt='gm convert'
    for laji in $@; do
	kmnt="$kmnt +append $kansio/$muuttuja/$kausi,_{$laji}.png"
    done
    kmnt="$kmnt -append kuvat/${muuttuja}_${kausi}_${luku}.png"
    eval $kmnt
    echo $kmnt
}

kaudet() {
    muuttuja=$1
    for kausi in $kaudet; do
	ls $kansio/$1/$kausi*.png 2>/dev/null 1>/dev/null || continue
	luku=1
	luokat $lajit1
	luku=2
	luokat $lajit2
	luku=3
	luokat $lajit3
    done
}

kaudet 'emission'
kaudet 'flux'
kaudet 'length'
kaudet 'start'
kaudet 'end'

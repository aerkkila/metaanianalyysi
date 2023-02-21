#!/bin/sh

# This script uses command line program "gm" to combine previously created figures into panels.

wc='warm cold'
bfm='bog fen marsh'
pt='permafrost_bog tundra_wetland'
kaudet='summer freezing winter'
kansio='../kuvia'

B3() {
    a="gm convert"
    for w in $pt; do
	a="$a +append"
	for k in $kaudet; do
	    a="$a $kansio/wregressio_suora_${k}_$w.png"
	done
    done
    $a -append $kansio/figB3.png
}

B2() {
    a="gm convert"
    for w in $bfm; do
	a="$a +append"
	for k in $kaudet; do
	    a="$a $kansio/wregressio_suora_${k}_$w.png"
	done
    done
    $a -append $kansio/figB2.png
}

B1() {
    a="gm convert"
    for z in $wc; do
	a="$a +append"
	for k in $kaudet; do
	    a="$a $kansio/wregressio_${k}_wetland_$z.png"
	done
    done
    $a -append $kansio/figB1.png
}

eval $@

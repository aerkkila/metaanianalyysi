#!/usr/bin/bash

ikir() {
    #./ikir_alkuloppu.py -s
    for al in 'start' 'end'; do
	a='gm convert '
	for i in `seq 0 3`; do
	    a="$a +append kuvia/yksittäiset/ikir${i}_w${al}_ft[012].png"
	done
	a="$a -append kuvia/ikir_w${al}.png"
	$a &
    done
}

koppen_ikir() {
    #./köppen_ikir_alkuloppu.py -s
    for al in 'start' 'end'; do
	a='gm convert '
	for i in `seq 0 3`; do
	    a="$a +append kuvia/yksittäiset/köppen_w${al}_ikir${i}_ft[012].png"
	done
	a="$a -append kuvia/köppen_ikir_w${al}.png"
	$a &
    done
}

bawld_ikir() {
    #./bald_ikir_alkuloppu.py -s
    for al in 'start' 'end'; do
	a='gm convert '
	for i in `seq 0 3`; do
	    a="$a +append kuvia/yksittäiset/bawld_w${al}_ikir${i}_ft[012].png"
	done
	a="$a -append kuvia/bawld_ikir_w${al}.png"
	$a &
    done
}

yleinen_vierekkain() {
    for al in 'start' 'end'; do
	gm convert kuvia/yksittäiset/$1_w${al}_ft[012].png +append kuvia/$1_w${al}.png
    done
}

bawld_laatikko() {
    #./bawld_laatikko_alkuloppu.py -s
    yleinen_vierekkain $@
}

koppen_laatikko() {
    #./köppen_laatikko_alkuloppu.py -s
    yleinen_vierekkain $@
}

#wetlandvuo() {
#    #./wetlandvuocsv.py -s
#    gm convert +append kuvia/yksittäiset/wetland_nmol,s,m2_s{0,1}.png \
#       +append kuvia/yksittäiset/wetland_nmol,s,m2_s{2,3}.png \
#       -append kuvia/wetland_nmol,s,m2.png
#}

kaikki() {
    ikir ikir
    koppen_ikir koppen_ikir
    bawld_ikir bawld_ikir
    bawld_laatikko bawld_laatikko
    koppen_laatikko köppen_laatikko
}

eval `echo $1 |tr -s ö o` $@

#!/usr/bin/sh

vanha_ikir() {
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

ikir() {
    #./ikir_alkuloppu.py -s
    a='gm convert '
    for i in `seq 0 3`; do
	a="$a +append"
	for k in 'freezing' 'winter' 'summer'; do
	    a="$a kuvia/yksittäiset/ikir${i}_${k}_start.png"
	done
    done
    a="$a -append kuvia/ikir_kaudet.png"
    echo $a
    $a
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

kaikki() {
    ikir ikir
    koppen_ikir koppen_ikir
    bawld_ikir bawld_ikir
    bawld_laatikko bawld_laatikko
    koppen_laatikko köppen_laatikko
}

eval `echo $1 |tr -s ö o` $@

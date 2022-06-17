#!/usr/bin/sh

ikir_ft_histog() {
    #./prf_ft_histog.py -s
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
    for al in 'start' 'end'; do
	a='gm convert '
	for i in `seq 0 3`; do
	    a="$a +append kuvia/yksittäiset/köppen_w${al}_ikir${i}_ft[012].png"
	done
	a="$a -append kuvia/köppen_ikir_w${al}.png"
	$a &
    done
}

yleinen_vierekkain() {
    for al in 'start' 'end'; do
	gm convert kuvia/yksittäiset/$1_w${al}_ft[012].png +append kuvia/$1_w${al}.png
    done
}

bawld_laatikko() {
    #./BAWLD_laatikko.py -s
    yleinen_vierekkain $@
}

bawld_laatikko_os() {
    #./BAWLD_laatikko_painotettu.py -s
    yleinen_vierekkain $@
}

koppen_laatikko() {
    #./köppen_laatikko.py -s
    yleinen_vierekkain $@
}

eval `echo $1 |tr -s ö o` $@

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

bawld_laatikko() {
    #./BAWLD_laatikko.py -s
    for al in 'start' 'end'; do
	gm convert kuvia/yksittäiset/BAWLD_laatikko_w${al}_ft[012].png +append kuvia/BAWLD_laatikko_w${al}.png
    done
}

koppen_laatikko() {
    #./köppen_laatikko.py -s
    for al in 'start' 'end'; do
	gm convert +append kuvia/yksittäiset/köppen_laat_${al}_ft[012].png \
	   kuvia/köppen_laat_${al}.png
    done
}

eval `echo $1 |tr -s ö o`

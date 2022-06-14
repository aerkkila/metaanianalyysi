#!/usr/bin/sh

#./prf_ft_histog.py -s
for al in 'start' 'end'; do
    a='gm convert '
    for i in `seq 0 3`; do
	a="$a +append kuvia/ikirft/ikir${i}_w${al}_ft[012].png"
    done
    a="$a -append kuvia/ikir_w${al}.png"
    $a &
done

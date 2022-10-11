#!/bin/sh
w0='fen marsh'
w1='permafrost_bog tundra_wetland'
k0='summer freezing winter whole_year'

for k in $k0; do
    a="gm convert +append ../kuvia/wregressio_${k}_wetland.png ../kuvia/wregressio_suora_${k}_bog.png +append"
    for w in $w0; do
	a="$a ../kuvia/wregressio_suora_${k}_${w}.png"
    done
    $a -append kuva_$k.png
done

for k in $k0; do
    a="gm convert +append ../kuvia/wregressio_${k}_wetland_permafrost.png +append"
    for w in $w1; do
	a="$a ../kuvia/wregressio_suora_${k}_${w}.png"
    done
    $a -append kuva_${k}_ikir.png
done

#!/bin/sh

laske() {
    pids=
    ./päivät_vuosittain.out $1 alku &
    pids="${pids} $!"
    ./päivät_vuosittain.out $1 loppu &
    pids="${pids} $!"
    ./päivät_vuosittain.out $1 pituus &
    pids="${pids} $!"
    for pid in $pids; do
	wait $pid
    done
}

make päivät_vuosittain.out
laske köpp
laske ikir
laske wetl
cat kausidata/length_*.csv > kausidata/length.csv
cat kausidata/start_*.csv > kausidata/start.csv
cat kausidata/end_*.csv > kausidata/end.csv

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
cat kausidata2301/length_*.csv > kausidata2301/length.csv
cat kausidata2301/start_*.csv > kausidata2301/start.csv
cat kausidata2301/end_*.csv > kausidata2301/end.csv

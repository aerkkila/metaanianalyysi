#!/bin/sh
make -q
if [ $? -gt 0 ]; then
    make
    [ $? -gt 0 ] && exit
fi
[ ! -d tallenteet ] && mkdir tallenteet

pids=''
for i in `seq 0 3`; do
    komento="./wregressio.out -k $i -s -p -s"
    { eval $komento; echo $komento; } &
    pids="${pids}$! "
    komento="./wregressio.out -k $i -s -p -s -i"
    { eval $komento; echo $komento; } &
    pids="${pids}$! "
done

for pid in $pids; do
    wait $pid
done

printf '%s csv %s\n' '-*-' '-*-' > sovitteet.txt
cat tallenteet/* >> sovitteet.txt
./virhepalkit.py -s

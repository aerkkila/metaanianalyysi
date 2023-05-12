#!/bin/sh
mkdir -p raaka
osoite=https://dap.ceda.ac.uk/neodc/esacci/permafrost/data/permafrost_extent/L4/area4/pp/v03.0
nimet=`curl -s $osoite -L |grep -oP '(?<=href=")[^"]*(?=")' |grep "^.*\.nc$"`
[ $? != 0 ] && echo curl epäonnistui. Lieneekö nettiä?
for n in $nimet; do
    if [ ! -e raaka/$n ]; then
	nyt="$osoite/$n"
	echo $nyt
	curl -LO $nyt
	mv $n raaka
    fi
done

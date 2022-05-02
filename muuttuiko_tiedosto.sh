#!/bin/sh
[ $1 ] || exit 0
gzip -k $1
if cmp -s $1.gz .cmp/$1.gz; then
    rm $1.gz
    exit 0
else
    mv $1.gz .cmp/
    exit 1
fi

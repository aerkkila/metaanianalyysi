#!/bin/env python3
from matplotlib.pyplot import *
import numpy as np
import sys, struct, os
from laatikkokuvaaja import laatikkokuvaaja
import luokat

kaudet   = luokat.kaudet[1:]
flatjarj = 'C'
pripost  = ['pri', 'post']
ppnum = 0 if 'pri' in sys.argv else 1

def laita_keskiarvot(avg, nimet, tunniste):
    assert(flatjarj == 'C')
    a = [nimi.split(',') for nimi in nimet.flatten()]
    rivit = [b[0] for b in a[::len(kaudet)]]
    sarakt = [b[1] for b in a[:len(kaudet)]]
    avg = np.array(avg).reshape([len(rivit),len(sarakt)])
    f = open('vuojakaumalaatikko_avg_pyout%s.csv' %tunniste, 'w')
    for s in sarakt:
        f.write(',%s' %s)
    for j,r in enumerate(rivit):
        f.write('\n%s' %r)
        for i,s in enumerate(sarakt):
            f.write(',%.4f' %avg[j,i])
    f.write('\n')
    f.close()

def lue(luokitus, kost):
    dt     = np.empty([len(luokitus),len(kaudet)], object)
    nimet  = np.empty([len(luokitus),len(kaudet)], object)
    for luokkai,luokka in enumerate(luokitus):
        dir = "vuojakaumadata%s" %("/kost" if kost[luokkai] else "")
        for kausii,kausi in enumerate(kaudet):
            with open('%s/%s_%s_%s.bin' %(dir, luokka, kausi, pripost[ppnum]), "r") as f:
                raaka = f.buffer.read()
            pit2 = struct.unpack("i", raaka[:4])[0]
            dt    [luokkai, kausii] = np.ndarray(pit2, dtype=np.float32, buffer=raaka[4:])
            nimet [luokkai, kausii] = "%s, %s" %(luokka,kausi)
    return dt, nimet

def aja(dt, nimet, tunniste):
    värit = 'rkb'*dt.shape[0]
    värit = [*värit]
    tulos = laatikkokuvaaja(dt.flatten(order=flatjarj), fliers='', vari=värit, avgmarker='.')
    laita_keskiarvot(tulos['avg'], nimet, tunniste)
    xticks(tulos['xsij'], labels=[s.replace('_',' ') for s in nimet.flatten(order=flatjarj)], rotation=90, ha='center')
    ax = gca()
    #[t.set_color(v) for t,v in zip(ax.xaxis.get_ticklabels(), värit)]
    #[t.set_color(v) for t,v in zip(ax.xaxis.get_ticklines(), värit)]
    grid('on', axis='y')
    ylabel('nmol m$^{-2}$ s$^{-1}$')
    yticks(rotation=90)
    tight_layout()
    if '-s' in sys.argv:
        nimi = 'kuvia/vuojakaumalaatikko_%s_%s.png' %(pripost[ppnum], tunniste)
        savefig(nimi)
        clf()
        os.system('gm convert -rotate 90 %s %s' %(nimi,nimi))
    else:
        show()

def main():
    def params():
        rcParams.update({'figure.figsize':(len(luokitus)*1.3,11), 'font.size':16})

    luokitus = np.array([*luokat.ikir, *luokat.kopp])
    params()
    dt,nimet = lue(luokitus, np.zeros(len(luokitus), bool))
    aja(dt, nimet, '0')

    luokitus = np.array([*luokitus, 'fen', 'permafrost_bog', 'tundra_wetland'])
    kost = np.ones(len(luokitus), bool)
    kost[-3:] = False
    params()
    dt,nimet = lue(luokitus, kost)
    aja(dt, nimet, '1')

    luokitus = np.array(luokat.wetl)
    rcParams.update({'figure.figsize':(len(luokitus)*1.3,11), 'font.size':16})
    dt, nimet = lue(luokitus, np.zeros(len(luokitus), bool))
    aja(dt, nimet, '2')

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit()

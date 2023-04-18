#!/bin/env python3
from matplotlib.pyplot import *
from matplotlib.patches import Rectangle
import numpy as np
import sys, struct, os
from laatikkokuvaaja import laatikkokuvaaja
import luokat
from PIL import Image

kaudet   = luokat.kaudet[1:]
flatjarj = 'F'
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
            nimet [luokkai, kausii] = "%s" %(luokka)
    return dt, nimet

def aja(dt, nimet, tunniste, pitdet, ryhmät):
    värit0 = [['#ff0000','#000000','#0000ff'], ['#ff7766','#798079','#4686cf'], ['#ffaaaa','#aaaaaa','#aaaaff']]
    värit = [värit0[int(r)][k] for r in ryhmät for k in range(3)]
    #värit = [*värit]
    värit = np.array(värit).reshape([len(värit)//3, 3]).flatten(order=flatjarj)
    tulos = laatikkokuvaaja(dt.flatten(order=flatjarj), fliers='', vari=värit, avgmarker='.', fill=1)
    #laita_keskiarvot(tulos['avg'], nimet, tunniste)
    xticks(tulos['xsij'], labels=[s.replace('_',' ') for s in nimet.flatten(order=flatjarj)], rotation=90, ha='center')
    #ax = gca()
    #[t.set_color(v) for t,v in zip(ax.xaxis.get_ticklabels(), värit)]
    #[t.set_color(v) for t,v in zip(ax.xaxis.get_ticklines(), värit)]
    grid('on', axis='y')
    ylabel('nmol m$^{-2}$ s$^{-1}$')
    yticks(rotation=90)
    pch = []
    tight_layout()

    y = 0.76
    gca().set_axisbelow(True)
    lisä = 0
    for ki,k in enumerate(kaudet):
        x = 0.8+ki*0.04/xkoko*10
        gca().add_patch(Rectangle((x,y), 0.02/xkoko*10, 0.022, facecolor=värit0[0][ki], edgecolor=None, transform=gca().transAxes, zorder=2))
        if '1' in ryhmät:
            gca().add_patch(Rectangle((x,y-0.025), 0.02/xkoko*10, 0.022,
                facecolor=värit0[1][ki], edgecolor=None, transform=gca().transAxes, zorder=2))
            lisä += 0.025*(ki==0)
        if '2' in ryhmät:
            gca().add_patch(Rectangle((x,y-0.05), 0.02/xkoko*10, 0.022,
                facecolor=värit0[2][ki], edgecolor=None, transform=gca().transAxes, zorder=2))
            lisä += 0.025*(ki==0)
        text(x-0.005/xkoko*10, 0.8, k, rotation=90, transform=gca().transAxes)

    gca().add_patch(Rectangle([0.8-0.01, y-0.01-lisä], 0.13/xkoko*10, 0.16+lisä,
        edgecolor='k', facecolor='w', fill=1, alpha=1, transform=gca().transAxes, zorder=1))

    if '-s' in sys.argv:
        nimi = 'kuvia/vuojakaumat_%s_%s.png' %(pripost[ppnum], tunniste)
        savefig(nimi)
        clf()
        os.system('gm convert -rotate 90 %s %s' %(nimi,nimi))
    else:
        show()

def main():
    global xkoko
    def params():
        global xkoko
        rcParams.update({'figure.figsize':(len(luokitus)*1.28,11), 'font.size':16})
        xkoko = len(luokitus)*1.25

    luokitus = np.array([*luokat.ikir, *luokat.köpp])
    params()
    dt,nimet = lue(luokitus, np.zeros(len(luokitus), bool))
    pitdet = [len(luokat.ikir), len(luokat.köpp)]
    ryhmät = '00001111'
    aja(dt, nimet, '0', pitdet, ryhmät)

    luokitus = np.array([*luokitus, 'fen', 'permafrost_bog', 'tundra_wetland'])
    kost = np.ones(len(luokitus), bool)
    kost[-3:] = False
    params()
    dt,nimet = lue(luokitus, kost)
    pitdet.append(3)
    ryhmät = '00001111222'
    aja(dt, nimet, '1', pitdet, ryhmät)

    luokitus = np.array(luokat.wetl)
    params()
    dt, nimet = lue(luokitus, np.zeros(len(luokitus), bool))
    ryhmät = '0'*dt.shape[0]
    aja(dt, nimet, '2', False, ryhmät)

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit()

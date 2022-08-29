#!/usr/bin/python3
from matplotlib.pyplot import *
import numpy as np
import sys, struct, os
from laatikkokuvaaja import laatikkokuvaaja
import luokat

luokitus0 = np.array([*luokat.ikir, *luokat.kopp])
luokitus1 = np.array(luokat.wetl)
#luokitus = luokitus[luokitus!='wetland']
kaudet   = ['summer','freezing','winter']
flatjarj = 'C'
pripost  = ['pri', 'post']

def laita_keskiarvot(avg, nimet, tunniste):
    assert(flatjarj == 'C')
    a = [nimi.split(',') for nimi in nimet.flatten()]
    rivit = [b[0] for b in a[::len(kaudet)]]
    sarakt = [b[1] for b in a[:len(kaudet)]]
    avg = np.array(avg).reshape([len(rivit),len(sarakt)])
    f = open('vuojakaumalaatikko_avg%s.csv' %tunniste, 'w')
    for s in sarakt:
        f.write(',%s' %s)
    for j,r in enumerate(rivit):
        f.write('\n%s' %r)
        for i,s in enumerate(sarakt):
            f.write(',%.4f' %avg[j,i])
    f.write('\n')
    f.close()

def aja(luokitus,tunniste):
    dt     = np.empty([len(luokitus),len(kaudet)], object)
    nimet  = np.empty([len(luokitus),len(kaudet)], object)
    pitdet = np.empty([len(luokitus),len(kaudet)], np.int32)
    ppnum = 0 if 'pri' in sys.argv else 1
    for luokkai,luokka in enumerate(luokitus):
        for kausii,kausi in enumerate(kaudet):
            with open('vuojakaumadata/%s_%s_%s.bin' %(luokka,kausi,pripost[ppnum]), "r") as f:
                raaka = f.buffer.read()
            pit2 = struct.unpack("ii", raaka[:8])
            dt    [luokkai, kausii] = np.ndarray(pit2[0], dtype=np.float32, buffer=raaka[4:])
            nimet [luokkai, kausii] = "%s, %s" %(luokka,kausi)
            pitdet[luokkai, kausii] = pit2[1]

    varit = 'rkb'*dt.shape[0]
    varit = [*varit]
    tulos = laatikkokuvaaja(dt.flatten(order=flatjarj), fliers='', vari=varit, avgmarker='.')
    laita_keskiarvot(tulos['avg'], nimet, tunniste)
    xticks(tulos['xsij'][:-1], labels=[s.replace('_',' ') for s in nimet.flatten(order=flatjarj)], rotation=90, ha='center')
    ax = gca()
    #[t.set_color(v) for t,v in zip(ax.xaxis.get_ticklabels(), varit)]
    #[t.set_color(v) for t,v in zip(ax.xaxis.get_ticklines(), varit)]
    grid('on', axis='y')
    ylabel('nmol m$^{-2}$ s$^{-1}$')
    yticks(rotation=90)
#    for i,x in enumerate(tulos['xsij'][:-1]):
#        text(x, 1.03, "%i" %(pitdet.flatten(order=flatjarj)[i]), transform=ax.get_xaxis_transform(), rotation=90, ha='center')
    tight_layout()
    if '-s' in sys.argv:
        nimi = 'kuvia/%s_%s_%s.png' %(sys.argv[0][:-3], pripost[ppnum], tunniste)
        savefig(nimi)
        clf()
        os.system('gm convert -rotate 90 %s %s' %(nimi,nimi))
    else:
        show()

def main():
    rcParams.update({'figure.figsize':(len(luokitus0)*1.3,11), 'font.size':16})
    aja(luokitus0, '0')
    rcParams.update({'figure.figsize':(len(luokitus1)*1.3,11), 'font.size':16})
    aja(luokitus1, '1')

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit()

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
    tulos = laatikkokuvaaja(dt.flatten(order=flatjarj), fliers='', vari=varit, avgmarker='.')
    xticks(tulos['xsij'][:-1], labels=nimet.flatten(order=flatjarj), rotation=90, ha='center')
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
    rcParams.update({'figure.figsize':(7,11), 'font.size':14})
    aja(luokitus0, '0')
    aja(luokitus1, '1')

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit()

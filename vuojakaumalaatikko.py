#!/usr/bin/python3
from matplotlib.pyplot import *
import numpy as np
import sys, struct, os
from laatikkokuvaaja import laatikkokuvaaja
import luokat

luokitus = np.array([*luokat.ikir, *luokat.wetl, *luokat.kopp])
#luokitus = luokitus[luokitus!='wetland']
kaudet   = ['summer','freezing','winter']
flatjarj = 'F'

def main():
    rcParams.update({'figure.figsize':(13,11), 'font.size':14})
    dt     = np.empty([len(luokitus),len(kaudet)], object)
    nimet  = np.empty([len(luokitus),len(kaudet)], object)
    pitdet = np.empty([len(luokitus),len(kaudet)], np.int32)
    for luokkai,luokka in enumerate(luokitus):
        for kausii,kausi in enumerate(kaudet):
            with open('vuojakaumadata/%s_%s_post.bin' %(luokka,kausi), "r") as f:
                raaka = f.buffer.read()
            pit2 = struct.unpack("ii", raaka[:8])
            dt    [luokkai, kausii] = np.ndarray(pit2[0], dtype=np.float32, buffer=raaka[4:])
            nimet [luokkai, kausii] = "%s, %s" %(luokka,kausi)
            pitdet[luokkai, kausii] = pit2[1]

    tulos = laatikkokuvaaja(dt.flatten(order=flatjarj), fliers='')
    xticks(tulos['xsij'][:-1], labels=nimet.flatten(order=flatjarj), rotation=90, ha='center')
    ax = gca()
    ax.spines['top'].set_visible(True)
    grid('on', axis='y')
    ylabel('nmol m$^{-2}$ s$^{-1}$')
    yticks(rotation=90)
#    for i,x in enumerate(tulos['xsij'][:-1]):
#        text(x, 1.03, "%i" %(pitdet.flatten(order=flatjarj)[i]), transform=ax.get_xaxis_transform(), rotation=90, ha='center')
    tight_layout()
    if '-s' in sys.argv:
        nimi = 'kuvia/%s.png' %(sys.argv[0][:-3])
        savefig(nimi)
        os.system('gm convert -rotate 90 %s %s' %(nimi,nimi))
    else:
        show()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit()

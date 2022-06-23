#!/usr/bin/python3
from matplotlib.pyplot import *
from wetlandvuo import kaudet
import numpy as np
import sys

def lue_data():
    alustettu = False
    for k,kausi in enumerate(kaudet):
        for ftnum in range(3):
            nimi = 'wetlandvuotaulukot/wetlandvuo_%s_ft%i.csv' %(kausi, ftnum)
            dt = np.genfromtxt(nimi, delimiter=',', skip_header=2)
            if not alustettu:
                wluokat = []
                with open(nimi) as f:
                    f.readline()
                    rivi = f.readline()
                    for r in f:
                        wluokat.append(r.partition(',')[0])
                cols        = rivi.split(',')
                vuo_per_s_c = cols.index('nmol/s/m²')
                massa_c     = cols.index('Tg')
                vuo_c       = cons.index('mol/m²')
                vuo_per_s   = np.empty((len(kaudet),3,len(wluokat)))
                massa       = np.empty((len(kaudet),3,len(wluokat)))
                vuo         = np.empty((len(kaudet),3,len(wluokat)))
                alustettu   = True
            vuo_per_s[k,ftnum,:] = dt[:,vuo_per_s_c]
    return vuo_per_s, massa, vuo, wluokat

def main():
    rcParams.update({'figure.figsize':(10,8), 'font.size':14})
    vuo_per_s,massa,wluokat = lue_data()

    #joka toinen nimi alemmalle riville
    for i,x in enumerate(wluokat):
        if i%2:
            wluokat[i] = '\n'+x

    xlev = 1/len(wluokat)
    xlevo = 0.3
    Xsij = lambda wi,fti: (wi+0.5)*xlev - 0.5*xlevo*xlev + fti*xlevo*xlev/3
    for k in range(vuo_per_s.shape[0]):
        for j in range(vuo_per_s.shape[1]):
            for i in range(vuo_per_s.shape[2]):
                plot(Xsij(i,j), vuo_per_s[k,j,i], '.', color='rgb'[j], markersize=12)
        xticks(Xsij(np.arange(6),1), wluokat)
        title(kaudet[k])
        tight_layout()
        if '-s' in sys.argv:
            savefig('kuvia/yksittäiset/wetland_nmol,s,m2_s%i.png' %(k))
            clf()
            continue
        show()

if __name__ == '__main__':
    main()

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
                cols      = rivi.rstrip().split(',')[1:]
                taul      = np.empty((len(cols), len(kaudet), 3, len(wluokat)))
                alustettu = True
            for c in range(len(cols)):
                taul[c,k,ftnum,:] = dt[:,c+1]
    return taul, wluokat, cols

def main():
    rcParams.update({'figure.figsize':(10,8), 'font.size':14})
    taul,wluokat,cols = lue_data()

    #joka toinen nimi alemmalle riville
    for i,x in enumerate(wluokat):
        if i%2:
            wluokat[i] = '\n'+x

    xlev = 1/len(wluokat)
    xlevo = 0.3
    Xsij = lambda wi,fti: (wi+0.5)*xlev - 0.5*xlevo*xlev + fti*xlevo*xlev/3
    for c in range(taul.shape[0]):
        for k in range(taul.shape[1]):
            for j in range(taul.shape[2]):
                for i in range(taul.shape[3]):
                    plot(Xsij(i,j), taul[c,k,j,i], '.', markersize=12, color='rgby'[k])

        for k in range(len(kaudet)):
            plot(0, np.nan, '.', markersize=12, color='rgby'[k], label=kaudet[k])
        legend()

        xticks(Xsij(np.arange(6),1), wluokat)
        ylabel(cols[c])
        tight_layout()
        if '-s' in sys.argv:
            savefig('kuvia/yksittäiset/wetland_%s.png' %(cols[c].replace('/',',')))
            clf()
            continue
        show()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

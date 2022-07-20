#!/usr/bin/python3
from matplotlib.pyplot import *
import numpy as np
import sys, struct

varit  = 'crkym'
tyylit = {' whole_year' : dict(linestyle='--', linewidth=1.6),
          ' winter'     : dict(linestyle='-.', linewidth=1.6),
          ' summer'     : dict(linestyle=':',  linewidth=1.6),
          ' freezing'   : dict(linestyle='-',  linewidth=2.6),}
jarj = [0,1] # 01 -> laji,kausi; 10 -> kausi,laji
tehtiin = False

def tee_kuva():
    global tehtiin
    xscale('log')#, linthreshx=0.001)
    xlabel('flux nmol/m/s$^2$')
    ylabel('pdf')
    legend(loc='upper right')
    tight_layout()
    show();
    tehtiin = True

def main():
    global tehtiin
    rcParams.update({'figure.figsize':(12,10), 'font.size':13})
    raaka = sys.stdin.buffer.read() # nimi\n(pit)(data)(cdf)
    lajit = [[], []]
    lasku=0
    while len(raaka):
        ind = raaka.index(10)
        if not ind:
            lajit = [[],[]]
            tee_kuva()
            raaka = raaka[1:]
            continue
        nimi = raaka[:ind].decode('UTF-8')
        raaka = raaka[ind+1:]
        pit = struct.unpack("i", raaka[:4])[0] * 4
        raaka = raaka[4:]
        dt = np.ndarray(pit//4, dtype=np.float32, buffer=raaka[:pit])
        raaka = raaka[pit:]
        cdf = np.ndarray(pit//4, dtype=np.float32, buffer=raaka[:pit])
        raaka = raaka[pit:]
        vuo = dt*1e9
        alku = np.searchsorted(vuo, 0.0001)

        tehtiin = False

        s = nimi.split(',')
        if s[0] not in lajit[0]:
            lajit[0].append(s[0])
        if s[1] not in lajit[1]:
            lajit[1].append(s[1])
        plot(vuo[alku:], 1-cdf[alku:], label=nimi,
             color = varit[ lajit[jarj[0]].index(s[jarj[0]]) ],
             **tyylit[s[jarj[1]]])

        lasku+=1
        print("\r%i" %lasku, end='')
        sys.stdout.flush()
    print('')

    if not tehtiin:
        tee_kuva()

if __name__=='__main__':
    main()

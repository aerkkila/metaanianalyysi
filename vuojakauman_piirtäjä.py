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
tee_laatikko = True
tee_jakauma = False

if tee_laatikko:
    from laatikkokuvaaja import laatikkokuvaaja

def tee_kuva(jakauma=False, laatikko=False):
    global tehtiin, datastot, rajastot, nimet
    if jakauma and tee_jakauma:
        xscale('log')#, linthreshx=0.001)
        xlabel('flux nmol/m/s$^2$')
        ylabel('pdf')
        legend(loc='upper right')
        tight_layout()
        show()
    if laatikko and tee_laatikko:
        tulos = laatikkokuvaaja(datastot, fliers=False, painostot=rajastot, valmis=True)
        xticks(tulos['xsij'], labels=nimet, rotation=30, ha='right')
        print(tulos['xsij'])
        grid('on', axis='y')
        tight_layout()
        savefig('kuvia/vuojakauma_laatikko.png')
        datastot = []
        rajastot = []
        nimet = []
    
    tehtiin = True

def main():
    global tehtiin, datastot, rajastot, nimet
    rcParams.update({'figure.figsize':(12,10), 'font.size':13})
    raaka = sys.stdin.buffer.read() # nimi\n(pit)(data)(cdf)
    lajit = [[], []]
    lasku=0
    datastot = []
    rajastot = []
    nimet = []
    while len(raaka):
        ind = raaka.index(10)
        if not ind: # laitettiin rivinvaihto
            tee_kuva(jakauma=True)
            raaka = raaka[1:]
            lajit = [[], []]
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

        tehtiin = False

        s = nimi.split(',')
        if s[0] not in lajit[0]:
            lajit[0].append(s[0])
        if s[1] not in lajit[1]:
            lajit[1].append(s[1])

        if tee_jakauma:
            alku = np.searchsorted(vuo, 0.0001)
            plot(vuo[alku:], 1-cdf[alku:], label=nimi,
                 color = varit[ lajit[jarj[0]].index(s[jarj[0]]) ],
                 **tyylit[s[jarj[1]]])

        if tee_laatikko:
            datastot.append(vuo.copy())
            rajastot.append(cdf.copy())
            nimet.append(nimi)

        lasku+=1
        print("\r%s: %i" %(sys.argv[0], lasku), end='')
        sys.stdout.flush()
    print('')

    if not tehtiin:
        tee_kuva(jakauma=True)
    tee_kuva(laatikko=True)

if __name__=='__main__':
    main()

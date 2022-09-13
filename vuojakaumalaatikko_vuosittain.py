#!/usr/bin/python3
from matplotlib.pyplot import *
import numpy as np
import sys, struct
from laatikkokuvaaja import laatikkokuvaaja
import luokat

luokitus0 = np.array([*luokat.ikir, *luokat.kopp])
luokitus1 = np.array(luokat.wetl)
#luokitus = luokitus[luokitus!='wetland']
kaudet   = ['summer','freezing','winter']
flatjarj = 'C'
pripost  = ['pri', 'post']

def aja2(luokka, kausi):#, csvtied):
    #csvtied.write("%s, %s" %(luokka,kausi))
    #csvtied.write(",%.5f" %np.mean(dt[vuosi-vuosi0]))
    #csvtied.write("\n")
    ppnum = 0 if 'pri' in sys.argv else 1
    with open('vuojakaumadata/vuosittain/%s_%s_%s.bin' %(luokka,kausi,pripost[ppnum]), "r") as f:
        raaka = f.buffer.read()
    (pit,vuosi0) = struct.unpack("ii", raaka[:8])
    vuosi1 = vuosi0 + (len(raaka)-8)//4 // pit
    vuosia = vuosi1-vuosi0
    nimet  = np.empty([vuosi1-vuosi0], object)
    dt0    = np.ndarray(pit*vuosia, dtype=np.float32, buffer=raaka[8:])
    dt     = np.split(dt0, vuosia)
    nimet  = [str(v) for v in range(vuosi0,vuosi1)]

    tulos = laatikkokuvaaja(dt, fliers='', avgmarker='o')
    xticks(tulos['xsij'], labels=nimet, rotation=0, ha='center')
    ax = gca()
    grid('on', axis='y')
    ylabel('nmol m$^{-2}$ s$^{-1}$')
    title("%s, %s" %(luokka, kausi))
    tight_layout()
    if '-s' in sys.argv:
        nimi = 'kuvia/jakaumat_vuosittain/%s_%s_%s.png' %(pripost[ppnum], luokka, kausi)
        savefig(nimi)
        clf()
    else:
        show()

def main():
    rcParams.update({'figure.figsize':(7,11), 'font.size':14})
    '''
    csvtied_ = 'keskivuo_vuosittain.csv' if '-s' in sys.argv else '/dev/null'
    csvtied = open(csvtied_, 'w')
    csvtied.write(',')
    for vuosi in range(vuosi0,vuosi1):
        csvtied.write(',%i' %(vuosi))
    csvtied.write('\n')
    '''
    print('')
    for luokkai,luokka in enumerate(np.concatenate([luokitus0,luokitus1])):
        print("\033[A\r%i/%i\033[K" %(luokkai+1,len(luokitus0)+len(luokitus1)))
        for kausii,kausi in enumerate(kaudet):
            aja2(luokka, kausi)#, csvtied)
    #csvtied.close()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit()

#!/usr/bin/python3
from matplotlib.pyplot import *
import numpy as np
import sys, struct
from laatikkokuvaaja import laatikkokuvaaja
import luokat

luokitus0 = np.array([*luokat.ikir, *luokat.kopp])
luokitus1 = np.array(luokat.wetl)
kaudet   = ['summer','freezing','winter']
pripost  = ['pri', 'post']

def taulukko(tulos, luokka, textied):
    avg = np.sort(tulos['avg'])
    suht = np.std(avg)/np.mean(avg[1:-1])

    yläraja = 0.45
    alaraja = 0.05
    jyrkkyys = 5
    #arvo = lambda x: np.log((x+siirto)*jyrkkyys)/np.log(siirto*jyrkkyys)
    arvo = lambda a: (np.exp(-(a-alaraja)*jyrkkyys)-np.exp(-yläraja*jyrkkyys)) / (1-np.exp(-yläraja*jyrkkyys))

    suht1 = 1 if suht<alaraja else arvo(suht) if suht<yläraja else 0
    textied.write(' & \\colorbox[rgb]{1.00, %.3f, %.3f}{%.3f}' %(suht1,suht1,suht))

def aja2(luokka, kausi, textied):
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
    taulukko(tulos, luokka, textied)
    if('-nf' in sys.argv):
        return
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
    textied_ = 'vuosittaisvaihtelu.tex' if '-s' in sys.argv else '/dev/null'
    textied = open(textied_, 'w')
    textied.write("\\begin{tabular}{l|rrr}\n")
    for kausi in kaudet:
        textied.write(' & %s' %kausi)
    textied.write('\\\\\n\\midrule\n')
    print('')
    for luokkai,luokka in enumerate(np.concatenate([luokitus0,luokitus1])):
        print("\033[A\r%i/%i\033[K" %(luokkai+1,len(luokitus0)+len(luokitus1)))
        textied.write(luokka.replace('_',' '))
        for kausii,kausi in enumerate(kaudet):
            aja2(luokka, kausi, textied)
        textied.write(' \\\\\n')
    textied.write('\\end{tabular}\n')
    textied.close()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit()

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
(vuosi0,vuosi1) = (2012,2021)

def aja(luokitus,tunniste,vuosi):
    dt     = np.empty([len(luokitus),len(kaudet)], object)
    nimet  = np.empty([len(luokitus),len(kaudet)], object)
    pitdet = np.empty([len(luokitus),len(kaudet)], np.int32)
    ppnum = 0 if 'pri' in sys.argv else 1
    for luokkai,luokka in enumerate(luokitus):
        for kausii,kausi in enumerate(kaudet):
            with open('vuojakaumadata_vuosittain/%s_%s_%s_%i.bin' %(luokka,kausi,pripost[ppnum],vuosi), "r") as f:
                raaka = f.buffer.read()
            pit2 = struct.unpack("ii", raaka[:8])
            dt    [luokkai, kausii] = np.ndarray(pit2[0], dtype=np.float32, buffer=raaka[4:])
            nimet [luokkai, kausii] = "%s, %s" %(luokka,kausi)
            pitdet[luokkai, kausii] = pit2[1]

    varit = 'rkb'*dt.shape[0]
    varit = [*varit]
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
        nimi = 'kuvia/jakaumat_vuosittain/%s_%s_%i.png' %(pripost[ppnum], tunniste, vuosi)
        savefig(nimi)
        clf()
        os.system('gm convert -rotate 90 %s %s' %(nimi,nimi))
    else:
        show()

def aja2(luokka, kausi, csvtied):
    dt     = np.empty([vuosi1-vuosi0], object)
    nimet  = np.empty([vuosi1-vuosi0], object)
    pitdet = np.empty([vuosi1-vuosi0], np.int32)
    ppnum = 0 if 'pri' in sys.argv else 1

    csvtied.write("%s, %s" %(luokka,kausi))
    for vuosi in range(vuosi0, vuosi1):
        with open('vuojakaumadata_vuosittain/ft%i_%s_%s_%s_%i.bin' %(ftnum,luokka,kausi,pripost[ppnum],vuosi), "r") as f:
            raaka = f.buffer.read()
        pit2 = struct.unpack("ii", raaka[:8])
        dt    [vuosi-vuosi0] = np.ndarray(pit2[0], dtype=np.float32, buffer=raaka[4:])
        nimet [vuosi-vuosi0] = str(vuosi)
        pitdet[vuosi-vuosi0] = pit2[1]
        csvtied.write(",%.5f" %np.mean(dt[vuosi-vuosi0]))
    csvtied.write("\n")

    tulos = laatikkokuvaaja(dt.flatten(order=flatjarj), fliers='', avgmarker='o')
    xticks(tulos['xsij'][:-1], labels=nimet.flatten(order=flatjarj), rotation=0, ha='center')
    ax = gca()
    grid('on', axis='y')
    ylabel('nmol m$^{-2}$ s$^{-1}$')
    title("%s, %s" %(luokka, kausi))
    tight_layout()
    if '-s' in sys.argv:
        nimi = 'kuvia/jakaumat_vuosittain/ft%i_%s_%s_%s.png' %(ftnum, pripost[ppnum], luokka, kausi)
        savefig(nimi)
        clf()
    else:
        show()

def main():
    global ftnum
    ftnum = 2
    rcParams.update({'figure.figsize':(7,11), 'font.size':14})
    #for vuosi in range(vuosi0,vuosi1):
    #    aja(luokitus0, '0', vuosi)
    #    aja(luokitus1, '1', vuosi)
    csvtied_ = 'keskivuo_vuosittain.csv' if '-s' in sys.argv else '/dev/null'
    csvtied = open(csvtied_, 'w')
    csvtied.write(',')
    for vuosi in range(vuosi0,vuosi1):
        csvtied.write(',%i' %(vuosi))
    csvtied.write('\n')
    print('')
    for luokkai,luokka in enumerate(np.concatenate([luokitus0,luokitus1])):
        print("\033[A\r%i/%i\033[K" %(luokkai+1,len(luokitus0)+len(luokitus1)))
        for kausii,kausi in enumerate(kaudet):
            aja2(luokka, kausi, csvtied)
    csvtied.close()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit()

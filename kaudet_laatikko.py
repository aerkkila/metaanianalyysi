#!/bin/env python3
import numpy as np
from netCDF4 import Dataset
from laatikkokuvaaja import laatikkokuvaaja
from matplotlib.pyplot import *
import luokat, sys, time
from pintaalat import pintaalat
from aikaväli import vuosi1

kaudet = luokat.kaudet[1:]
pd_muuttujat = [['%s_start' %k, '%s_end' %k] for k in kaudet]
vuosi0 = 2011
jatka_ikiroutaa = False
karkausvuosi = [not(i%4) and (bool(i%100) or not(i%400)) for i in range(vuosi0, vuosi1)]

def muunna_aika(lista):
    r = np.empty(len(lista), object)
    for i in range(len(r)):
        tämä = time.localtime(time.mktime(time.struct_time((2002,1,int(lista[i])+1,0,0,0,0,1,0)))) # oispa C
        r[i] = time.strftime("%m-%d", tämä)
    return r

def viimeistele(tulos, xnimet, ynimi):
    ax = gca()
    xs = tulos['xsij']
    grid('on', axis='y')
    ylabel(ynimi)
    xticks(tulos['xsij'], labels=[s.replace('_',' ') for s in xnimet.flatten()])
    if not 'length' in ynimi:
        yl = ylim()
        ytik = ax.get_yticks()[1:-1]
        yticks(ytik)
        ax.twinx()
        ylim(yl)
        päivät = muunna_aika(ytik)
        yticks(ytik,päivät)
    tight_layout()
    if '-s' in sys.argv:
        nimi="kuvia/kaudet_%s.png" %(ynimi.replace(' ','-'))
        savefig(nimi)
        clf()
    else:
        show()

def toimikoon_ikirouta(ikirdata):
    global vuosi1
    lisä_alkuun  = ikirdata['vuosi'][:][0] - vuosi0
    lisä_loppuun = vuosi1-1 - ikirdata['vuosi'][:][-1]
    if not jatka_ikiroutaa:
        if lisä_loppuun > 0:
            vuosi1 -= lisä_loppuun
            lisä_lopppuun = 0
    muoto = list(ikirdata['luokka'].shape)
    muoto[0] += lisä_alkuun + lisä_loppuun
    uusi = np.empty(muoto, np.int8)
    pit = vuosi1 - vuosi0
    data = np.ma.getdata(ikirdata['luokka'][:])

    if lisä_alkuun <= 0 and lisä_loppuun >= 0:
        assert(pit == data.shape[0]+lisä_loppuun+lisä_alkuun)
        uusi[:pit-lisä_loppuun, ...] = data[-lisä_alkuun:, ...]
        uusi[pit-lisä_loppuun:, ...] = np.tile(data[-1, ...], [uusi.shape[0]-(pit-lisä_loppuun), 1, 1])
        return uusi
    elif lisä_alkuun <= 0 and lisä_loppuun < 0:
        assert(pit == data.shape[0]+lisä_loppuun+lisä_alkuun)
        uusi[...] = data[-lisä_alkuun: data.shape[0]+lisä_loppuun, ...]
        return uusi

    print("tämä ei toimi: %i, %i" %(lisä_alkuun, lisä_loppuun))
    sys.exit()

def main():
    rcParams.update({'figure.figsize':(5,7), 'font.size':14})
    ikirluvut  = [0,1,2,3]
    ikirdata_  = Dataset("ikirdata.nc", "r")
    ikirdata   = toimikoon_ikirouta(ikirdata_).flatten() # pitää olla ennen köppeniä, koska määrää aikapituuden
    päivädata  = Dataset("kausien_päivät_int16.nc", "r")
    köppdata   = np.tile(np.load("köppenmaski.npy"), vuosi1-vuosi0)
    ikirdata_.close()

    painot = np.tile(np.repeat(pintaalat, 360), vuosi1-vuosi0)

    xnimet_ikir = ['PF%i' %i for i in range(4)]
    xnimet_köpp = luokat.köpp

    for kausi,muutt in zip(kaudet, pd_muuttujat):
        painostot_ikir = np.empty([len(ikirluvut)], object)
        pdatastot_ikir = np.empty_like(painostot_ikir)
        painostot_köpp = np.empty([len(luokat.kopp)], object)
        pdatastot_köpp = np.empty_like(painostot_köpp)

        vuodet     = päivädata['vuosi'][:]
        vuosimaski = (vuosi0<=vuodet) & (vuodet<vuosi1)
        vuodet     = vuodet[vuosimaski]
        loput      = np.ma.getdata(päivädata[muutt[1]][:][vuosimaski]).astype(np.float32)
        alut       = np.ma.getdata(päivädata[muutt[0]][:][vuosimaski]).astype(np.float32)

        täyttö = alut[0,0,0]
        alut[alut==täyttö] = np.nan
        loput[loput==täyttö] = np.nan
        pitdet = (loput-alut).flatten()

        # Poistetaan alkupäivistä sellaiset kohdat,
        # joissa kausi kestää usean vuoden ja on katkaistu jonain päivänä.
        # Tällöin kauden loppupäivä on sama kuin sen alkupäivä seuraavana vuonna + vuoden päivät.
        for v in range(len(vuodet)-1):
            päiviä = 365 + karkausvuosi[v]
            loput[v, ...] -= päiviä
        tmpmaski = (alut[1:, ...] == loput[:-1, ...])
        alut[1:, ...] = np.where(tmpmaski, np.nan, alut[1:, ...])
        alut = alut.flatten()

        for dt,nimi in zip([alut,pitdet], ['start','length']):
            for iluok in range(len(ikirluvut)):
                maski  = ikirdata == ikirluvut[iluok]
                pdatastot_ikir[iluok] = dt[maski]
                painostot_ikir[iluok] = painot[maski]
                maski = pdatastot_ikir[iluok] == pdatastot_ikir[iluok]
                pdatastot_ikir[iluok] = pdatastot_ikir[iluok][maski]
                painostot_ikir[iluok] = painostot_ikir[iluok][maski]

            for iluok in range(len(luokat.köpp)):
                maski  = köppdata[iluok]
                pdatastot_köpp[iluok] = dt[maski]
                painostot_köpp[iluok] = painot[maski]
                maski = pdatastot_köpp[iluok] == pdatastot_köpp[iluok]
                pdatastot_köpp[iluok] = pdatastot_köpp[iluok][maski]
                painostot_köpp[iluok] = painostot_köpp[iluok][maski]

            gca().set_axisbelow(1)
            tulos = laatikkokuvaaja(np.concatenate([pdatastot_ikir.flatten(), pdatastot_köpp.flatten()]),
                                    fliers='', avgmarker='o', fill=1, vari=np.append(['#798079']*4, ['#aaaaaa']*4),
                                    painostot = np.concatenate([painostot_ikir.flatten(), painostot_köpp.flatten()]))
            viimeistele(tulos, np.concatenate([xnimet_ikir, xnimet_köpp]), '%s %s' %(kausi, nimi))

    päivädata.close()

if __name__=='__main__':
    from warnings import filterwarnings
    filterwarnings(action='ignore', category=DeprecationWarning, message='`np.bool` is a deprecated alias')
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

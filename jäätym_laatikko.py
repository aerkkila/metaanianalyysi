#!/usr/bin/python3
import numpy as np
from netCDF4 import Dataset
from laatikkokuvaaja import laatikkokuvaaja
from matplotlib.pyplot import *
import luokat, sys

aste = 0.0174532925199
SPINTAALA = lambda _lat: np.sin((_lat+1)*aste) - np.sin(_lat*aste)

al_muuttuja = ['jaatym_alku', 'talven_alku', 'freezing']
al_nimi = ['freezing start', 'freezing end', 'freezing length']
vuosi0 = 2012
vuosi1 = 2019
ftluvut = [0,1,2]

def viimeistele(tulos, nimi, xnimet, ynimi):
    ax = gca()
    xs = tulos['xsij']
    lf = len(ftluvut)
    lj = len(tulos['mediaanit']) // lf
    for i in range(1, lj):
        ax.axvline(np.mean([xs[i*lf], xs[i*lf-1]]))

    grid('on', axis='y')
    ylabel(ynimi)
    xticks(tulos['xsij'], labels=xnimet.flatten())
    tight_layout()

    if '-s' in sys.argv:
        savefig("kuvia/%s_%s_laatikko.png" %(ynimi.replace(' ','-'), nimi))
        clf()
    else:
        show()

def main():
    rcParams.update({'figure.figsize':(9,7), 'font.size':14})
    ikirluvut  = [0,1,2,3]
    paivadata  = [Dataset("kausien_pituudet%i.nc" %(i), "r") for i in ftluvut]
    koppdata   = np.tile(np.load("köppenmaski.npy"), vuosi1-vuosi0)
    ikirdata_  = Dataset("ikirdata.nc", "r")
    ikirvuodet = ikirdata_['vuosi'][:]
    ikirdata   = ikirdata_['luokka'][(vuosi0<=ikirvuodet) & (ikirvuodet<vuosi1)][...].flatten()
    ikirdata_.close()

    painot = np.array([SPINTAALA(lat) for lat in paivadata[0]['lat'][:]])
    painot = np.tile(np.repeat(painot, 360), vuosi1-vuosi0)
    for i_muutt in range(len(al_muuttuja)):
        painostot_ikir = np.empty([len(ikirluvut),len(ftluvut)], object)
        pdatastot_ikir = np.empty_like(painostot_ikir)
        xnimet_ikir    = np.empty_like(painostot_ikir)
        painostot_kopp = np.empty([len(luokat.kopp),len(ftluvut)], object)
        pdatastot_kopp = np.empty_like(painostot_kopp)
        xnimet_kopp    = np.empty_like(painostot_kopp)

        for i_ft in range(len(ftluvut)):
            vuodet     = paivadata[i_ft]['vuosi'][:]
            vuosimaski = (vuosi0<=vuodet) & (vuodet<vuosi1)
            data_      = np.ma.getdata(paivadata[i_ft][al_muuttuja[i_muutt]][:][vuosimaski].flatten())

            for i_luok in range(len(ikirluvut)):
                luokmaski  = ikirdata == ikirluvut[i_luok]
                data_luok  = data_[luokmaski]
                paino_luok = painot[luokmaski]
                datamaski  = data_luok == data_luok
                data_luok  = data_luok[datamaski]
                paino_luok = paino_luok[datamaski]
                pdatastot_ikir[i_luok,i_ft] = data_luok
                painostot_ikir[i_luok,i_ft] = paino_luok
                xnimet_ikir[   i_luok,i_ft] = "data%i%s" %(ftluvut[i_ft],
                                                           '' if i_ft != len(ftluvut)//2 else '\n'+luokat.ikir[i_luok])

            for i_luok in range(len(luokat.kopp)):
                luokmaski  = koppdata[i_luok,:]
                data_luok  = data_[luokmaski]
                paino_luok = painot[luokmaski]
                datamaski  = data_luok == data_luok
                data_luok  = data_luok[datamaski]
                paino_luok = paino_luok[datamaski]
                pdatastot_kopp[i_luok,i_ft] = data_luok
                painostot_kopp[i_luok,i_ft] = paino_luok
                xnimet_kopp[   i_luok,i_ft] = "data%i%s" %(ftluvut[i_ft],
                                                           '' if i_ft != len(ftluvut)//2 else '\n'+luokat.kopp[i_luok])

        tulos = laatikkokuvaaja(pdatastot_ikir.flatten(), fliers='', painostot=painostot_ikir.flatten())
        viimeistele(tulos, "ikir", xnimet_ikir, al_nimi[i_muutt])
        tulos = laatikkokuvaaja(pdatastot_kopp.flatten(), fliers='', painostot=painostot_kopp.flatten())
        viimeistele(tulos, "kopp", xnimet_kopp, al_nimi[i_muutt])

    for p in paivadata:
        p.close()

if __name__=='__main__':
    from warnings import filterwarnings
    filterwarnings(action='ignore', category=DeprecationWarning, message='`np.bool` is a deprecated alias')
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

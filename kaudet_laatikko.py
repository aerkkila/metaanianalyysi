#!/usr/bin/python3
import numpy as np
from netCDF4 import Dataset
from laatikkokuvaaja import laatikkokuvaaja
from matplotlib.pyplot import *
import luokat, sys

aste = 0.0174532925199
SPINTAALA = lambda _lat: np.sin((_lat+1)*aste) - np.sin(_lat*aste)

al_muuttuja = ['jaatym_alku','talven_alku','talven_loppu','freezing','winter','summer',]
al_nimi = ['freezing_start', 'winter_start', 'summer_start','freezing_length','winter_length','summer_length']
vuosi0 = 2012
vuosi1 = 2021

def viimeistele(tulos, nimi, xnimet, ynimi):
    ax = gca()
    xs = tulos['xsij']
    grid('on', axis='y')
    ylabel(ynimi)
    xticks(tulos['xsij'], labels=[s.replace('_',' ') for s in xnimet.flatten()])
    tight_layout()

    if '-s' in sys.argv:
        nimi="kuvia/kausilaatikko_%s_%s.png" %(ynimi.replace(' ','-'), nimi)
        savefig(nimi)
        clf()
    else:
        show()

def toimikoon_ikirouta(ikirdata):
    e0 = ikirdata['vuosi'][:][0] - vuosi0
    e1 = vuosi1-1 - ikirdata['vuosi'][:][-1]
    muoto = list(ikirdata['luokka'].shape)
    muoto[0] += e0+e1
    uusi = np.empty(muoto, np.int8)
    pit = vuosi1-vuosi0
    data = np.ma.getdata(ikirdata['luokka'][:])

    if e0 <= 0 and e1 >= 0:
        assert(-e0+pit-e1 == data.shape[0])
        uusi[:pit-e1, ...] = data[-e0:, ...]
        uusi[pit-e1:, ...] = np.tile(data[-1, ...], [uusi.shape[0]-(pit-e1), 1, 1])
        return uusi

    print("tämä ei toimi")
    sys.exit()

def main():
    rcParams.update({'figure.figsize':(5,7), 'font.size':14})
    ikirluvut  = [0,1,2,3]
    päivädata  = Dataset("kausien_pituudet2.nc", "r")
    köppdata   = np.tile(np.load("köppenmaski.npy"), vuosi1-vuosi0)
    ikirdata_  = Dataset("ikirdata.nc", "r")
    ikirvuodet = ikirdata_['vuosi'][:]
    ikirdata   = toimikoon_ikirouta(ikirdata_).flatten()
    ikirdata_.close()

    painot = np.array([SPINTAALA(lat) for lat in päivädata['lat'][:]])
    painot = np.tile(np.repeat(painot, 360), vuosi1-vuosi0)

    #xnimet_ikir = ['%s%s' %('\n'*max((i%3),(i%2)), s) for i,s in enumerate(luokat.ikir)]
    xnimet_ikir = ['PF%i' %i for i in range(4)]
    xnimet_köpp = luokat.kopp

    for i_muutt,muutt in enumerate(al_muuttuja):
        painostot_ikir = np.empty([len(ikirluvut)], object)
        pdatastot_ikir = np.empty_like(painostot_ikir)
        painostot_köpp = np.empty([len(luokat.kopp)], object)
        pdatastot_köpp = np.empty_like(painostot_köpp)

        vuodet     = päivädata['vuosi'][:]
        vuosimaski = (vuosi0<=vuodet) & (vuodet<vuosi1)
        data_      = np.ma.getdata(päivädata[muutt][:][vuosimaski].flatten())

        for i_luok in range(len(ikirluvut)):
            luokmaski  = ikirdata == ikirluvut[i_luok]
            data_luok  = data_[luokmaski]
            paino_luok = painot[luokmaski]
            datamaski  = data_luok == data_luok
            data_luok  = data_luok[datamaski]
            paino_luok = paino_luok[datamaski]
            pdatastot_ikir[i_luok] = data_luok
            painostot_ikir[i_luok] = paino_luok

        for i_luok in range(len(luokat.kopp)):
            luokmaski  = köppdata[i_luok,:]
            data_luok  = data_[luokmaski]
            paino_luok = painot[luokmaski]
            datamaski  = data_luok == data_luok
            data_luok  = data_luok[datamaski]
            paino_luok = paino_luok[datamaski]
            pdatastot_köpp[i_luok] = data_luok
            painostot_köpp[i_luok] = paino_luok

        #tulos = laatikkokuvaaja(pdatastot_ikir.flatten(), fliers='', painostot=painostot_ikir.flatten())
        #viimeistele(tulos, "ikir", xnimet_ikir, al_nimi[i_muutt))
        #tulos = laatikkokuvaaja(pdatastot_köpp.flatten(), fliers='', painostot=painostot_köpp.flatten())
        #viimeistele(tulos, "köpp", xnimet_köpp, al_nimi[i_muutt])
        tulos = laatikkokuvaaja(np.concatenate([pdatastot_ikir.flatten(), pdatastot_köpp.flatten()]),
                                fliers='',
                                painostot = np.concatenate([painostot_ikir.flatten(), painostot_köpp.flatten()]))
        viimeistele(tulos, "ikirköpp", np.concatenate([xnimet_ikir, xnimet_köpp]), al_nimi[i_muutt].replace('_',' '))

    päivädata.close()

if __name__=='__main__':
    from warnings import filterwarnings
    filterwarnings(action='ignore', category=DeprecationWarning, message='`np.bool` is a deprecated alias')
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

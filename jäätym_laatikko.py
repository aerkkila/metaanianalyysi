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

def main():
    rcParams.update({'figure.figsize':(9,7), 'font.size':14})
    ftluvut    = [0,1,2]
    ikirluvut  = [0,1,2,3]
    paivadata  = [Dataset("kausien_pituudet%i.nc" %(i), "r") for i in ftluvut]
    ikirdata_  = Dataset("ikirdata.nc", "r")
    ikirvuodet = ikirdata_['vuosi'][:]
    ikirdata   = ikirdata_['luokka'][(vuosi0<=ikirvuodet) & (ikirvuodet<vuosi1)][...].flatten()
    ikirdata_.close()

    painot = np.array([SPINTAALA(lat) for lat in paivadata[0]['lat'][:]])
    painot = np.tile(np.repeat(painot, 360), vuosi1-vuosi0)
    for i_muutt in range(len(al_muuttuja)):
        painostot = np.empty([len(ikirluvut),len(ftluvut)], object)
        pdatastot = np.empty_like(painostot)
        xnimet    = np.empty_like(painostot)
        for i_ikir in range(len(ikirluvut)):
            for i_ft in range(len(ftluvut)):
                vuodet     = paivadata[i_ft]['vuosi'][:]
                vuosimaski = (vuosi0<=vuodet) & (vuodet<vuosi1)
                ikirmaski  = ikirdata == ikirluvut[i_ikir]
                data_      = np.ma.getdata(paivadata[i_ft][al_muuttuja[i_muutt]][:][vuosimaski].flatten()[ikirmaski])
                paino_     = painot[ikirmaski]
                datamaski  = data_ == data_
                data_      = data_[datamaski]
                paino_     = paino_[datamaski]
                pdatastot[i_ikir,i_ft] = data_
                painostot[i_ikir,i_ft] = paino_
                xnimet[   i_ikir,i_ft] = "data%i%s" %(ftluvut[i_ft], '' if i_ft != len(ftluvut)//2 else '\n'+luokat.ikir[i_ikir])
        tulos = laatikkokuvaaja(pdatastot.flatten(), fliers='', painostot=painostot.flatten())

        ax = gca()
        xs = tulos['xsij']
        lf = len(ftluvut)
        for i in range(1, len(ikirluvut)):
            ax.axvline(np.mean([xs[i*lf], xs[i*lf-1]]))

        grid('on', axis='y')
        ylabel(al_nimi[i_muutt])
        xticks(tulos['xsij'], labels=xnimet.flatten())
        tight_layout()
        if '-s' in sys.argv:
            savefig("kuvia/%s_laatikko.png" %(al_nimi[i_muutt].replace(' ','-')))
            clf()
        else:
            show()

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

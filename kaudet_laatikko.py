#!/usr/bin/python3
import numpy as np
from netCDF4 import Dataset
from laatikkokuvaaja import laatikkokuvaaja
from matplotlib.pyplot import *
import luokat, sys, time

aste = 0.0174532925199
SPINTAALA = lambda _lat: np.sin((_lat+1)*aste) - np.sin(_lat*aste)

kaudet = luokat.kaudet[1:]
pd_muuttujat = [['%s_start' %k, '%s_end' %k] for k in kaudet]
vuosi0 = 2012
vuosi1 = 2021

def muunna_aika(lista):
    r = np.empty(len(lista), object)
    for i in range(len(r)):
        tämä = time.localtime(time.mktime(time.struct_time((2002,1,int(lista[i])+1,0,0,0,0,1,0)))) # oispa C
        r[i] = time.strftime("%m-%d", tämä)
    return r

def viimeistele(tulos, nimi, xnimet, ynimi):
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
    päivädata  = Dataset("kausien_päivät.nc", "r")
    köppdata   = np.tile(np.load("köppenmaski.npy"), vuosi1-vuosi0)
    ikirdata_  = Dataset("ikirdata.nc", "r")
    ikirvuodet = ikirdata_['vuosi'][:]
    ikirdata   = toimikoon_ikirouta(ikirdata_).flatten()
    ikirdata_.close()

    painot = np.array([SPINTAALA(lat) for lat in päivädata['lat'][:]])
    painot = np.tile(np.repeat(painot, 360), vuosi1-vuosi0)

    xnimet_ikir = ['PF%i' %i for i in range(4)]
    xnimet_köpp = luokat.köpp

    for kausi,muutt in zip(kaudet, pd_muuttujat):
        painostot_ikir = np.empty([len(ikirluvut)], object)
        pdatastot_ikir = np.empty_like(painostot_ikir)
        painostot_köpp = np.empty([len(luokat.kopp)], object)
        pdatastot_köpp = np.empty_like(painostot_köpp)

        vuodet     = päivädata['vuosi'][:]
        vuosimaski = (vuosi0<=vuodet) & (vuodet<vuosi1)
        loput      = np.ma.getdata(päivädata[muutt[1]][:][vuosimaski]).flatten()
        alut       = np.ma.getdata(päivädata[muutt[0]][:][vuosimaski]).flatten()
        pitdet     = loput-alut

        for dt,nimi in zip([alut,pitdet], ['start','length']):
            for iluok in range(len(ikirluvut)):
                maski  = ikirdata == ikirluvut[iluok]
                pdatastot_ikir[iluok] = dt[maski]
                painostot_ikir[iluok] = painot[maski]
                maski = pdatastot_ikir[iluok] == pdatastot_ikir[iluok]
                pdatastot_ikir[iluok] = pdatastot_ikir[iluok][maski]
                painostot_ikir[iluok] = painostot_ikir[iluok][maski]

            for iluok in range(len(luokat.köpp)):
                maski  = ikirdata == ikirluvut[iluok]
                pdatastot_köpp[iluok] = dt[maski]
                painostot_köpp[iluok] = painot[maski]
                maski = pdatastot_köpp[iluok] == pdatastot_köpp[iluok]
                pdatastot_köpp[iluok] = pdatastot_köpp[iluok][maski]
                painostot_köpp[iluok] = painostot_köpp[iluok][maski]

            tulos = laatikkokuvaaja(np.concatenate([pdatastot_ikir.flatten(), pdatastot_köpp.flatten()]),
                                    fliers='', avgmarker='o',
                                    painostot = np.concatenate([painostot_ikir.flatten(), painostot_köpp.flatten()]))
            viimeistele(tulos, "ikirköpp", np.concatenate([xnimet_ikir, xnimet_köpp]), '%s %s' %(kausi, nimi))

    päivädata.close()

if __name__=='__main__':
    from warnings import filterwarnings
    filterwarnings(action='ignore', category=DeprecationWarning, message='`np.bool` is a deprecated alias')
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

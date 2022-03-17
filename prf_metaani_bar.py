#!/usr/bin/python3
import xarray as xr
import numpy as np
from numpy import sin
from configure import tyotiedostot
from matplotlib.pyplot import *
import prf_extent as prf
import sys

def argumentit(argv):
    global tarkk,verbose,tallenna
    tarkk = 5
    verbose = False
    tallenna = False
    i=1
    while i<len(argv):
        a = argv[i]
        if a == '-t':
            i += 1
            tarkk = int(argv[i])
        elif a == '-v':
            verbose = True
        elif a == '-s':
            tallenna = True
        else:
            print("Varoitus: tuntematon argumentti \"%s\"" %a)
        i += 1
    return

_viimelat1x1 = np.nan
def pintaala1x1(lat):
    global _viimelat1x1, _viimeala1x1
    if lat == _viimelat1x1:
        return _viimeala1x1
    _viimelat1x1 = lat
    aste = 0.0174532925199
    R2 = 40592558970441
    _viimeala1x1 = aste*R2*( sin((lat+1)*aste) - sin(lat*aste) )*1.0e-6
    return _viimeala1x1

class Vuo():
    def __init__(self,osdet,vuot,alat):
        self.osdet = osdet
        self.vuot = vuot
        self.alat = alat
        return
    def __str__(self):
        vari0 = '\033[0m'
        vari1 = '\033[1;33m'
        vari2 = '\033[1;32m'
        return ('%sVuo ja ikirouta:%s\n' %(vari2,vari0) +
                f'%sosuudet:%s\n{self.osdet}\n' %(vari1,vari0) +
                f'%svuot:%s\n{self.vuot}\n' %(vari1,vari0) +
                f'%salat:%s\n{self.alat}\n' %(vari1,vari0))

def laske_vuot():
    alku = int(ikirouta.min())
    loppu = int(ikirouta.max())
    osuudet = np.arange(alku,loppu+tarkk,tarkk)
    #luettava data
    ikirflat = ikirouta.data.flatten()
    latflat = np.meshgrid( ikirouta.lon.data, ikirouta.lat.data )[1].flatten()
    vuoflat = vuodata.data.flatten()
    #kirjoitettava data
    vuot = np.zeros(len(osuudet))
    alat = np.zeros(len(osuudet))
    for i in range(len(ikirflat)):
        ala = pintaala1x1(latflat[i])
        #pyöristettäköön indeksi ylöspäin, jotta 0 % on oma luokkansa ja 100 % sisältyy 100-ε %:in
        ind = int(np.ceil( (ikirflat[i]-alku) / tarkk ))
        alat[ind] += ala
        vuot[ind] += vuoflat[i]*ala
    return Vuo(osuudet,vuot,alat)

if __name__ == '__main__':
    rcParams.update({'font.size':13,'figure.figsize':(10,8)})
    argumentit(sys.argv)
    ncmuuttuja = 'posterior_bio'
    tiedosto = 'FT_implementointi/Results_LPX2019/flux1x1_LPX2019_FTimpl_S3_bio_antro_tot.nc'
    vuodata = xr.open_dataset(tyotiedostot+tiedosto)[ncmuuttuja].mean(dim='time')
    ikiroutaolio = prf.Prf('1x1')#.rajaa([vuodata.lat.min(),vuodata.lat.max()+1]) #rajaus on jo oikein
    ikirouta = ikiroutaolio.data.mean(dim='time')

    vuoolio = laske_vuot()
    if verbose:
        print(vuoolio)
    fig = figure()
    palkit = bar( vuoolio.osdet, vuoolio.vuot/vuoolio.alat )
    tight_layout()
    show()

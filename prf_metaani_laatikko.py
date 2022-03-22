#!/usr/bin/python3
import xarray as xr
import pandas as pd
from numpy import sin
import numpy as np
from config import edgartno_lpx_muutt, edgartno_lpx_tied
from matplotlib.pyplot import *
import prf as prf
import sys, warnings

def argumentit(argv):
    global tarkk,verbose,tallenna,latraja
    tarkk = 5; verbose = False; tallenna = False; latraja = 50
    i=1
    while i<len(argv):
        a = argv[i]
        if a == '-v':
            verbose = True
        elif a == '-s':
            tallenna = True
        elif a == '-t':
            i += 1
            tarkk = int(argv[i])
        elif a == '-l0':
            i += 1
            latraja = int(argv[i])
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
    _viimeala1x1 = aste*R2*( sin((lat+1)*aste) - sin(lat*aste) )
    return _viimeala1x1

class Vuo():
    def __init__(self,osdet,vuot,alat):
        self.osdet = osdet
        self.vuot = vuot
        self.alat = alat
        self.vari0 = '\033[0m'
        self.vari1 = '\033[1;32m'
        self.vari2 = '\033[1;33m'
        return
    def __str__(self):
        return ('%sVuo ja ikirouta:%s\n' %(self.vari1,self.vari0) +
                f'%sosuudet:%s\n{self.osdet}\n' %(self.vari2,self.vari0) +
                f'%svuot:%s\n{self.vuot}\n' %(self.vari2,self.vari0) +
                f'%salat:%s\n{self.alat}\n' %(self.vari2,self.vari0))

def laske_vuot(vuodata):
    alku = int(ikirouta.min())
    loppu = int(ikirouta.max())
    osuudet = np.arange(alku,loppu+tarkk,tarkk)
    #luettava data
    ikirflat = ikirouta.data.flatten()
    latflat = np.meshgrid( ikirouta.lon.data, ikirouta.lat.data )[1].flatten()
    vuoflat = vuodata.data.flatten()
    #kirjoitettava data
    vuot = []
    [ vuot.append([]) for i in range(len(osuudet)) ]
    #alat = vuot.copy()
    for i in range(len(ikirflat)):
        ala = pintaala1x1(latflat[i])
        #pyöristettäköön indeksi ylöspäin, jotta 0 % on oma luokkansa ja 100 % sisältyy 100-ε %:in
        ind = int(np.ceil( (ikirflat[i]-alku) / tarkk ))
        #alat[ind].append(ala)
        vuot[ind].append(vuoflat[i])
    vuonp = np.empty([len(vuot), max(len(v) for v in vuot)]) + np.nan
    for i in range(len(vuot)):
        for j in range(len(vuot[i])):
            vuonp[i,j] = vuot[i][j]
    vuodf = pd.DataFrame(vuonp.T,columns=osuudet)
    return Vuo(osuudet,vuodf,None)

if __name__ == '__main__':
    rcParams.update({'font.size':13,'figure.figsize':(10,8)})
    argumentit(sys.argv)
    ikiroutaolio = prf.Prf('1x1').rajaa([latraja,90])
    ikirouta = ikiroutaolio.data.mean(dim='time')

    vuodata = xr.open_dataset(edgartno_lpx_tied)[edgartno_lpx_muutt].mean(dim='record').loc[latraja:,:]
    vuoolio = laske_vuot(vuodata)
    vuodata.close()

    if verbose:
        print(vuoolio)

    with warnings.catch_warnings():
         warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)
         vuoolio.vuot.boxplot(whis=(5,95))
    if tallenna:
        savefig('kuvia/%s.png' %sys.argv[0][:-3])
    else:
        show()

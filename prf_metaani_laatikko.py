#!/usr/bin/python3
import xarray as xr
import pandas as pd
from numpy import sin
import numpy as np
from matplotlib.pyplot import *
import prf
import sys, warnings
from wetlandtyypin_pisteet import valitse_painottaen

def argumentit(argv):
    global tarkk,verbose,tallenna
    tarkk = 25; verbose = False; tallenna = False
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
        else:
            print("Varoitus: tuntematon argumentti \"%s\"" %a)
        i += 1
    return

class Vuo():
    def __init__(self,osdet,vuot):
        self.osdet = osdet
        self.vuot = vuot
        self.vari0 = '\033[0m'
        self.vari1 = '\033[1;32m'
        self.vari2 = '\033[1;33m'
        return
    def __str__(self):
        return ('%sVuo ja ikirouta:%s\n' %(self.vari1,self.vari0) +
                f'%sosuudet:%s\n{self.osdet}\n' %(self.vari2,self.vari0) +
                f'%svuot:%s\n{self.vuot}\n' %(self.vari2,self.vari0))

def laske_vuot(vuodata, monistus):
    alku = int(ikirouta.min())
    loppu = int(ikirouta.max())
    osuudet = np.arange(alku,loppu+tarkk,tarkk)
    #luettava data
    latflat = np.meshgrid( ikirouta.lon.data, ikirouta.lat.data )[1].flatten()
    indeksit = valitse_painottaen(latflat[wetlmaski], 8)
    latflat = latflat[wetlmaski][indeksit]
    ikirflat = ikirouta.data.flatten()[wetlmaski][indeksit]
    vuoflat = vuodata.data.flatten()[wetlmaski][indeksit]
    #kirjoitettava data
    vuot = []
    [ vuot.append([]) for i in range(len(osuudet)) ]
    for i in range(len(ikirflat)):
        #pyöristettäköön indeksi ylöspäin, jotta 0 % on oma luokkansa ja 100 % sisältyy 100-ε %:in
        ind = int(np.ceil( (ikirflat[i]-alku) / tarkk ))
        vuot[ind].append(vuoflat[i])
    vuonp = np.empty([len(vuot), max(len(v) for v in vuot)]) + np.nan
    for i in range(len(vuot)):
        for j in range(len(vuot[i])):
            vuonp[i,j] = vuot[i][j]
    vuodf = pd.DataFrame(vuonp.T,columns=osuudet)
    return Vuo(osuudet,vuodf)

if __name__ == '__main__':
    rcParams.update({'font.size':13,'figure.figsize':(10,8)})
    argumentit(sys.argv)
    vuodata = xr.open_dataset('./flux1x1_summer.nc')['flux_bio_posterior'].mean(dim='time')
    bawdata = xr.open_dataset('./BAWLD1x1.nc')['wetland']
    ikiroutaolio = prf.Prf('1x1').rajaa([vuodata.lat.min(),vuodata.lat.max()+0.01])
    ikirouta = ikiroutaolio.data.mean(dim='time')
    bawdata = bawdata.sel({'lat':slice(vuodata.lat.min(),vuodata.lat.max()+0.01)})
    wetlmaski = bawdata.data.flatten() >= 0.05
    vuodata = vuodata.where(vuodata==vuodata, np.nan)
    maksimi = vuodata.max()
    vuodata = vuodata.where(vuodata.lon<0,np.nan)
    vuoolio = laske_vuot(vuodata, 8)
    vuodata.close()
    if verbose:
        print(vuoolio)

    with warnings.catch_warnings():
         warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)
         vuoolio.vuot.boxplot(whis=(5,95))
    xlabel('% permafrost')
    ylabel('CH$_4$ flux (mol/m$^2$/s)')
    ylim(top=maksimi)
    if tallenna:
        savefig('kuvia/%s.png' %sys.argv[0][:-3])
    else:
        show()
    bawdata.close()
    vuodata.close()

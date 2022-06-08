#!/usr/bin/python3
import xarray as xr
import pandas as pd
from numpy import sin
import numpy as np
from matplotlib.pyplot import *
import prf
import sys, warnings
from wetlandtyypin_pisteet import valitse_painottaen

def laske_vuot(vuodata, ikirouta, monistus, osuudet, wetlmaski):
    #luettava data
    alku = osuudet[0]
    loppu = osuudet[-1]
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
    return [osuudet,vuodf]

def main():
    rcParams.update({'font.size':13,'figure.figsize':(10,8)})
    vuodata = xr.open_dataset('./flux1x1_summer.nc')['flux_bio_posterior'].mean(dim='time')
    bawdata = xr.open_dataset('./BAWLD1x1.nc')['wetland']
    ikiroutaolio = prf.Prf('1x1').rajaa([vuodata.lat.min(),vuodata.lat.max()+0.01])
    ikirouta = ikiroutaolio.data.mean(dim='time')
    bawdata = bawdata.sel({'lat':slice(vuodata.lat.min(),vuodata.lat.max()+0.01)})
    wetlmaski = bawdata.data.flatten() >= 0.05
    bawdata.close()
    vuodata = vuodata.where(vuodata==vuodata, np.nan)
    maksimi = vuodata.max()
    vuodata = vuodata.where(vuodata.lon<0,np.nan)
    alku = int(ikirouta.min())
    loppu = int(ikirouta.max())
    osuudet = np.arange(alku,loppu+25,25)
    osuudet,vuot = laske_vuot(vuodata, ikirouta, 8, osuudet, wetlmaski)
    vuodata.close()

    with warnings.catch_warnings():
         warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)
         vuot.boxplot(whis=(5,95))
    xlabel('% permafrost')
    ylabel('CH$_4$ flux (mol/m$^2$/s)')
    ylim(top=maksimi)
    if '-s' in sys.argv:
        savefig('kuvia/%s.png' %sys.argv[0][:-3])
    else:
        show()

if __name__ == '__main__':
    main()

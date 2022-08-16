#!/usr/bin/python3
import xarray as xr
import pandas as pd
from numpy import sin
import numpy as np
from matplotlib.pyplot import *
import sys, warnings, luokat
from wetlandtyypin_pisteet import valitse_painottaen
from multiprocessing import Process

def laske_vuot(vuodata, ikirouta, monistus, wetlmaski):
    #luettava data
    latflat  = np.meshgrid(ikirouta.lon.data, ikirouta.lat.data)[1].flatten()
    indeksit = valitse_painottaen(latflat[wetlmaski], 8)
    latflat  = latflat[wetlmaski][indeksit]
    ikirflat = ikirouta.data.flatten()[wetlmaski][indeksit]
    vuoflat  = vuodata.data.flatten()[indeksit]
    vuoflat *= 1
    #kirjoitettava data
    vuot = np.empty(len(luokat.ikir), object)
    for i in range(len(luokat.ikir)):
        vuot[i] = vuoflat[ikirflat==i]
    vuonp = np.empty([len(vuot), max(len(v) for v in vuot)]) + np.nan
    for i in range(len(vuot)):
        for j in range(len(vuot[i])):
            vuonp[i,j] = vuot[i][j]
    vuodf = pd.DataFrame(vuonp.T, columns=luokat.ikir)
    return vuodf

def aja(vuodata0, ikirouta, ialue, alue):
    if ialue == 0:
        vuodata = vuodata0
    elif ialue == 1:
        vuodata = vuodata0.where(vuodata0.lon<0, np.nan)
    else:
        vuodata = vuodata0.where(vuodata0.lon>=0, np.nan)
    maksimi = vuodata.max()
    vuot = laske_vuot(vuodata, ikirouta, 8, ...)
    vuodata.close()
    for i,l in enumerate(luokat.ikir):
        if i%2:
            luokat.ikir[i] = '\n'+l
    vuot.columns = luokat.ikir

    with warnings.catch_warnings():
         warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)
         vuot.boxplot(whis=(5,95))
    gca().get_yaxis().labelpad = 15
    ylabel(r'$\frac{\mathrm{mol}}{\mathrm{m}^2\mathrm{s}}$', fontsize=18, rotation=0)
    ylim(top=maksimi)
    if(ialue):
        title(alue[1:])
    tight_layout()
    if '-s' in sys.argv:
        savefig('kuvia/%s%s.png' %(sys.argv[0][:-3], alue))
    else:
        show()

def main():
    rcParams.update({'font.size':13,'figure.figsize':(5,8)})
    vuodata  = xr.open_dataset('./flux1x1.nc')['flux_bio_posterior'].mean(dim='time')
    ikirouta = xr.open_dataset('./ikirdata.nc')['luokka'].sel({"lat":slice(29.5,84)})
    ikirouta = ikirouta.mean(dim='vuosi').round().astype(np.int8)
    pr = np.empty(3, object)
    for ialue,alue in enumerate(['','_west','_east']):
        pr[ialue] = Process(target=aja, args=[vuodata, ikirouta, ialue, alue])
        pr[ialue].start()
    for p in pr:
        p.join()

if __name__ == '__main__':
    main()

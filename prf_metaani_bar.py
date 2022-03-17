#!/usr/bin/python3
import xarray as xr
import numpy as np
from numpy import sin
from configure import tyotiedostot
from matplotlib.pyplot import *
import prf_extent as prf
import sys

def argumentit(argv):
    global tarkk
    tarkk = 5
    i=1
    while i<len(argv):
        a = argv[i]
        if a == '-t':
            i += 1
            tarkk = int(argv[i])
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

def laske_vuot():
    alku = int(ikirouta.min())
    loppu = int(ikirouta.max())
    osuudet = np.arange(alku,loppu+1,tarkk)
    #luettava data
    ikirflat = ikirouta.data.flatten()
    latflat = np.meshgrid( ikirouta.lon.data, ikirouta.lat.data )[1].flatten()
    vuoflat = vuodata.data.flatten()
    #kirjoitettava data
    vuot = np.zeros(len(osuudet))
    alat = np.zeros(len(osuudet))
    for i in range(len(ikirflat)):
        ala = pintaala1x1(latflat[i])
        ind = int(np.floor( (ikirflat[i]-alku) / tarkk ))
        alat[ind] += ala
        vuot[ind] += vuoflat[i]*ala
    return osuudet, vuot, alat

if __name__ == '__main__':
    rcParams.update({'font.size':13,'figure.figsize':(10,8)})
    argumentit(sys.argv)
    ncmuuttuja = 'posterior_bio'
    tiedosto = 'FT_implementointi/Results_LPX2019/flux1x1_LPX2019_FTimpl_S3_bio_antro_tot.nc'
    vuodata = xr.open_dataset(tyotiedostot+tiedosto)[ncmuuttuja].mean(dim='time')
    ikiroutaolio = prf.Prf('1x1')#.rajaa([vuodata.lat.min(),vuodata.lat.max()+1])
    ikirouta = ikiroutaolio.data.mean(dim='time')

    ikir_osuus, vuo, ala = laske_vuot()
    fig = figure()
    palkit = bar( ikir_osuus, vuo/ala )
    tight_layout()
    show()

#!/usr/bin/python3
import numpy as np
from numpy import sin
from matplotlib.pyplot import *
import talven_ajankohta as taj
import prf_extent as prf

def argumentit():
    global startend, tallenna
    tallenna = False
    startend = 'start'
    for a in sys.argv:
        if a == '-s':
            tallenna = True
        elif a == 'start' or a == 'end':
            startend = a
    return

def pintaalat1x1(darr):
    aste = 0.0174532925199
    R2 = 40592558970441
    PINTAALA = lambda _lat: aste*R2*( sin((_lat+1)*aste) - sin(_lat*aste) )*1.0e-6
    
    dat = darr.data.flatten().astype(int)
    minluku = int(darr.min())
    maxluku = int(darr.max())
    lukualat = np.zeros( maxluku - minluku + 1 )
    for j,la in enumerate(darr.lat.data):
        ala = PINTAALA(la)
        lonarr = dat[ j*darr.lon.size : (j+1)*darr.lon.size ]
        lonarr = lonarr[lonarr >= minluku]
        for luku in lonarr:
            lukualat[luku-minluku] += ala
    return np.arange(minluku,maxluku+1), lukualat

def piirra_histogrammi(darr): #xarray.DataArray
    xarr,yarr = pintaalat1x1(darr) #olisiko argumenttina myös tarkkuus?
    plot(xarr,yarr)
    show()

if __name__ == '__main__':
    argumentit()
    rcParams.update({'font.size':13,'figure.figsize':(12,10)})
    doy = taj.lue_avgdoy(startend)
    ikirouta = prf.Prf('1x1').rajaa( (doy.lat.min(), doy.lat.max()+1) )
    ikirstr = prf.luokittelu_str_xr(ikirouta.data.mean(dim='time'))

    piirra_histogrammi(doy.where(ikirstr, np.nan))

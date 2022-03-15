#!/usr/bin/python3
import numpy as np
from numpy import sin
from matplotlib.pyplot import *
import talven_ajankohta as taj
import prf_extent as prf

def argumentit():
    global startend, tallenna, tarkk
    tallenna = False
    startend = 'start'
    tarkk = 1
    for i in range(len(sys.argv)):
        a = sys.argv[i]
        if a == '-s':
            tallenna = True
        elif a == 'start' or a == 'end':
            startend = a
        elif a == '-t' or a == '--tarkkuus':
            i += 1
            tarkk = int(sys.argv[i])
    return

def pintaalat1x1(darr,tarkk):
    aste = 0.0174532925199
    R2 = 40592558970441
    PINTAALA = lambda _lat: aste*R2*( sin((_lat+1)*aste) - sin(_lat*aste) )*1.0e-6
    
    dat = darr.data.flatten().astype(int)
    minluku = int(darr.min())
    maxluku = int(darr.max())
    lukualat = np.zeros( (maxluku - minluku) // tarkk + 1 )
    for j,la in enumerate(darr.lat.data):
        ala = PINTAALA(la)
        lonarr = dat[ j*darr.lon.size : (j+1)*darr.lon.size ]
        lonarr = lonarr[lonarr >= minluku]
        for luku in lonarr.astype(int):
            lukualat[(luku-minluku)//tarkk] += ala
    return np.arange(minluku,maxluku+1,tarkk), lukualat

def piirra_histogrammi(darr): #xarray.DataArray
    xarr,yarr = pintaalat1x1(darr,tarkk)
    plot(xarr,yarr/1000/tarkk,'.')
    xlabel('winter %s doy' %startend)
    ylabel('extent (1000 km$^2$ / %s day)' %startend)
    
    tight_layout()
    show()

if __name__ == '__main__':
    argumentit()
    rcParams.update({'font.size':13,'figure.figsize':(12,10)})
    doy = taj.lue_avgdoy(startend)
    ikirouta = prf.Prf('1x1').rajaa( (doy.lat.min(), doy.lat.max()+1) )
    ikirstr = prf.luokittelu_str_xr(ikirouta.data.mean(dim='time'))

    piirra_histogrammi(doy.where(ikirstr, np.nan))

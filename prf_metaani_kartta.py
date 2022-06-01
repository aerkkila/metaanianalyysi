#!/usr/bin/python3
import xarray as xr
import numpy as np
from numpy import log
import pandas as pd
import cartopy.crs as ccrs
from matplotlib.pyplot import *
import matplotlib.colors as mcolors
from matplotlib.colors import ListedColormap as lcmap
import matplotlib, sys, prf
import config

varoitusvari = '\033[1;33m'
vari0 = '\033[0m'
ikir_ind = 0

def argumentit(argv):
    global tallenna,verbose
    tallenna=False; verbose=False
    i=0
    while i < len(argv):
        a = argv[i]
        if a == '-s':
            tallenna = True
        elif a == '-v':
            verbose = True
        else:
            print("%sVaroitus:%s tuntematon argumentti \"%s\"" %(varoitusvari,vari0,a))
        i+=1

def luo_varikartta(ch4data):
    global pienin,suurin
    pienin = np.nanpercentile(ch4data.data, 1)
    suurin = np.nanpercentile(ch4data.data,99)
    if verbose:
        print('pienin, prosenttipiste: ', ch4data.min().data, pienin)
        print('suurin, prosenttipiste: ', ch4data.max().data, suurin)
    N = 1024
    cmap = matplotlib.cm.get_cmap('coolwarm',N)
    varit = np.empty(N,object)
    kanta = 10

    #negatiiviset vuot lineaarisesti ja positiiviset logaritmisesti
    for i in range(0,N//2): #negatiiviset vuot
        varit[i] = cmap(i)
    cmaplis=np.logspace(log(0.5)/log(kanta),0,N//2)
    for i in range(N//2,N): #positiiviset vuot
        varit[i] = cmap(cmaplis[i-N//2])
    return lcmap(varit)


ulkovari = '#d0e0c0'
harmaavari = '#c0c0c0'
    
def piirra():
    ax = gca()
    ax.set_extent(kattavuus,platecarree)
    ax.coastlines()
    #Tämä asettaa maskin ulkopuolisen alueen eri väriseksi
    harmaa = lcmap(ulkovari)
    muu = xr.DataArray(data=np.zeros([kattavuus[3]-kattavuus[2],kattavuus[1]-kattavuus[0]]),
                       coords={ 'lat':np.arange(kattavuus[2]+0.5,kattavuus[3],1),
                                'lon':np.arange(kattavuus[0]+0.5,kattavuus[1],1), },
                       dims=['lat','lon'])
    muu.plot.pcolormesh(transform=platecarree, ax=gca(), cmap=harmaa, add_colorbar=False)
    #Varsinainen data
    ch4data.where(ikirouta==ikir_ind,np.nan).plot.\
        pcolormesh(transform=platecarree, cmap=vkartta, norm=mcolors.DivergingNorm(0,max(pienin*6,-suurin),suurin),
                   add_colorbar=False)
    #Tämä asettaa muut ikiroutaluokka-alueet harmaaksi.
    harmaa = lcmap(harmaavari)
    ch4data.where(~(ikirouta==ikir_ind),np.nan).plot.\
        pcolormesh( transform=platecarree, ax=gca(), add_colorbar=False, cmap=harmaa )
    title(prf.luokat[ikir_ind])

def varipalkki():
    cbar_nimio = r'CH$_4$ flux ($\frac{\mathrm{mol}}{\mathrm{m}^2\mathrm{s}}$)'
    norm = mcolors.DivergingNorm(0,max(pienin*6,-suurin),suurin)
    ax = axes((0.91,0.031,0.03,0.92))
    cbar = gcf().colorbar(matplotlib.cm.ScalarMappable(cmap=vkartta,norm=norm), label=cbar_nimio, cax=ax)
    #väripalkki ulkoalueista
    harmaa = lcmap([ulkovari,harmaavari])
    norm = matplotlib.colors.Normalize(vmin=-2, vmax=2)
    ax = axes((0.78,0.031,0.03,0.92))
    cbar = gcf().colorbar(matplotlib.cm.ScalarMappable(cmap=harmaa,norm=norm),ticks=[-1,1], cax=ax)
    cbar.set_ticklabels(['undefined', 'other\ncategories'])

def tee_alikuva(subplmuoto, subpl, **axes_kwargs):
    subpl_y = subplmuoto[0]-1 - subpl // subplmuoto[1]
    subpl_x = subpl % subplmuoto[1]
    xkoko = 0.77/subplmuoto[1]
    ykoko = 0.97/subplmuoto[0]
    ax = axes([0.02 + subpl_x*xkoko,
               0.03 + subpl_y*ykoko,
               xkoko-0.03, ykoko-0.05],
              **axes_kwargs)
    return ax

def main(tiedosto,muuttuja):
    global projektio,platecarree,kattavuus,ch4data,ikirouta,vkartta,ikir_ind
    rcParams.update({'font.size':18,'figure.figsize':(14,6),'text.usetex':True})
    argumentit(sys.argv[1:])
    kansio = config.tyotiedostot+'FT_implementointi/FT_percents_pixel_ease_flag/DOY/'

    ikirouta = xr.open_dataset('./prfdata.nc')['luokka']

    ch4data = xr.open_dataset(tiedosto)[muuttuja]
    ch4data = ch4data.mean(dim='time')
    
    ikirouta = ikirouta.sel({'time':range(2011,2019)}).mean(dim='time')
    ikirouta = ikirouta.sel({'lat':slice(ch4data.lat.min(),ch4data.lat.max())})

    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    kattavuus   = [-180,180,30,90]
    fig = figure()

    vkartta = luo_varikartta(ch4data)

    sca(tee_alikuva([1,2], 0, projection=projektio))
    piirra()
    ikir_ind=3
    sca(tee_alikuva([1,2], 1, projection=projektio))
    piirra()
    varipalkki()
    if not tallenna:
        show()
        return
    if verbose:
        print(prf.luokat[ikir_ind])
    savefig("kuvia/%s.png" %(sys.argv[0][:-3]))

if __name__ == '__main__':
    main('./flux1x1_whole_year.nc', 'flux_bio_posterior')

#!/usr/bin/python3
import xarray as xr
import numpy as np
from numpy import log
import cartopy.crs as ccrs
from matplotlib.pyplot import *
import matplotlib
import matplotlib.colors as mcolors
from matplotlib.colors import ListedColormap as lcmap
from config import edgartno_lpx_m, edgartno_lpx_t, tyotiedostot
import sys
import prf as prf
import talven_ajankohta as taj

def argumentit(argv):
    global tallenna,verbose,ikir_ind
    tallenna=False; verbose=False; ikir_ind=0
    i=1
    while i < len(argv):
        a = argv[i]
        if a == '-s':
            tallenna = True
        elif a == '-v':
            verbose = True
        else:
            print("%sVaroitus:%s tuntematon argumentti \"%s\"" %(varoitusvari,vari0,a))
        i+=1

def luo_varikartta():
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

def piirra():
    clf()
    ax = axes([0.01,0.01,1,0.95],projection=projektio)
    ax.set_extent(kattavuus,platecarree)
    ax.coastlines()
    #Tämä asettaa maskin ulkopuolisen alueen eri väriseksi
    harmaa = lcmap('#d0e0c0')
    muu = xr.DataArray(data=np.zeros([kattavuus[3]-kattavuus[2],kattavuus[1]-kattavuus[0]]),
                       coords={ 'lat':np.arange(kattavuus[2]+0.5,kattavuus[3],1),
                                'lon':np.arange(kattavuus[0]+0.5,kattavuus[1],1), },
                       dims=['lat','lon'])
    muu.plot.pcolormesh( transform=platecarree, ax=gca(), add_colorbar=False, cmap=harmaa )
    #Varsinainen data
    cbar_nimio = (r'%s ($\frac{\mathrm{mol}}{\mathrm{m}^2\mathrm{s}}$)' %edgartno_lpx_m).replace('_','\\_')
    ch4data.where(ikirluokat==prf.luokat1[ikir_ind],np.nan).plot.\
        pcolormesh( transform=platecarree, cmap=vkartta, norm=mcolors.DivergingNorm(0,max(pienin*6,-suurin),suurin),
                    cbar_kwargs={'label':cbar_nimio} )
    #Tämä asettaa muut ikiroutaluokka-alueet harmaaksi.
    harmaa = lcmap('#c0c0c0')
    ch4data.where(~(ikirluokat==prf.luokat1[ikir_ind]),np.nan).plot.\
        pcolormesh( transform=platecarree, ax=gca(), add_colorbar=False, cmap=harmaa )
    title(prf.luokat1[ikir_ind])

def vaihda_luokka(hyppy):
    global ikir_ind
    ikir_ind = ( ikir_ind + len(prf.luokat1) + hyppy ) % len(prf.luokat1)
    piirra()
    draw()

def nappainfunk(tapaht):
    if tapaht.key == 'right' or tapaht.key == 'o' or tapaht.key == 'i':
        vaihda_luokka(1)
    elif tapaht.key == 'left' or tapaht.key == 'g' or tapaht.key == 'a':
        vaihda_luokka(-1)

if __name__ == '__main__':
    varoitusvari = '\033[1;33m'
    vari0 = '\033[0m'
    rcParams.update({'font.size':18,'figure.figsize':(12,10),'text.usetex':True})
    argumentit(sys.argv)
    datamaski = xr.open_dataset(tyotiedostot + 'FT_implementointi/FT_percents_pixel_ease_flag/DOY/winter_end_doy_2014.nc')
    
    ikiroutaolio = prf.Prf('1x1').rajaa([datamaski.lat.min(),datamaski.lat.max()+0.01])
    ikirouta = ikiroutaolio.data.mean(dim='time')
    ikirluokat = prf.luokittelu1_str_xr(ikirouta)

    ch4data = xr.open_dataset(edgartno_lpx_t)[edgartno_lpx_m].\
        mean(dim='record').\
        loc[datamaski.lat.min():datamaski.lat.max(),:].\
        where(datamaski.spring_start==datamaski.spring_start,np.nan)

    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    kattavuus   = [-180,180,30,90]
    fig = figure()

    vkartta = luo_varikartta()

    piirra()
    if not tallenna:
        fig.canvas.mpl_connect('key_press_event',nappainfunk)
        show()
        ch4data.close()
        exit()
    while True:
        if verbose:
            print(prf.luokat1[ikir_ind])
        savefig("kuvia/%s%i.png" %(sys.argv[0][:-3],ikir_ind))
        if ikir_ind==len(prf.luokat1)-1:
            exit()
        vaihda_luokka(1)

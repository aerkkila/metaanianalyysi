#!/usr/bin/python3
import xarray as xr
import numpy as np
import cartopy.crs as ccrs
from matplotlib.pyplot import *
import matplotlib.colors as mcolors
import sys
import prf_extent as prf
import maalajit as ml

def argumentit(argv):
    global latraja,tallenna,ikir_ind
    latraja=45; tallenna=False; ikir_ind=0
    i=1
    while i < len(argv):
        a = argv[i]
        if a == '-s':
            tallenna = True
        elif a == '-l0':
            i+=1
            try:
                latraja = int(argv[i])
            except Exception as e:
                print("%sVaroitus:%s latrajan lukeminen epäonnistui. %s" %(varoitusvari,vari0,str(e)))
        else:
            print("%sVaroitus:%s tuntematon argumentti \"%s\"" %(varoitusvari,vari0,a))
        i+=1

def piirra():
    clf()
    ax = axes([0.01,0.01,1,0.95],projection=projektio)
    ax.set_extent(kattavuus,platecarree)
    ax.coastlines()
    ch4data.where(ikirluokat==prf.luokat[ikir_ind],np.nan).plot.\
        pcolormesh( transform=platecarree, norm=mcolors.DivergingNorm(0,max(datamin*6,-datamax),datamax) )
    #Tämä asettaa muut ikiroutaluokka-alueet harmaaksi. ax.set_facecolor() ei toiminut
    from matplotlib.colors import ListedColormap as lcmap
    harmaa = lcmap('#c0c0c0')
    ch4data.where(~(ikirluokat==prf.luokat[ikir_ind]),np.nan).plot.\
        pcolormesh( transform=platecarree, ax=gca(), add_colorbar=False, cmap=harmaa )
    title(prf.luokat[ikir_ind])

def vaihda_luokka(hyppy):
    global ikir_ind
    ikir_ind = ( ikir_ind + len(prf.luokat) + hyppy ) % len(prf.luokat)
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
    rcParams.update({'font.size':13,'figure.figsize':(12,10)})
    argumentit(sys.argv)
    
    ikiroutaolio = prf.Prf('1x1').rajaa([latraja,90])
    ikirouta = ikiroutaolio.data.mean(dim='time')
    ikirluokat = prf.luokittelu_str_xr(ikirouta)
    prf.luokat = prf.luokat[1:] # distinguishing isolated pois

    from config import LPX2019vuo
    ncmuuttuja = 'posterior_bio'
    ch4data = xr.open_dataset(LPX2019vuo)[ncmuuttuja].mean(dim='time').loc[latraja:,:]

    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    kattavuus   = [-180,180,latraja,90]
    fig = figure()
    #Tällä asetetaan muut ikiroutaluokka-alueet harmaaksi.
    from matplotlib.colors import ListedColormap as lcmap
    harmaa = lcmap('#c0c0c0')

    datamin = float(ch4data.min())
    datamax = float(ch4data.max())

    piirra()
    if not tallenna:
        fig.canvas.mpl_connect('key_press_event',nappainfunk)
        show()
        ch4data.close()
        exit()
    while True:
        savefig("kuvia/%s%i.png" %(sys.argv[0][:-3],ikir_ind))
        if ikir_ind==len(prf.luokat)-1:
            exit()
        vaihda_luokka(1)

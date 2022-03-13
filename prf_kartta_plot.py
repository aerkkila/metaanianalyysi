#!/usr/bin/python3
import numpy as np
from matplotlib.pyplot import *
import cartopy.crs as ccrs
import matplotlib
import prf_extent as prf

def toinen():
    ikirouta = prf.Prf('1x1').rajaa( (40,90) )
    ikirdata = np.mean(ikirouta.data,axis=0)
    ikirnum = prf.luokittelu_num(ikirdata)
    ikirouta = None
    ikirdata = None
    luokkia=4
    cmap = matplotlib.cm.get_cmap('plasma_r',lut=luokkia)
    cmap = matplotlib.colors.ListedColormap([ cmap(i) for i in range(luokkia) ])
    imshow(ikirnum, cmap=cmap, interpolation='none')
    cbar=colorbar()
    vali = (luokkia-1)/luokkia
    cbar.set_ticks( np.linspace(vali/2,luokkia-1-vali/2,luokkia) )
    cbar.ax.set_yticklabels(prf.luokat)
    tight_layout()
    show()

def main():
    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
#    projektio  = platecarree
    kattavuus   = [-180,180,45,90]
    ax = axes(projection=projektio)
    ax.coastlines()
    ax.set_extent(kattavuus,platecarree)
    ikirouta = prf.Prf('1x1',muoto='xarray').data.mean(dim='time')
    ikirouta.plot.pcolormesh(transform=platecarree)
    show()

if __name__ == '__main__':
    rcParams.update({'font.size':13,'figure.figsize':(12,10)})
    main()

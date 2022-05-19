#!/usr/bin/python3
from matplotlib.pyplot import *
import cartopy.crs as ccrs
import matplotlib
import prf as prf
import sys

if __name__ == '__main__':
    rcParams.update({'font.size':13,'figure.figsize':(12,10)})
    tallenna = False
    if '-s' in sys.argv:
        tallenna = True
    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    #projektio  = platecarree
    kattavuus   = [-180,180,25,90]
    ax = axes(projection=projektio)
    ax.coastlines()
    ax.set_extent(kattavuus,platecarree)
    ikirouta = prf.Prf().data.mean(dim='time')
    ikirouta.where(ikirouta>0,np.nan).plot.pcolormesh(transform=platecarree,cmap=get_cmap('rainbow'))
    if not tallenna:
        show()
    else:
        savefig('kuvia/%s.png' %(sys.argv[0][:-3]))

#!/usr/bin/python3
from matplotlib.pyplot import *
import cartopy.crs as ccrs
import matplotlib
import prf_extent as prf

def main():
    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    #projektio  = platecarree
    kattavuus   = [-180,180,25,90]
    ax = axes(projection=projektio)
    ax.coastlines()
    ax.set_extent(kattavuus,platecarree)
    ikirouta = prf.Prf('1x1',muoto='xarray').data.mean(dim='time')
    ikirouta.where(ikirouta>0,np.nan).plot.pcolormesh(transform=platecarree,cmap=get_cmap('rainbow'))
    show()

if __name__ == '__main__':
    rcParams.update({'font.size':13,'figure.figsize':(12,10)})
    main()

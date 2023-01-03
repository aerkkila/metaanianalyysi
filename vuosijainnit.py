#!/bin/env python3
import cartopy.crs as ccrs
from matplotlib.pyplot import *
import matplotlib.colors as mcolors
from netCDF4 import Dataset
import numpy as np
import sys

def main():
    rcParams.update({'font.size': 15,
                     'figure.figsize': (12,9)})
    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    kattavuus   = [-180,180,45,90]
    lajit       = ['fen','marsh','permafrost_bog','tundra_wetland']

    ds = Dataset("vuosijainnit%s.nc" %('_sekoitus' if '--sekoitus' in sys.argv[1:] else ''), "r")
    lat = np.ma.getdata(ds['lat'])
    lon = np.ma.getdata(ds['lon'])
    mx,my = np.meshgrid(lon,lat, sparse=True)

    for il,laji in enumerate(lajit):
        ax = subplot(2,2,il+1, projection=projektio)
        ax.coastlines()
        ax.set_extent(kattavuus, platecarree)
        dt = np.ma.getdata(ds[laji])
        normi = mcolors.TwoSlopeNorm(0, np.nanmin(dt), np.nanmax(dt))
        pcolormesh(mx,my, dt, transform=platecarree, cmap=get_cmap('coolwarm'), norm=normi)
        title(laji.replace('_',' '))
        colorbar()

    tight_layout()
    if '-s' in sys.argv:
        savefig('kuvia/vuosijainnit%s.png' %('_sekoitus' if '--sekoitus' in sys.argv[1:] else ''))
    else:
        show()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

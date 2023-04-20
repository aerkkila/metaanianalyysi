#!/bin/env python3
import cartopy.crs as ccrs
from matplotlib.pyplot import *
import matplotlib.colors as mcolors
from netCDF4 import Dataset
import numpy as np
import sys
from pintaalat import pintaalat
from laatikkokuvaaja import wpercentile

def main():
    rcParams.update({'font.size': 15,
                     'figure.figsize': (11,12)})
    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    kattavuus   = [-180,180,45,90]
    lajit       = ['bog','fen','marsh','permafrost_bog','tundra_wetland']

    ds = Dataset("vuosijainnit%s.nc" %('_sekoitus' if '--sekoitus' in sys.argv[1:] else ''), "r")
    lat = np.ma.getdata(ds['lat'])
    lon = np.ma.getdata(ds['lon'])
    mx,my = np.meshgrid(lon,lat, sparse=True)

    alat = np.repeat(pintaalat, len(lon))

    for il,laji in enumerate(lajit):
        ax = subplot(3,2,il+1+(il>0), projection=projektio)
        ax.coastlines()
        ax.set_extent(kattavuus, platecarree)
        dt = np.ma.getdata(ds[laji]) * 5 # 1000 -> 5000 km²
        #normi = mcolors.TwoSlopeNorm(0, np.nanmin(dt), np.nanmax(dt))
        #normi = mcolors.TwoSlopeNorm(0, np.nanpercentile(dt,1), np.nanpercentile(dt,99))
        normi = mcolors.TwoSlopeNorm(0, *wpercentile(dt.flatten(),alat,[1,99]))
        pcolormesh(mx,my, dt, transform=platecarree, cmap=get_cmap('coolwarm'), norm=normi)
        title(laji.replace('_',' '))
        colorbar(extend='both')

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

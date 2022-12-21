#!/bin/env python
import cartopy.crs as ccrs
from matplotlib.pyplot import *
import matplotlib as mpl
from netCDF4 import Dataset
import numpy as np
import sys

lajit = ['permafrost_bog', 'tundra_wetland']

def tee_kuva(rajat):
    ax.coastlines()
    ax.set_extent(kattavuus, platecarree)
    cm = get_cmap(cmap, 256)
    normi = mpl.colors.BoundaryNorm(boundaries=rajat, ncolors=256)
    pcolormesh(mx, my, a, transform=platecarree, cmap=cm, norm=normi)
    for nimiö,arvo in zip(['nonpermafrost wetland', 'both', 'permafrost wetland'], [0.01, 0.5, 0.99]):
        plot(-1, -1, '.', markersize=25, transform=platecarree, color=cm(normi(arvo)), label=nimiö)
    legend(loc='lower left')

if __name__=='__main__':
    rcParams.update({'font.size': 18,
                     'figure.figsize': (10,10)})
    ds          = Dataset('BAWLD1x1.nc', 'r')
    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    kattavuus   = [-180,180,45,90]
    cmap        = 'jet'

    mx,my       = np.meshgrid(ds['lon'][:], ds['lat'][:], sparse=True)
    wl          = np.ma.getdata(ds['wetland'][:,:])
    wl[wl<0.05] = np.nan

    a = np.empty([len(lajit),ds['bog'].shape[0],ds['bog'].shape[1]], np.float32)
    for i,laji in enumerate(lajit):
        a[i,...] = np.ma.getdata(ds[laji][:,:]) / wl
    ds.close()
    a = np.sum(a, axis=0)

    ax = axes(projection=projektio)
    rajat = np.array([0,0.03,0.97,1])
    tee_kuva(rajat)
    tight_layout()
    if('-s') in sys.argv:
        savefig('kuvia/permafrost_wetland_kartta.png')
    else:
        show()

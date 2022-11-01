#!/usr/bin/python
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
    normi = mpl.colors.BoundaryNorm(boundaries=rajat, ncolors=256)
    pcolormesh(mx, my, a, transform=platecarree, cmap=get_cmap(cmap, 256), norm=normi)

def väripalkki(rajat):
    nimet = ['non-prf wetland','both','prf wetland']
    r = np.empty(len(rajat)-1, np.float32)
    for i in range(len(rajat)-1):
        r[i] = np.mean(rajat[i:i+2])
    locator = mpl.ticker.FixedLocator(r)
    cbar = colorbar(ticks=locator)
    cbar.set_ticklabels(nimet)

if __name__=='__main__':
    rcParams.update({'font.size': 18,
                     'figure.figsize': (12,10)})
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
    väripalkki(rajat)
    tight_layout()
    if('-s') in sys.argv:
        savefig('kuvia/bawld_ikir_kartta.png')
    else:
        show()

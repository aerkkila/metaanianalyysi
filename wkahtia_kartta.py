#!/usr/bin/python
import cartopy.crs as ccrs
from matplotlib.pyplot import *
import matplotlib as mpl
from netCDF4 import Dataset
import numpy as np
import sys

lajit = ['permafrost_bog', 'tundra_wetland']

def tee_kuva(ots):
    ax.coastlines()
    ax.set_extent(kattavuus, platecarree)
    rajat = np.concatenate([
        [0,0.05],
        np.arange(0.95, 1, 0.01),
    ])
    normi = mpl.colors.BoundaryNorm(boundaries=rajat, ncolors=256)
    pcolormesh(mx, my, a, transform=platecarree, cmap=get_cmap(cmap, 256), norm=normi)
    colorbar()
    title(ots)

if __name__=='__main__':
    rcParams.update({'font.size': 15,
                     'figure.figsize': (15,7)})
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

    ax = subplot(1, 2, 2, projection=projektio)
    tee_kuva('portion of permafrost bog + tundra wetland')
    a = 1-a
    ax = subplot(1, 2, 1, projection=projektio)
    tee_kuva('portion of bog + fen + marsh')
    tight_layout()
    if('-s') in sys.argv:
        savefig('kuvia/wkahtia_kartta.png')
    else:
        show()

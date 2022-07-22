#!/usr/bin/python3
import cartopy.crs as ccrs
from matplotlib.pyplot import *
import matplotlib as mpl
from netCDF4 import Dataset
import numpy as np
import sys

def tee_alikuva(subplmuoto, subpl, **axes_kwargs):
    subpl_y = subplmuoto[0]-1 - subpl // subplmuoto[1]
    subpl_x = subpl % subplmuoto[1]
    xkoko = 0.91/subplmuoto[1]
    ykoko = 0.97/subplmuoto[0]
    ax = axes([0.02 + subpl_x*xkoko,
               0.03 + subpl_y*ykoko,
               xkoko-0.03, ykoko-0.05],
              **axes_kwargs)
    return ax

def main():
    rcParams.update({'font.size': 15,
                     'figure.figsize': (14,8)})
    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    kattavuus   = [-180,180,45,90]
    lajit       = ['bog','fen','marsh','permafrost_bog','tundra_wetland']
    ds          = Dataset('BAWLD1x1.nc', 'r', format="NETCDF4_CLASSIC")
    cmap        = 'gnuplot2_r'
    mx,my       = np.meshgrid(ds['lon'][:], ds['lat'][:], sparse=True)
    a           = np.empty([len(lajit),ds['bog'].shape[0],ds['bog'].shape[1]], np.float32)
    wl          = ds['wetland'][:,:]
    wl[wl<0.05] = np.nan
    for i,laji in enumerate(lajit):
        a[i,...] = ds[laji][:,:] / wl
    maxmuu   = np.max(a[[True,True,False,True,True], ...])
    for i,laji in enumerate(lajit):
        ax = tee_alikuva([2,3], i, projection=projektio)
        ax.coastlines()
        ax.set_extent(kattavuus, platecarree)
        pcolormesh(mx,my, a[i,...], transform=platecarree, cmap=get_cmap('gnuplot2_r'), vmin=0,
                   vmax=maxmuu if i!=2 else None)
        title(laji)
        colorbar()
    if('-s' in sys.argv):
        savefig('kuvia/%s.png' %sys.argv[0])
    else:
        show()

if __name__ == '__main__':
    from warnings import filterwarnings
    filterwarnings(action='ignore', category=DeprecationWarning, message='`np.bool` is a deprecated alias')
    main()

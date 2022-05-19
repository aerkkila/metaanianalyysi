#!/usr/bin/python3
import cartopy.crs as ccrs
import maalajit as ml
import sys
from matplotlib.pyplot import *
import matplotlib as mpl

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

if __name__ == '__main__':
    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    kattavuus   = [-180,180,45,90]
    alkup, muunnos = ml.lue_maalajit(['bog','fen','tundra_wetland','permafrost_bog'], muunnos=False)
    rcParams.update({'font.size': 15,
                     'figure.figsize': (11,10.6)})

    fig = figure()
    maks = 0
    for i,laji in enumerate(alkup.keys()):
        m = alkup[laji].max()
        if m > maks:
            maks = m

    cmap='gnuplot2_r'
    for i,laji in enumerate(alkup.keys()):
        ax = tee_alikuva([2,2], i, projection=projektio)
        ax.coastlines()
        ax.set_extent(kattavuus, platecarree)
        alkup[laji].plot.pcolormesh(transform=platecarree, cmap=cmap, vmax=maks, vmin=0, add_colorbar=False)
        title(laji)
    ax = axes((0.91,0.031,0.03,0.92))
    norm = mpl.colors.Normalize(vmin=0, vmax=maks)
    colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), cax=ax)

    if('-s' in sys.argv):
        savefig('kuvia/BAWLD_wetlands.png')
    else:
        show()

#!/bin/env python
import cartopy.crs as ccrs
import numpy as np
from matplotlib.pyplot import *
import matplotlib.colors as mcolors
import sys

def lue(luku):
    if(type(luku) == type('s')):
        nimi = luku
    else:
        nimi = "met_kau%i.bin" %luku
    with open(nimi, 'r') as f:
        raaka = f.buffer.read()
    return np.ndarray((2,55,360), np.float32, buffer=raaka)

def piirrä(dt, mx, my, tall):
    pc   = ccrs.PlateCarree()
    proj = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    katt = [-180,180,35,90]
    fig, axs = subplots(1, 2, layout='constrained', subplot_kw={'projection':proj})
    #axs = figure(constrained_layout=True).subplot_mosaic('AB', subplot_kw={"projection":proj})

    for i in range(2):
        ax = axs[i]
        sca(ax)
        ax.coastlines()
        ax.set_extent(katt, pc)
        mi = np.nanpercentile(dt[i,...], 2)
        ext = 'both'
        if mi >= 0:
            mi = np.nanmin(dt[i,...])
            ext = 'max'
        ma = np.nanpercentile(dt[i,...], 98)
        normi = mcolors.TwoSlopeNorm(0, mi, ma)
        pcolormesh(mx, my, dt[i,...], transform=pc, norm=normi, cmap=get_cmap('coolwarm'))
        tikit = np.concatenate([
            np.ceil(np.linspace(mi, 0, 3)[:-1] * 10) / 10,
            np.floor(np.linspace(0, ma, 5) * 10) / 10
            ])
        cb = colorbar(extend=ext, shrink=0.8, ticks = tikit)

    if '-s' in sys.argv:
        savefig('kuvat/' + tall)
        clf()
    else:
        show()

kaudet = ['summer','freezing','winter']

def main():
    rcParams.update({'font.size':15, 'figure.figsize':(14,7)})
    lon = np.arange(-180,180,1) + 0.5
    lat = np.arange(29,84,1) + 0.5
    lon,lat = np.meshgrid(lon, lat, sparse=True)
    for i in range(3):
        piirrä(lue(i), lon, lat, tall='keskivuo_%s.png' %(kaudet[i]))
    piirrä(lue('kesän_maksvuo.bin'), lon, lat, tall='kesän_maxvuo.png')

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

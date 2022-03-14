#!/usr/bin/python3
import numpy as np
from matplotlib.pyplot import *
import prf_extent as prf
import cartopy.crs as ccrs
import sys

def vaihda_vuosi(maara:int):
    global vuosi_ind
    vuosi_ind = (vuosi_ind + tif.data.shape[0] + maara) % tif.data.shape[0]
    olio.set_array(tif.data[vuosi_ind,:,:].data.flatten())
    title(str(tif.vuodet[vuosi_ind]))
    draw()

def nappainfunk(tapaht):
    if tapaht.key == 'right' or tapaht.key == 'o' or tapaht.key == 'i':
        vaihda_vuosi(1)
    elif tapaht.key == 'left' or tapaht.key == 'a' or tapaht.key == 'g':
        vaihda_vuosi(-1)

if __name__ == '__main__':
    avg=False
    for a in sys.argv:
        if a == 'avg':
            avg=True
    rcParams.update({'font.size':13,'figure.figsize':(12,10)})
    tif = prf.Prf('1x1','xarray')
    tif.data = tif.data.where(tif.data>0,np.nan)
    vuosi_ind = 0
    platecarree = ccrs.PlateCarree()
    projektio = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    fig = figure()
    ax = axes([0,0.04,1,0.92],projection=projektio)
    ax.coastlines()
    ax.set_extent([-180,180,25,90],platecarree)
    if avg:
        olio = tif.data.mean(dim='time').plot.pcolormesh( cmap=get_cmap('rainbow'), ax=ax, transform=platecarree )
        tif.vuodet=[0]
    else:
        olio = tif.data[vuosi_ind,:,:].plot.pcolormesh( cmap=get_cmap('rainbow'), ax=ax, transform=platecarree )
        title(str(tif.vuodet[vuosi_ind]))
        fig.canvas.mpl_connect('key_press_event',nappainfunk)
    show()

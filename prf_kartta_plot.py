#!/usr/bin/python3
import numpy as np
from matplotlib.pyplot import *
import prf_extent as prf
import cartopy.crs as ccrs

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
    rcParams.update({'font.size':13,'figure.figsize':(12,10)})
    tif = prf.Prf('1x1','xarray')
    vuosi_ind = 0
    platecarree = ccrs.PlateCarree()
    projektio = platecarree
    fig = figure()
    ax = axes(projection=projektio)
    ax.coastlines()
    olio = tif.data[vuosi_ind,:,:].plot.pcolormesh( cmap=get_cmap('rainbow'), ax=ax )
    title(str(tif.vuodet[vuosi_ind]))
    tight_layout()
    fig.canvas.mpl_connect('key_press_event',nappainfunk)
    show()

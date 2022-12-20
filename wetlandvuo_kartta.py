#!/bin/env python
from netCDF4 import Dataset
import numpy as np
from matplotlib.pyplot import *
import cartopy.crs as ccrs
from matplotlib.colors import TwoSlopeNorm
import luokat
from PIL import Image
import os, time

def tee_data():
    ds = Dataset('flux1x1.nc', 'r')
    vuo = np.ma.getdata(ds['flux_bio_posterior'][:])
    vuo = np.mean(vuo, axis=0)
    lat = np.ma.getdata(ds['lat'])
    lon = np.ma.getdata(ds['lon'])
    ds.close

    ds = Dataset('BAWLD1x1.nc')
    wet = np.ma.getdata(ds['wetland'][:])
    ds.close

    vuo = np.where(wet<0.05, 0, vuo)
    return vuo, lat, lon

def main():
    # Paremman puutteessa köppikir_kartta-kuvan koko luettakoon järjestelmän grep-komennoilla.
    p = os.popen('grep -o "figure\.figsize[^:]*:" köppikir_kartta.py', 'r')
    lookbehind = p.read()
    lookbehind = lookbehind.replace('\n','').replace('\'','\\\'').replace('"','\"')
    p.close()
    kutsu = 'grep -Po "(?<=%s)\([0-9]*, *[0-9]*\)" köppikir_kartta.py' %lookbehind
    p = os.popen(kutsu, 'r')
    koko = p.read()
    p.close()
    xkoko,ykoko = eval(koko)
    rcParams.update({'font.size':15, 'figure.figsize':(xkoko,ykoko)})

    vuo,lat,lon = tee_data()
    lon,lat = np.meshgrid(lon,lat, sparse=True)

    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    kattavuus   = [-180,180,40,90]
    ax = axes(projection=projektio)
    ax.set_extent(kattavuus, platecarree)
    ax.coastlines()

    pienin = np.min(vuo)
    suurin = np.max(vuo)
    normi = TwoSlopeNorm(0,max(pienin*6,-suurin),suurin)
    pcolormesh(lon, lat, vuo, transform=platecarree, cmap=get_cmap('coolwarm'), norm=normi)
    #colorbar()

    tight_layout()

    nimi = 'tmp%i.png' %int(time.time()*1000)
    savefig(nimi)
    kuva0 = Image.open(nimi)
    os.unlink(nimi)

    kuva1 = Image.open('kuvia/ikir_kartta.png')
    kuva1.putalpha(90)
    
    kuva = Image.alpha_composite(kuva0, kuva1)
    kuva.save('testi.png')
    #kuva0 = kuva0 + (kuva1-kuva0)*alpha
    #pil.

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

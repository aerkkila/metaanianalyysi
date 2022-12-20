#!/bin/env python
from netCDF4 import Dataset
import numpy as np
from matplotlib.pyplot import *
import cartopy.crs as ccrs
import luokat
from matplotlib.colors import ListedColormap as lcmap

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

def lue_ikirouta():
    ds = Dataset('ikirdata.nc', 'r')
    ret = np.ma.getdata(ds['luokka'][:])
    ret = np.round(np.mean(ret, axis=0)).astype(np.int8)
    ds.close()
    return ret

def main():
    rcParams.update({'font.size': 15,
                     'figure.figsize': (12,10)})
    vuo,lat,lon = tee_data()
    lon,lat = np.meshgrid(lon,lat, sparse=True)

    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    kattavuus   = [-180,180,45,90]
    ax = axes(projection=projektio)
    ax.set_extent(kattavuus, platecarree)
    ax.coastlines()

    ikir = lue_ikirouta()
    pcolormesh(lon, lat, np.where(ikir==1,vuo,np.nan), transform=platecarree, cmap=get_cmap('gnuplot2_r'))
    colorbar()


    tight_layout()
    show()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

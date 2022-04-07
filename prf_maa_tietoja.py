#!/usr/bin/python3
import xarray as xr
import numpy as np
import cartopy.crs as ccrs
from matplotlib.pyplot import *

def piirra(data,tasoja):
    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    kattavuus   = [-180,180,25,90]
    ax = axes(projection=projektio)
    ax.coastlines()
    ax.set_extent(kattavuus,platecarree)
    data.plot.pcolormesh(transform=platecarree, cmap=get_cmap('rainbow',tasoja),
                         cbar_kwargs={'ticks':range(tasoja)})

def bogfen_alueen_muut_luokat():
    #ikir_ind = 0
    osuusraja = 0.8
    ikirmaa = xr.open_dataset('prf_maa_kaikki.nc').\
        drop_vars(['wetland','bog','fen','tundra_wetland','permafrost_bog']).median(dim='time').sum(dim='prf')
    bf = (ikirmaa['bog+fen'])
    ikirmaa = ikirmaa.drop_vars(['bog+fen'])
    maski = (bf >= wetlandraja).astype(int).data.flatten()
    maski = xr.where(maski,1,np.nan)
    muut_bin = np.empty([len(maski), len(ikirmaa.keys())])
    muut_liu = np.empty([len(maski), len(ikirmaa.keys())])
    #muut sisältää:
    # nan, jos bog+fen-luokkaa on alle wetlandraja
    # 0/1 sen mukaan, onko kutakin luokkaa pisteessä yli osuusrajan
    for aind,av in enumerate(ikirmaa.keys()):
        dt = ikirmaa[av].data.flatten()
        for i,d in enumerate(dt):
            muut_liu[i,aind] = d*maski[i]
            muut_bin[i,aind] = (d>=osuusraja)*maski[i]
    uusi = np.sum(muut_bin,axis=1)
    np.nan_to_num(muut_liu,copy=False)
    np.nan_to_num(muut_bin,copy=False)
    bf.data = uusi.reshape(bf.data.shape)

    laj = list(ikirmaa.keys())
    lajit_bin = np.zeros(len(laj),int)
    lajit_liu = np.zeros(len(laj),float)
    for j in range(muut_bin.shape[0]):
        for i in range(muut_bin.shape[1]):
            lajit_liu[i] += muut_liu[j,i]
            lajit_bin[i] += muut_bin[j,i]==1

    for i,laji in enumerate(laj):
        print('\033[32m%s\033[33m\t%i\t\033[0m%.4f' %(laji,lajit_bin[i],lajit_liu[i]))

    piirra(bf,int(np.nanmax(uusi)))
    savefig('testi0.png')
    show()
    ikirmaa.close()

    
def piirra1(data,sij):
    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    kattavuus   = [-180,180,25,90]
    ax = gcf().add_axes(sij,projection=projektio)
    ax.coastlines()
    ax.set_extent(kattavuus,platecarree)
    data.plot.pcolormesh(transform=platecarree, cmap=get_cmap('jet'))

def luokat_ilman_wetland():
    rcParams.update({'figure.figsize':(14,12),'font.size':14})
    luokat = ['boreal_forest','tundra_dry','rockland','lake']
    w = 0.4; h = 0.4
    fig = figure()
    sij = [[0,0.05,w,h],[0.5,0.05,w,h],[0,0.55,w,h],[0.5,0.55,w,h]]
    for l,luokka in enumerate(luokat):
        ikirmaa = xr.open_dataset('prf_maa_kaikki.nc').median(dim='time').sum(dim='prf')
        bf = ikirmaa[luokka]
        bfdata = bf.data.flatten()
        wetdata = ikirmaa.wetland.data.flatten()
        uusi = (wetdata<wetlandraja)*bfdata
        bf.data = np.reshape(uusi,bf.data.shape)
        piirra1(bf,sij[l])
        title(luokka)
    show()
    ikirmaa.close()

if __name__ == '__main__':
    wetlandraja = 0.03
    bogfen_alueen_muut_luokat()
    luokat_ilman_wetland()

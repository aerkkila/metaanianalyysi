#!/bin/env python
from netCDF4 import Dataset
import numpy as np
import cartopy.crs as ccrs
import matplotlib.colors as mcolors
import matplotlib, sys, luokat
from matplotlib.pyplot import *
from matplotlib.colors import ListedColormap as lcmap

varoitusväri = '\033[1;33m'
väri0        = '\033[0m'
ikir_ind     = 0
ikirjako = False
kost     = True

def luo_värikartta(ch4data):
    global pienin,suurin
    pienin = np.nanpercentile(ch4data.data, 1)
    suurin = np.nanpercentile(ch4data.data,99)
    if '-v' in sys.argv:
        print('pienin, prosenttipiste: ', ch4data.min().data, pienin)
        print('suurin, prosenttipiste: ', ch4data.max().data, suurin)
    N = 1024
    cmap = matplotlib.cm.get_cmap('coolwarm',N)
    värit = np.empty(N,object)
    kanta = 10

    #negatiiviset vuot lineaarisesti
    for i in range(0,N//2):
        värit[i] = cmap(i)

    #positiiviset vuot logaritmisesti
    cmaplis=np.logspace(np.log(0.5)/np.log(kanta),0,N//2)
    for i in range(N//2,N):
        värit[i] = cmap(cmaplis[i-N//2])
    return lcmap(värit)

ulkoväri = '#d0e0c0'
harmaaväri = '#c0c0c0'

def piirrä(ikir_ind):
    ax = gca()
    ax.set_extent(kattavuus,platecarree)
    ax.coastlines()

    #Varsinainen data
    normi = mcolors.TwoSlopeNorm(0,max(pienin*6,-suurin),suurin)
    if ikirjako:
        data = np.where(ikirouta==ikir_ind, ch4data, np.nan)
    else:
        data = ch4data
    pcolormesh(lon, lat, data, transform=platecarree, cmap=vkartta, norm=normi)
    c = colorbar()
    c.set_label('nmol m$^{-2}$ s$^{-1}$')

    #Tämä asettaa muut ikiroutaluokka-alueet harmaaksi.
    if ikirjako:
        harmaa = lcmap(harmaaväri)
        pcolormesh(lon, lat, np.where(ikirouta!=ikir_ind, 0, np.nan), transform=platecarree, cmap=harmaa)

    #Tämä asettaa maskin ulkopuolisen alueen eri väriseksi
    harmaa = lcmap(ulkoväri)
    pcolormesh(lon, lat, np.where(maski, np.nan, 0), transform=platecarree, cmap=harmaa)

pripost_sis = ['flux_bio_prior', 'flux_bio_posterior'][::-1]
pripost_ulos = ['pri', 'post'][::-1]

def aja():
    global ch4data, vkartta
    ds = Dataset("kaudet.nc", "r")
    kaudet = np.ma.getdata(ds['kausi'][:])
    ds.close()
    k = 0
    assert(k==0)
    ch4data = np.nanmean(ch4data0, axis=0)
    if kost:
        ch4data = np.where((wetl>=0.05), ch4data/wetl, np.nan)

    vkartta = luo_värikartta(ch4data)

    for ikir_ind in range(len(luokat.ikir) if ikirjako else 1):
        ax = axes(projection=projektio)
        piirrä(ikir_ind)
        if ikirjako:
            if k:
                tunniste = "%s, %s" %(luokat.ikir[ikir_ind], luokat.kaudet[k])
            else:
                tunniste("%s" %(luokat.ikir[ikir_ind]))
        else:
            if k:
                tunniste("%s" %(luokat.kaudet[k]))
            else:
                tunniste = ''
        title(tunniste)
        tight_layout()
        if not '-s' in sys.argv:
            show()
            continue
        tunniste = tunniste.replace(', ','_')
        savefig("./kuvia/yksittäiset/%s_%s.png" %(sys.argv[0][:-3], tunniste))
        clf()

def main():
    global projektio,platecarree,kattavuus,ikirouta,ch4data0,lat,lon,maski,wetl
    rcParams.update({'font.size':18,'figure.figsize':(11,10)})

    ds = Dataset('./flux1x1.nc', 'r')
    ch4data0 = np.ma.getdata(ds['flux_bio_posterior'][:]) * 1e9
    ds.close()

    ds = Dataset('aluemaski.nc', 'r')
    maski = np.ma.getdata(ds['maski'][:])
    lat = np.ma.getdata(ds['lat'][:])
    lon = np.ma.getdata(ds['lon'][:])
    lon,lat = np.meshgrid(lon,lat, sparse=True)
    ds.close()

    ds = Dataset('BAWLD1x1.nc', 'r')
    wetl = np.ma.getdata(ds['wetland'][:])
    ds.close()

    ds = Dataset('ikirdata.nc', 'r')
    ikirouta = np.ma.getdata(ds['luokka'][:])
    ikirouta = np.round(np.mean(ikirouta, axis=0)).astype(np.int8)

    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    kattavuus   = [-180,180,45,90]

    aja()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

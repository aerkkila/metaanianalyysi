#!/bin/env python
import cartopy.crs as ccrs
from matplotlib.pyplot import *
from matplotlib.patches import Patch
from netCDF4 import Dataset
import matplotlib, re, sys, luokat, os

luokat_köpp_re = ['D.b', 'D.c', 'D.d', 'ET']
luokat_ikir = luokat.ikir
cmapnimi = "jet"

def aja(ikirkö):
    global lon, lat, platecarree
    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    kattavuus   = [-180,180,45,90]
    ds = Dataset('aluemaski.nc')
    lon = np.ma.getdata(ds['lon']).flatten()
    lat = np.ma.getdata(ds['lat']).flatten()
    maski = np.ma.getdata(ds['maski']).flatten()
    ds.close()

    if ikirkö==1:
        luokitus_ = Dataset('ikirdata.nc', 'r')
        luokitus = np.zeros(len(lat)*len(lon), np.int8)
        taul = np.ma.getdata(luokitus_['luokka'])
        vuodet = np.ma.getdata(luokitus_['vuosi'])
        taul = np.round(np.mean(taul[vuodet>=2011], axis=0)).astype(int)
        for i,v in enumerate(luokat_ikir):
            k = luokat.ikir.index(v)
            luokitus += (taul==k).flatten() * maski * (i+1)
        luokitus_.close()
        luokat_ = luokat_ikir
        ncol=1
    elif ikirkö==0:
        luokitus_ = Dataset('köppen1x1maski.nc', 'r')
        luokitus = np.zeros(len(lat)*len(lon), np.int8)
        for ilk,lk in enumerate(luokat_köpp_re):
            for k in luokitus_.variables:
                if re.match(lk, k):
                    luokitus |= np.ma.getdata(luokitus_[k]).flatten() * maski * (ilk+1)
        luokitus_.close()
        luokat_ = luokat_köpp_re
        ncol=2
    else:
        luokitus_ = Dataset('BAWLD1x1.nc', 'r')
        luokitus = np.zeros(len(lat)*len(lon), np.int8)
        wl = np.ma.getdata(luokitus_['wetland']).flatten()
        kylymä = np.ma.getdata(luokitus_['wetland_prf']).flatten()
        kylymä[wl<0.05] = np.nan
        kylymä /= wl
        luokitus[kylymä<=0.03] = 1
        luokitus[(0.03<kylymä) & (kylymä<0.97)] = 2
        luokitus[0.97<=kylymä] = 3
        luokitus_.close()
        ncol=1
        luokat_ = ['warm wetland', 'temperate wetland', 'cold wetland']

    cmap = matplotlib.cm.get_cmap(cmapnimi, len(luokat_))
    ax = subplot(1,3,1+ikirkö, projection=projektio)
    ax.coastlines()
    ax.set_extent(kattavuus, platecarree)
    luokitus = luokitus.reshape([len(lat),len(lon)])
    mx,my = np.meshgrid(lon, lat, sparse=True)
    lk = np.ma.masked_where(luokitus==0, luokitus)
    pcolormesh(mx, my, lk, cmap=cmapnimi, transform=platecarree)

    jäsenet = np.empty(len(luokat_), object)
    for i,l in enumerate(luokat_):
        jäsenet[i] = Patch(color=cmap(i), label=l.replace('.',''))
    legend(handles=list(jäsenet), loc='lower left', fancybox=False, framealpha=0.5, ncol=ncol,
            bbox_to_anchor=[0,-0.2])

def main():
    rcParams.update({'font.size':18,'figure.figsize':(16,8)})
    aja(0)
    aja(1)
    aja(2)
    tight_layout()
    if '-s' in sys.argv:
        savefig('kuvia/aluejaot.png', bbox_inches='tight')
        clf()
    else:
        show()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

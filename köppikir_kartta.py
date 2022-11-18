#!/usr/bin/python3
import cartopy.crs as ccrs
from matplotlib.pyplot import *
import matplotlib as mpl
from netCDF4 import Dataset
import matplotlib.patches as patches
import matplotlib, re, sys, luokat

luokat_köpp = ['C.b', 'D.a', 'D.b', 'D.c', 'D.d', 'ET']
luokat_ikir = luokat.ikir
cmapnimi = "jet"

def main():
    global lon, lat, platecarree
    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    kattavuus   = [-180,180,40,90]
    rcParams.update({'font.size':18,'figure.figsize':(10,10)})
    ds = Dataset('aluemaski.nc')
    lon = np.ma.getdata(ds['lon']).flatten()
    lat = np.ma.getdata(ds['lat']).flatten()
    maski = np.ma.getdata(ds['maski']).flatten()
    ds.close()

    if 'ikir' in sys.argv:
        luokitus_ = Dataset('ikirdata.nc', 'r')
        luokitus = np.zeros(len(lat)*len(lon), np.int8)
        taul = np.ma.getdata(luokitus_['luokka'])
        taul = np.round(np.mean(taul, axis=0)).astype(int)
        for i,v in enumerate(luokat_ikir):
            k = luokat.ikir.index(v)
            luokitus += (taul==k).flatten() * maski * (i+1)
        luokitus_.close()
        luokat_ = luokat_ikir
        ncol=1
        nimi = 'ikir_kartta'
    else:
        luokitus_ = Dataset('köppen1x1maski.nc', 'r')
        luokitus = np.zeros(len(lat)*len(lon), np.int8)
        for ilk,lk in enumerate(luokat_köpp):
            for k in luokitus_.variables:
                if re.match(lk, k):
                    luokitus |= np.ma.getdata(luokitus_[k]).flatten() * maski * (ilk+1)
        luokitus_.close()
        luokat_ = luokat_köpp
        ncol=2
        nimi = 'köppen_kartta'

    cmap = matplotlib.cm.get_cmap(cmapnimi, len(luokat_))
    fig = figure()
    ax = axes(projection=projektio)
    ax.coastlines()
    ax.set_extent(kattavuus, platecarree)
    luokitus = luokitus.reshape([len(lat),len(lon)])
    mx,my = np.meshgrid(lon, lat, sparse=True)
    lk = np.ma.masked_where(luokitus==0, luokitus)
    pcolormesh(mx, my, lk, cmap=cmapnimi, transform=platecarree)

    for i,l in enumerate(luokat_):
        plot(-1,-1,'.',markersize=25,color=cmap(i),label=l,transform=platecarree)
    legend(loc='lower left', fancybox=False, framealpha=1, ncol=ncol)
    tight_layout()
    if '-s' in sys.argv:
        savefig('kuvia/%s.png' %(nimi))
        clf()
    else:
        show()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

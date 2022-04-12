#!/usr/bin/python3
import xarray as xr
import numpy as np
import cartopy.crs as ccrs
from matplotlib.pyplot import *
import matplotlib, sys
import config

#Käsitellään pisteitä, joissa on jotain wetland-luokkaa tai yhtä muuta luokkaa tai molempia.
#Hylätään pisteet, joissa on merkittävästi useampaa kuin näitä kahta luokkaa.

def luo_varikartta(ch4data):
    global pienin,suurin
    pienin = np.nanpercentile(ch4data.data, 0.5)
    suurin = np.nanpercentile(ch4data.data,99.5)
    N = 1024
    cmap = matplotlib.cm.get_cmap('coolwarm',N)
    varit = np.empty(N,object)
    kanta = 10
    #negatiiviset vuot lineaarisesti ja positiiviset logaritmisesti
    for i in range(0,N//2): #negatiiviset vuot
        varit[i] = cmap(i)
    cmaplis=np.logspace(np.log(0.5)/np.log(kanta),0,N//2)
    for i in range(N//2,N): #positiiviset vuot
        varit[i] = cmap(cmaplis[i-N//2])
    return matplotlib.colors.ListedColormap(varit)

def piirra(data:xr.DataArray, subpl:int):
    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    kattavuus   = [-180,180,35,90]
    subpl_y = subplmuoto[0]-1 - subpl // subplmuoto[1]
    subpl_x = subpl % subplmuoto[1]
    xkoko = 0.94/subplmuoto[1]
    ykoko = 0.94/subplmuoto[0]
    ax = axes([0.04 + subpl_x*xkoko,
               0.04 + subpl_y*ykoko,
               xkoko-0.03, ykoko-0.05],
              projection=projektio)
    ax.coastlines()
    ax.set_extent(kattavuus,platecarree)
    data.plot.pcolormesh(transform=platecarree, cmap=cmap, norm=matplotlib.colors.DivergingNorm(0,max(pienin*4,-suurin),suurin))
    return

def main():
    global cmap, subplmuoto
    luokat_wl = ['bog','fen','marsh','tundra_wetland','permafrost_bog']
    raja_luokka = 0.1   #luokan pisteissä on vähintään näin paljon luokkaa
    raja_osuus = 0.5 #luokan pisteet ovat vähintään näin suuri osa kaikista wlluokista kys. pisteessä
    baw = xr.open_dataset('BAWLD1x1.nc')
    if '-jk' in sys.argv:
        vuot = xr.open_dataarray('flux1x1_jäätymiskausi.nc').mean(dim='time')
    else:
        vuot = xr.open_dataarray(config.edgartno_dir+'posterior.nc').mean(dim='time').\
            sel({'lat': slice(baw.lat.min(),baw.lat.max())})

    bw = baw.wetland
    wlvuo = xr.where((bw>=raja_luokka), vuot, np.nan)
    #vuo_jaett = xr.where((bw>=raja_luokka), vuot/bw, np.nan)
    cmap=luo_varikartta(wlvuo)

    rcParams.update({'figure.figsize':(14,12), 'font.size':14})
    subplmuoto = [2,3]
    for i,luokka in enumerate(luokat_wl):
        maski = (baw[luokka]>=raja_luokka) & (baw[luokka]/bw>=raja_osuus)
        piirra(xr.where(maski,vuot,np.nan),i)
        title(luokka)
    show()
    return

if __name__ == '__main__':
    main()

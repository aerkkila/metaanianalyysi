#!/usr/bin/python3
import xarray as xr
import numpy as np
import cartopy.crs as ccrs
from matplotlib.pyplot import *
import matplotlib
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
    luokka_wl = 'wetland'
    luokka_muu = 'boreal_forest'
    raja_wl_muu = 0.02 #muuluokan pisteissä on tätä vähemmän wlluokkaa
    raja_muu_muu = 0.3 #muuluokan pisteissä on vähintään näin paljon muuluokkaa
    raja_wl_wl = 0.3   #wlluokan pisteissä on vähintään näin paljon wlluokkaa
    raja_yht = 0.8     #wl- ja muuluokan yhteenlaskettu osuus on vähintään tämän verran
    baw = xr.open_dataset('BAWLD1x1.nc')
    vuot = xr.open_dataarray(config.edgartno_dir+'posterior.nc').mean(dim='time').\
        sel({'lat': slice(baw.lat.min(),baw.lat.max())})
    bm = baw[luokka_muu]
    bw = baw[luokka_wl]
    muuvuo = xr.where((bm>=raja_muu_muu) & (bw<raja_wl_muu) & (bm+bw>=raja_yht), vuot, np.nan)
    wlvuo = xr.where((bw>=raja_wl_wl) & (bm+bw>=raja_yht), vuot, np.nan)
    wlvuo_jaett = xr.where((bw>=raja_wl_wl) & (bm+bw>=raja_yht), vuot/bw, np.nan)

    rcParams.update({'figure.figsize':(14,12), 'font.size':14})
    cmap=luo_varikartta(wlvuo)
    subplmuoto = [2,2]
    piirra(muuvuo,0)
    title(luokka_muu)
    piirra(wlvuo,1)
    title(luokka_wl)
    cmap=luo_varikartta(wlvuo_jaett)
    piirra(wlvuo_jaett,2)
    title('%s/frac(%s)' %(luokka_wl,luokka_wl))
    show()
    return

if __name__ == '__main__':
    main()

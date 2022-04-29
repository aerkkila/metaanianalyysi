#!/usr/bin/python3
import xarray as xr
import config
import numpy as np
import sys
from threading import Thread

#Interpoloinnin saisi yhdelläkin komennolla.
#Teeön se kuitenkin useassa vaiheessa, jolloin saadaan tulostettua tietoa interpoloinnin etenemisestä.
##teeön on yks. 1. pers. optatiivi sanasta tehdä
def interpoloi(ds,ch4,kohde,alku,loppu,patka,rivi):
    t=alku
    while t<loppu-patka:
        muoto_mjon = '\033[%iF%%i/%%i\033[%iE' %(rivi,rivi)
        sys.stdout.flush()
        print(muoto_mjon %(t+1,loppu), end='')
        kohde[t:t+patka, ...] = ds.interp(time=ch4.time.data[t:t+patka], lat=ch4.lat.data, lon=ch4.lon.data, method='nearest')
        t += patka
    print(muoto_mjon %(loppu,loppu), end='')
    sys.stdout.flush()
    kohde[t:loppu, ...] = ds.interp(time=ch4.time.data[t:loppu], lat=ch4.lat.data, lon=ch4.lon.data)
    return

def main():
    ds = xr.open_dataset(config.WAD2M+'WAD2M_wetlands_2000-2020_025deg_Ver2.0.nc').Fw.astype(np.float32)
    ch4 = xr.open_dataarray('./flux1x1_whole_year.nc')
    uusi = np.empty(ch4.data.shape, np.float32)
    saikeita = 4
    print('\n'*saikeita, end='')
    saikeet = np.empty(saikeita, object)
    for i in range(saikeita):
        saikeet[i] = Thread(target=interpoloi, kwargs={'ds':ds,
                                                       'ch4':ch4,
                                                       'kohde':uusi,
                                                       'alku':ch4.time.size//saikeita*i,
                                                       'loppu':min(ch4.time.size//saikeita*(i+1), ch4.time.size),
                                                       'patka':128,
                                                       'rivi':saikeita-i})
        saikeet[i].start()
    for saie in saikeet:
        saie.join()

    uusi_ds = xr.DataArray(uusi, name='fw', dims=ch4.dims, coords=ch4.coords)
    ch4.close(); ds.close()
    uusi_ds.to_netcdf(config.WAD2M+'wad2m.nc')
    uusi_ds.close()
    return 0

if __name__=='__main__':
    main()

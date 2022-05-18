#!/usr/bin/python3
import xarray as xr
import config
import numpy as np
import sys
from multiprocessing import Process
import multiprocessing.shared_memory as shm

#Interpoloinnin saisi yhdelläkin komennolla.
#Se jaetaan kuitenkin osiin, jotta voidaan tulostaa tieto prosessin etetemisestä.
def interpoloi(ds,ch4,alku,loppu,patka,rivi):
    kohde_shm = shm.SharedMemory(name=jaettu.name)
    kohde = np.ndarray(ch4.shape, np.float32, buffer=kohde_shm.buf)
    t=alku
    while t<loppu-patka:
        muoto_mjon = '\033[%iF%%i/%%i\033[%iE' %(rivi,rivi)
        print(muoto_mjon %(t+1,loppu), end='')
        sys.stdout.flush()
        kohde[t:t+patka, ...] = ds.interp(time=ch4.time.data[t:t+patka], lat=ch4.lat.data, lon=ch4.lon.data, method='nearest')
        t += patka
    print(muoto_mjon %(loppu,loppu), end='')
    sys.stdout.flush()
    kohde[t:loppu, ...] = ds.interp(time=ch4.time.data[t:loppu], lat=ch4.lat.data, lon=ch4.lon.data)
    kohde_shm.close()
    return

def main():
    global jaettu
    ds = xr.open_dataset(config.WAD2M+'WAD2M_wetlands_2000-2020_025deg_Ver2.0.nc').Fw.astype(np.float32)
    ch4 = xr.open_dataarray('./flux1x1_whole_year.nc')
    jaettu = shm.SharedMemory(create=True, size=ch4.data.size*4)
    uusi = np.ndarray(ch4.data.shape, np.float32, buffer=jaettu.buf)
    prosesseja = 4
    print('\n'*prosesseja, end='')
    prosessit = np.empty(prosesseja, object)
    for i in range(prosesseja):
        prosessit[i] = Process(target=interpoloi,
                               kwargs={'ds':ds,
                                       'ch4':ch4,
                                       'alku':ch4.time.size//prosesseja*i,
                                       'loppu':min(ch4.time.size//prosesseja*(i+1), ch4.time.size),
                                       'patka':128,
                                       'rivi':prosesseja-i})
        prosessit[i].start()
    for prosessi in prosessit:
        prosessi.join()

    uusi_ds = xr.DataArray(uusi, name='fw', dims=ch4.dims, coords=ch4.coords)
    ch4.close(); ds.close()
    uusi_ds.to_netcdf(config.WAD2M+'wad2m.nc')
    uusi_ds.close()
    jaettu.close()
    jaettu.unlink()
    return 0

if __name__=='__main__':
    main()

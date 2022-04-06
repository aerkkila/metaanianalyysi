#!/usr/bin/python3
import xarray as xr
import numpy as np
from config import edgartno1d_t
import pandas as pd
import sys
from threading import Thread

def kirjoita(data,vuosi):
    xr.concat(data,dim='time').to_netcdf('%s_%i.nc' %(sys.argv[0][:-3],vuosi))

def main():
    maan_osuusraja = 30 # %
    ikirmaa = xr.open_dataset('prf_maa.nc')
    ikirmaa = xr.where(ikirmaa<maan_osuusraja,0,ikirmaa)
    metaani = xr.open_dataarray(edgartno1d_t).sel({'lat':slice(ikirmaa.lat.min(),ikirmaa.lat.max())})
    #metaani rajataan prfdatan aikasarjaan
    prf0 = pd.Period('%s-01-01' %(ikirmaa.time.data[0]), freq='D')
    prf1 = pd.Period('%s-01-01' %(ikirmaa.time.data[-1]+1), freq='D')
    met0 = pd.Period(metaani.time.data[0], freq='D')
    alku = (prf0-met0).n
    loppu = (prf1-met0).n
    metaani = metaani[alku:loppu,...]
    #tehdään uusi data, jossa on ikirmaan muuttuja-alueilla päivittäiset metaanivuot kertaa maaluokan osuus
    i=0
    print('')
    for v,vuosi in enumerate(ikirmaa.time.data):
        print("\033[1F%i/%i\033[K" %(v+1,len(ikirmaa.time)))
        aikaraja = pd.Period('%s-01-01' %(vuosi+1), freq='D')
        n = (aikaraja-pd.Period(metaani.time.data[i],freq='D')).n
        kerrottava = ikirmaa.isel({'time':v})
        #koko aikasarja ei mahdu muistiin samanaikaisesti, joten tallennetaan vuosi kerrallaan
        uusi = np.empty(n,object)
        for j in range(n):
            print("\r%i/%i\033[K" %(j+1,n), end='')
            uusi[j] = (kerrottava * metaani[i,...]).assign_coords({'time':metaani.time.data[i]})
            i += 1
        if v != 0:
            thread.join()
        thread = Thread(target=kirjoita, args=(uusi,vuosi))
        thread.start()
    thread.join()
    print('')

if __name__ == '__main__':
    main()

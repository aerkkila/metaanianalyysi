#!/usr/bin/python3
import xarray as xr
import numpy as np
import pandas as pd
import sys, config
from multiprocessing import Process

def vuoden_tulos(vuosi,ind_paiva):
    aikaraja = pd.Period('%s-01-01' %(vuosi+1), freq='D')
    n = (aikaraja-pd.Period(metaani.time.data[ind_paiva],freq='D')).n
    kerrottava = ikirmaa.sel({'time':vuosi})
    #koko aikasarja ei mahtune ram-muistiin samanaikaisesti, joten tallennetaan vuosi kerrallaan
    uusi = np.empty(n,object)
    for j in range(n):
        uusi[j] = (kerrottava * metaani[ind_paiva,...]).assign_coords({'time':metaani.time.data[ind_paiva]})
        ind_paiva += 1
    xr.concat(uusi,dim='time').to_netcdf('%s_%i.nc' %(sys.argv[0][:-3],vuosi))
    return ind_paiva

def tee_vuodet(vuosi0, vuosi1, ind_paiva, p_ind):
    muoto = "\033[%iF%%i/%%i\033[K\033[%iE" %(p_ind,p_ind)
    for v in range(vuosi1-vuosi0):
        print(muoto %(v+1,vuosi1-vuosi0), end='')
        sys.stdout.flush()
        ind_paiva = vuoden_tulos(vuosi0+v, ind_paiva)
    return

def main():
    global ikirmaa, metaani
    ikirmaa = xr.open_dataset('prf_maa.nc')
    metaani = xr.open_dataset(config.edgartno_dir+'flux1x1_1d.nc', engine='h5netcdf')['flux_bio_posterior'].\
        sel({'lat':slice(ikirmaa.lat.min(),ikirmaa.lat.max())})
    #metaani rajataan ikiroudan aikasarjaan
    prf0 = pd.Period('%s-01-01' %(ikirmaa.time.data[0]), freq='D')
    prf1 = pd.Period('%s-01-01' %(ikirmaa.time.data[-1]+1), freq='D')
    met0 = pd.Period(metaani.time.data[0], freq='D')
    alku = (prf0-met0).n
    loppu = (prf1-met0).n
    metaani = metaani[alku:loppu,...]
    #tehdään uusi data, jossa on ikirmaan muuttuja-alueilla päivittäiset metaanivuot kertaa maaluokan osuus
    prosesseja = 3
    prosessit = np.empty(prosesseja-1, object)
    vuosia = len(ikirmaa.time)
    print('\n'*prosesseja, end='')
    aika0 = pd.Period('%s-01-01' %(ikirmaa.time.data[0]), freq='D')
    ind_paiva = (aika0-pd.Period(metaani.time.data[0],freq='D')).n
    vuosi0 = ikirmaa.time.data[0]
    for p in range(prosesseja-1):
        vuosi1 = ikirmaa.time.data[0] + int((p+1)*vuosia/prosesseja)
        prosessit[p] = Process(target=tee_vuodet, args=(vuosi0, vuosi1, ind_paiva, prosesseja-p))
        prosessit[p].start()
        ind_paiva += (pd.Period("%4i-01-01" %(vuosi1)) - pd.Period("%4i-01-01" %(vuosi0))).n
        vuosi0 = vuosi1
    tee_vuodet(vuosi0, ikirmaa.time.data[-1]+1, ind_paiva, 1)
    for p in prosessit:
        p.join()
    print('')

if __name__ == '__main__':
    main()

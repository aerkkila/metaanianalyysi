#!/usr/bin/python3
import xarray as xr
import pandas as pd
import numpy as np

def main():
    muuttuja = 'flux_bio_prior_mean'
    kerroin = 'flux_multiplier_m_bio'
    uudet_muuttujat = ['flux_bio_prior', 'flux_bio_posterior']
    ds = xr.open_dataset('flux1x1.nc')
    haku = 'yhdistettävät/flux1x1_'
    historia = ds.attrs['history']
    pit = len(haku)
    paikka=0
    ajat0 = np.empty(ds.sizes['time'],object)
    
    for i in range(len(ajat0)):
        osuma = historia[paikka:].index(haku)+pit
        paikka += osuma
        vuosi=historia[paikka:paikka+4]
        paikka+=4
        kk = historia[paikka:paikka+2]
        paikka+=2
        pp = historia[paikka:paikka+2]
        paikka+=2
        ajat0[i] = pd.Timestamp('%s-%s-%s' %(vuosi,kk,pp))

    prior = ds[muuttuja]
    posterior = ds[muuttuja]*ds[kerroin].astype(np.float32)
    ds.close()
    ajat1 = []
    data_pri = []
    data_post = []
    for i in range(len(ajat0)-1):
        paivia = (ajat0[i+1]-ajat0[i]).days
        ajat1.extend(pd.date_range(ajat0[i], periods=paivia, freq='D'))
        aika = np.linspace(i, i+1, num=paivia, endpoint=False)
        data_pri.extend(prior.interp(time=aika, assume_sorted=True, kwargs={'copy':False}).astype(np.float32))
        data_post.extend(posterior.interp(time=aika, assume_sorted=True, kwargs={'copy':False}).astype(np.float32))
        print('\r%i/%i' %(i+1,len(ajat0)-1), end='')
    data_pri = xr.concat(data_pri,dim='time').transpose('time','lat','lon').assign_coords({'time':ajat1})
    data_post = xr.concat(data_post,dim='time').transpose('time','lat','lon').assign_coords({'time':ajat1})
    print('')
    ds = xr.Dataset({uudet_muuttujat[0]:data_pri, uudet_muuttujat[1]:data_post})
    ds.to_netcdf('flux1x1_1d.nc')
    return

if __name__ == '__main__':
    main()

#!/usr/bin/python3
import xarray as xr
import pandas as pd
import numpy as np

def main():
    muuttuja = 'flux_bio_prior_mean'
    kerroin = 'flux_multiplier_m_bio'
    uusi_muuttuja = 'flux_bio_posterior'
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

    posterior = ds[muuttuja]*ds[kerroin].astype(np.float32)
    ds.close()
    ajat1 = []
    data = []
    for i in range(len(ajat0)-1):
        paivia = (ajat0[i+1]-ajat0[i]).days
        ajat1.extend(pd.date_range(ajat0[i], periods=paivia, freq='D'))
        data.extend(posterior.interp(time=np.linspace(i, i+1, num=paivia, endpoint=False),
                                     assume_sorted=True, kwargs={'copy':False}).astype(np.float32))
        print('\r%i/%i' %(i+1,len(ajat0)-1), end='')
    data = xr.concat(data,dim='time').transpose('time','lat','lon').\
        assign_coords({'time':ajat1}).rename(uusi_muuttuja)
    #kopioidaan, jotta aika-attribuutti päivittyy
    tallennus = xr.DataArray(data = data.data,
                             coords = {'time':data.time.data, 'lat':data.lat.data, 'lon':data.lon.data},
                             dims = ['time','lat','lon'])
    print('')
    data.to_netcdf('flux1x1_1d.nc')
    return

if __name__ == '__main__':
    main()

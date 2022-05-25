#!/usr/bin/python3
import numpy as np
import xarray as xr
import copy, sys

nimet = ['bog', 'fen', 'bog+fen', 'marsh', 'tundra_wetland', 'permafrost_bog', 'wetland']
kaudet = ['whole_year', 'summer', 'freezing', 'winter']

def tee_data(kausi='whole_year', tmp=False, pakota=False):
    raja_wl = 0.03
    dsbaw = xr.open_dataset('./BAWLD1x1.nc')[nimet]
    dsbaw = xr.where(dsbaw.wetland>=raja_wl, dsbaw, np.nan)
    dsvuo = xr.open_dataset('./flux1x1_%s.nc' %(kausi))['flux_bio_posterior'].mean(dim='time')
    if kausi != 'whole_year':
        kausien_pituudet = xr.open_dataset('kausien_pituudet.nc')[kausi].mean(dim='vuosi').data.flatten()
    else:
        kausien_pituudet = [365.25]*55*360
    dsvuo *= 1e9
    lon,lat = np.meshgrid(dsvuo.lon.data, dsvuo.lat.data)
    lon = lon.flatten()
    lat = lat.flatten()

    ds = dsbaw
    dt = np.empty([len(ds.keys()), ds[list(ds.keys())[0]].data.size])
    for i,key in enumerate(ds.keys()):
        dt[i,:] = ds[key].data.flatten()
    dt = dt.transpose()
    dty = dsvuo.data.flatten()
    lasku = 0
    #dropna
    for i in range(dt.shape[0]):
        if all(dt[i,:] == dt[i,:]) and dty[i] == dty[i]:
            lasku += 1
    uusix = np.empty([lasku, dt.shape[1]])
    uusiy = np.empty(lasku)
    uusilat = np.empty(lasku)
    uusilon = np.empty(lasku, np.float32)
    uusikausi = np.empty(lasku, np.float32)
    maski = np.zeros(dt.shape[0], bool)
    ind = 0
    for i in range(dt.shape[0]):
        if all(dt[i,:] == dt[i,:]) and dty[i] == dty[i]:
            uusix[ind,:] = dt[i,:]
            uusiy[ind] = dty[i]
            uusilat[ind] = lat[i]
            uusilon[ind] = lon[i]
            uusikausi[ind] = kausien_pituudet[i]
            maski[ind] = True
            ind += 1
    return [uusix, uusiy, list(ds.keys()), uusilat, uusikausi, maski, uusilon]

if __name__=='__main__':
    for kausi in kaudet:
        tee_data(kausi)

#!/usr/bin/python3
import xarray as xr
import pandas as pd
import numpy as np
import sys

def main():
    maadata = xr.open_dataset('BAWLD1x1.nc')
    prfdata = xr.open_dataset('prfdata.nc').sel({'lat':slice(maadata.lat.min(),maadata.lat.max())})
    prf_maa = np.full(len(prfdata.keys()), {}, object)
    for i, ikirl in enumerate(prfdata.keys()):
        for m, maalaji in enumerate(maadata.keys()):
            prf_maa[i].update({maalaji: maadata[maalaji].where(prfdata[ikirl],0).astype(np.float32)})
        prf_maa[i] = xr.Dataset(prf_maa[i])
    ds = xr.concat(prf_maa, 'prf')
    ds = ds.transpose('prf','time','lat','lon')
    ds.to_netcdf('%s.nc' %(sys.argv[0][:-3]))

if __name__ == '__main__':
    main()

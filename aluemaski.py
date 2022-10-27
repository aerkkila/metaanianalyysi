#!/usr/bin/python3
import xarray as xr

ds = xr.open_dataarray('kaudet2.nc')[0,...].to_dataset(name='maski').drop_vars('time')
print(ds)
ds.to_netcdf('aluemaski.nc')

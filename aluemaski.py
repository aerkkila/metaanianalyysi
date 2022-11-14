#!/usr/bin/python3
import xarray as xr

ds = xr.open_dataarray('../smos_uusi/ft_percent/number_of_pixels.nc').astype('bool').to_dataset(name='maski')
print(ds)
ds.to_netcdf('aluemaski.nc')

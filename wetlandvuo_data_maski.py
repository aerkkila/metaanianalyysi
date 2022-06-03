#!/usr/bin/python3
import xarray as xr
import wetlandvuo_data as wld
import numpy as np
import sys

if __name__=='__main__':
    data = wld.tee_data2('whole_year')
    lat = np.arange(29.5, 84, 1)
    lon = np.arange(-179.5, 180, 1)
    da = xr.DataArray(dims=['lat','lon'],
                      coords={'lat':lat, 'lon':lon},
                      data=data['maski'].astype(np.int8).reshape([len(lat),len(lon)]),
                      name='data')
    da.to_netcdf('%s.nc' %(sys.argv[0][:-3]))

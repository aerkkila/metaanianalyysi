#!/usr/bin/python3
from prf import *
import xarray as xr

if __name__ == '__main__':
    prfolio = Prf()
    prfdata = xr.concat(prfolio.data, dim='time').sel({'lat':slice(23.5,90)}).astype(np.float32)
    avgluok = luokittelu_num_xr(prfdata.mean(dim='time'))
    tietue = {'luokka':avgluok, 'osuus':prfdata}
    ds = xr.Dataset(tietue)
    ds.to_netcdf('%s.nc' %sys.argv[0][:-3])

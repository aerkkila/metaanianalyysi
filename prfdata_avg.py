#!/usr/bin/python3
from prf import *

if __name__ == '__main__':
    prfolio = Prf()
    prfdata = xr.concat(prfolio.data, dim='time')
    avgluok = luokittelu1_num_xr(prfdata.mean(dim='time'))
    avgluok.name = 'avg'
    avgluok.to_netcdf('%s.nc' %sys.argv[0][:-3])

#!/usr/bin/python3
from prf import *

if __name__ == '__main__':
    prfolio = Prf()
    prfdata = xr.concat(prfolio.data, dim='time')
    prfdata = prfdata.assign_coords({'time':prfolio.vuodet})
    prfluok = luokittelu_num_xr(prfdata)
    luokat_set = {}
    for i,luok in enumerate(luokat):
        luokat_set.update({luok: xr.where(prfluok==i,1,0)})
    ds = xr.Dataset(luokat_set)
    ds.to_netcdf('%s.nc' %sys.argv[0][:-3])

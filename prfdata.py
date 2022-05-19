#!/usr/bin/python3
from prf import *
from numpy import int8

if __name__ == '__main__':
    prfolio = Prf()
    prfdata = xr.concat(prfolio.data, dim='time')
    prfdata = prfdata.assign_coords({'time':prfolio.vuodet})
    prfluok = luokittelu_num_xr(prfdata)
    luokat_set = {"luokka":prfluok}
    for i,luok in enumerate(luokat):
        luokat_set.update({luok: xr.where(prfluok==i,1,0).astype(int8)})
    ds = xr.Dataset(luokat_set)
    ds.to_netcdf('%s.nc' %sys.argv[0][:-3])

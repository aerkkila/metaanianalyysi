#!/usr/bin/python3
import xarray as xr
import numpy as np
import sys
from flux1x1 import kaudet

suot = ['bog','fen','tundra_wetland','permafrost_bog']

def vuo_bawld(kausi:str):
    bawld = xr.open_dataset('./BAWLD1x1.nc')
    vuotied = 'flux1x1_%s.nc' %kausi
    vuo = xr.open_dataarray(vuotied)
    wetl = bawld['wetland']
    bawld = xr.where(wetl>0.1, bawld, np.nan)
    bawld = bawld[suot]
    uusi = {}
    for nimi_ind,nimi in enumerate(bawld.keys()):
        vuodt = vuo.data.reshape([vuo.time.size, vuo.lat.size*vuo.lon.size]).copy()
        bawflat = bawld[nimi].data.flatten()
        wetflat = wetl.data.flatten()
        maski = (bawflat/wetflat < 0.5) | (bawflat!=bawflat) | (wetflat!=wetflat)
        for t in range(vuo.time.size):
            vuodt[t,maski] = np.nan
        uusi.update({ nimi: xr.DataArray(np.reshape(vuodt, vuo.data.shape),
                                         dims=('time','lat','lon'),
                                         coords = ({'time':vuo.time.data,
                                                    'lat':vuo.lat.data,
                                                    'lon':vuo.lon.data})) })
    vuo.close()
    return xr.Dataset(uusi)

if __name__ == '__main__':
    print('')
    for i,kausi in enumerate(kaudet.keys()):
        print('\033[F%i/%i\033[K' %(i+1,len(kaudet.keys())))
        vuo_bawld(kausi).to_netcdf('%s_%s.nc' %(sys.argv[0][:-3],kausi))

#!/usr/bin/python3
import xarray as xr
import numpy as np
import sys, köppen
from vuo_bawld import kaudet

def vuo_koppen(kausi:str):
    kopp = köppen.lue_oletusluokkamaskit_dataset()
    vuotied = 'flux1x1_%s.nc' %kausi
    vuo = xr.open_dataarray(vuotied)
    uusi = {}
    for nimi_ind,nimi in enumerate(kopp.keys()):
        vuodt = vuo.data.reshape([vuo.time.size, vuo.lat.size*vuo.lon.size]).copy()
        maski = ~kopp[nimi].data.flatten()
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
        vuo_koppen(kausi).to_netcdf('%s_%s.nc' %(sys.argv[0][:-3],kausi))

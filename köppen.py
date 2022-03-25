import xarray as xr
import numpy as np
import re

def lue_oletusluokkamaskit_dataset(ncnimi='köppen1x1maski.nc'):
    luokat = ['D.c','D.d','ET']
    dset = xr.open_dataset(ncnimi)
    koko = dset[list(dset.keys())[0]].size
    uusidata = np.zeros([len(luokat),koko],bool)
    for nimi in dset.keys():
        for i,luok in enumerate(luokat):
            if not re.match(luok,nimi):
                continue
            uusidata[i,:] = uusidata[i,:] | dset[nimi].data.flatten()
    dvars = {}
    for i,luok in enumerate(luokat):
        npdata = uusidata[i,:].reshape(dset[list(dset.keys())[0]].shape)
        syote = xr.DataArray(data=npdata,coords=dset.coords,dims=dset.dims)
        dvars.update({ luok : syote })
    return xr.Dataset(data_vars=dvars,coords=dset.coords)

if __name__ == '__main__':
    print(lue_oletusluokkamaskit_dataset())

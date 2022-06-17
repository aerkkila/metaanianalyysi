#!/usr/bin/python3
import numpy as np
import xarray as xr
from PIL import Image
import re, os, sys, luokat
from config import tyotiedostot

def lue_numpy(hila='1x1') -> dict:
    kansio = tyotiedostot + 'PermafrostExtent/'
    vuodet = []
    nimi0 = 'PRF_Extent'
    nimi1 = '_%s.tif' %hila
    for tiednimi in os.listdir(kansio):
        vuosi = re.search('(?<=%s)[0-9]+(?=%s)'%(nimi0,nimi1), tiednimi)
        if vuosi:
            vuodet.append(vuosi.group(0))
    vuodet = np.sort(np.array(vuodet,np.int32))
    tiednimi = kansio + nimi0 + str(vuodet[0]) + nimi1
    with Image.open(tiednimi) as im:
        muoto = im.size[::-1]
    tifdata = np.empty([len(vuodet),np.product(muoto)])
    for i,vuosi in enumerate(vuodet):
        with Image.open( kansio + nimi0 + str(vuosi) + nimi1 ) as im:
            tifdata[i] = np.flip( np.array(im.getdata()).reshape(muoto), axis=0 ).flatten()
    muoto = [ len(vuodet), muoto[0], muoto[1] ]
    tifdata = tifdata.reshape(muoto)
    tifdata = tifdata[:, int(29.5+89.5): int(84.5+89.5), :] # rajataan asteisiin 29.5–83.5
    return {'vuodet':vuodet, 'data':tifdata}

def lue_xarray(hila) -> dict:
    lnp = lue_numpy(hila)
    lat = np.arange(29.5, 84)
    lon = np.arange(-179.5,180)
    xrdata = xr.DataArray(data=lnp['data'], dims=('vuosi','lat','lon'), coords={'vuosi':lnp['vuodet'],'lat':lat,'lon':lon})
    return xrdata

def luokittelu_num_xr(data:xr.DataArray) -> xr.DataArray:
    dt = data.data.flatten()
    uusi = np.empty(dt.shape,np.int8)
    uusi[  (dt<10)           ] = 0
    uusi[ (10<=dt) & (dt<50) ] = 1
    uusi[ (50<=dt) & (dt<90) ] = 2
    uusi[ (90<=dt)           ] = 3
    return xr.DataArray(data=uusi.reshape(data.data.shape), coords=data.coords, dims=data.dims)

if __name__ == '__main__':
    prf = lue_xarray('1x1')
    prfluok = luokittelu_num_xr(prf)
    luokat_set = {"luokka":prfluok}
    for i,luok in enumerate(luokat.ikir):
        luokat_set.update({luok: xr.where(prfluok==i,1,0).astype(np.int8)})
    ds = xr.Dataset(luokat_set)
    ds.to_netcdf('%s.nc' %sys.argv[0][:-3])
    np.save("%s_%i_%i.npy" %(sys.argv[0][:-3],ds.vuosi.data[0],ds.vuosi.data[-1]), ds.luokka.data.flatten())

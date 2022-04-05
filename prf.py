#!/usr/bin/python3
from PIL import Image
import numpy as np
import re, os, sys
import xarray as xr
from config import tyotiedostot

def lue_numpy(hila='1x1') -> dict:
    kansio = tyotiedostot + 'PermafrostExtent/'
    vuodet = []
    nimi0 = 'PRF_Extent'
    nimi1 = '_%s.tif' %hila
    for tiednimi in os.listdir(kansio):
        vuosi = re.search( '(?<=%s)[0-9]+(?=%s)'%(nimi0,nimi1), tiednimi )
        if vuosi:
            vuodet.append(vuosi.group(0))
    vuodet = sorted(np.array(vuodet,int))
    tiednimi = kansio + nimi0 + str(vuodet[0]) + nimi1
    with Image.open(tiednimi) as im:
        muoto = im.size[::-1]
    tifdata = np.empty([len(vuodet),np.product(muoto)])
    for i,vuosi in enumerate(vuodet):
        with Image.open( kansio + nimi0 + str(vuosi) + nimi1 ) as im:
            tifdata[i] = np.flip( np.array(im.getdata()).reshape(muoto), axis=0 ).flatten()
    muoto = [ len(vuodet), muoto[0], muoto[1] ]
    return { 'vuodet':vuodet, 'data':tifdata.reshape(muoto) }

def lue_xarray(hila) -> dict:
    lnp = lue_numpy(hila)
    lat = np.arange(-89.5,90)
    lon = np.arange(-179.5,180)
    time = lnp['vuodet']
    xrdata = xr.DataArray( data=lnp['data'], dims=('time','lat','lon'), coords={'time':time,'lat':lat,'lon':lon} )
    lnp['data'] = xrdata
    return lnp

def rajaa1x1( dataarr, lat01 ):
    if type(dataarr) == np.ndarray:
        print('Muoto olkoon xarray (prf.py:rajaa1x1).')
        exit()
    elif type(dataarr) == xr.DataArray:
        return dataarr[:, (lat01[0]<=dataarr.lat) & (dataarr.lat<lat01[1]) ]
    print('\033[1;31mVirhe (rajaa1x1)\033[0m. Tuntematon muoto.')
    exit()

class Prf():
    def __init__(self,hila='1x1',muoto='xarray'):
        a = lue_numpy(hila) if muoto=='numpy' else lue_xarray(hila)
        if muoto=='numpy':
            print('\033[1;33mVaroitus:\033[0m Prf-numpy ei välttämättä toimi halutusti. Muoto olkoon xarray.')
        self.vuodet = a['vuodet']
        self.data   = a['data'  ]
        self.hila = hila
        return
    def __str__(self):
        return ( f'muoto: {self.data.shape}\n'
                 f'hila: {self.hila}\n'
                 f'vuodet: {self.vuodet}\n'
                 f'data: {self.data}' )
    def rajaa(self,lat01):
        if self.hila == '1x1':
            self.data = rajaa1x1(self.data,lat01)
        else:
            print( 'Rajaaminen ei onnistu. Tuntematon muoto: \"%s\".' %(self.hila) )
        return self

luokat = ['distinguishing isolated', 'sporadic', 'discontinuous', 'continuous']
luokat1 = ['non permafrost', 'sporadic', 'discontinuous', 'continuous']

def luokittelu_str_xr(data:xr.DataArray) -> xr.DataArray:
    dt = data.data.flatten()
    uusi = np.empty(dt.shape,object)
    uusi[  0==dt             ] = None
    uusi[ (0 < dt) & (dt<10) ] = luokat[0]
    uusi[ (10<=dt) & (dt<50) ] = luokat[1]
    uusi[ (50<=dt) & (dt<90) ] = luokat[2]
    uusi[ (90<=dt)           ] = luokat[3]
    return xr.DataArray( data=uusi.reshape(data.data.shape), coords=data.coords, dims=data.dims )

def luokittelu1_str_xr(data:xr.DataArray) -> xr.DataArray:
    dt = data.data.flatten()
    uusi = np.empty(dt.shape,object)
    uusi[  (dt<10)           ] = luokat1[0]
    uusi[ (10<=dt) & (dt<50) ] = luokat1[1]
    uusi[ (50<=dt) & (dt<90) ] = luokat1[2]
    uusi[ (90<=dt)           ] = luokat1[3]
    return xr.DataArray( data=uusi.reshape(data.data.shape), coords=data.coords, dims=data.dims )

def luokittelu1_num_xr(data:xr.DataArray) -> xr.DataArray:
    dt = data.data.flatten()
    uusi = np.empty(dt.shape,object)
    uusi[  (dt<10)           ] = 0
    uusi[ (10<=dt) & (dt<50) ] = 1
    uusi[ (50<=dt) & (dt<90) ] = 2
    uusi[ (90<=dt)           ] = 3
    return xr.DataArray( data=uusi.reshape(data.data.shape), coords=data.coords, dims=data.dims )

if __name__ == '__main__':
    prfolio = Prf()
    prfdata = xr.concat(prfolio.data, dim='time')
    prfdata.assign_coords({'time':prfolio.vuodet})
    prfluok = luokittelu1_num_xr(prfdata)
    luokat_set = {}
    for i,luok in enumerate(luokat1):
        luokat_set.update({luok: xr.where(prfluok==i,1,0)})
    xr.Dataset(luokat_set).to_netcdf('%s.nc' %sys.argv[0][:-3])

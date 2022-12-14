import xarray as xr
import os, re, warnings
import numpy as np
from config import tyotiedostot

def lue_doyt(kumpi='start') -> xr.DataArray:
    if(kumpi == 'start'):
        muuttuja = 'autumn_end'
    else:
        muuttuja = 'spring_start'
    kansio = os.getcwd()
    os.chdir(tyotiedostot+'FT_implementointi/FT_percents_pixel_ease_flag/DOY')
    muoto = f'(?<=winter_{kumpi}_doy_)[0-9]+(?=\.nc)'
    vuodet = []
    for tied in os.listdir('.'):
        vuosi = re.search(muoto, tied)
        if vuosi:
            vuodet.append(int(vuosi.group(0)))
    vuodet = vuodet[1:-1] #ensimmäinen ja viimeinen vuosi ovat omituisia
    dat = xr.open_dataset(f'winter_{kumpi}_doy_{vuodet[0]}.nc')
    uusi = xr.DataArray( dims=('time', 'lat' ,'lon'),
                         coords=({'time':vuodet, 'lat':dat.lat.data, 'lon':dat.lon.data}) )
    uusi.loc[vuodet[0],:,:] = dat[muuttuja]
    dat.close()
    for vuosi in vuodet[1:]:
        dat = xr.open_dataset(f'winter_{kumpi}_doy_{vuosi}.nc')
        uusi.loc[vuosi,:,:] = dat[muuttuja]
        dat.close()
    os.chdir(kansio)
    return uusi

def lue_avgdoy(startend):
    doy = lue_doyt(startend)
    with warnings.catch_warnings():
        warnings.filterwarnings( action='ignore', message='Mean of empty slice' )
        return doy.mean(dim='time')

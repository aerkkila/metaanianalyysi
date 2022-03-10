import xarray as xr
import os, re
import numpy as np
from configure import tyotiedostot

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
    #alku ei ole hyvä ensimmäisenä ja loppu viimeisenä vuonna
    if(kumpi=='start'):
        vuodet = vuodet[1:]
    else:
        vuodet = vuodet[:-1]
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

def doy2numpy(doy):
    data = np.empty( len(doy.data.flatten()) )
    pit = len(doy[0,:,:].data.flatten())
    for v in range(len(doy.time)):
        data1 = doy[v,:,:].data.flatten()
        with np.errstate(invalid='ignore'):
            data1[data1<-300] = np.nan
        data[ v*pit : (v+1)*pit ] = data1
    return data

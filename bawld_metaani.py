import xarray as xr
import numpy as np
import config

suot = ['bog','fen','tundra_wetland','permafrost_bog']

def bawld_metaani(vuotied):
    baw = xr.open_dataset('./BAWLD1x1.nc')
    vuo = xr.open_dataarray(vuotied).sel({'lat':slice(baw.lat.min(),baw.lat.max())})
    ajat = xr.open_dataarray(config.tyotiedostot + 'FT_implementointi/FT_percents_pixel_ease_flag/DOY/winter_end_doy_2014.nc')
    baw = xr.where(ajat==ajat, baw, np.nan)
    ajat.close()
    wetl = baw['wetland']
    baw = xr.where(wetl>0.2, baw, np.nan)
    baw = baw[suot]
    for nimi in baw.keys():
        baw[nimi] = xr.where(baw[nimi]/wetl>=0.5, vuo, np.nan)
    vuo.close()
    return baw

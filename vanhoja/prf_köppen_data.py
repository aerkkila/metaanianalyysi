#!/usr/bin/python3
#import numpy as np
#import sys
#import xarray as xr
#import pandas as pd

def _vanha_valmista_data(startend):
    #köppen-data
    koppdf = köppen.lue_oletusluokkamaskit_dataset('köppen1x1maski.nc').to_dataframe()
    koppdf.where(koppdf, np.nan, inplace=True)
    #yhdistetään talven ajankohta
    doy = taj.lue_avgdoy(startend)
    koppdf = koppdf.mul(doy.data.flatten(), axis=0)
    #ikiroutadata
    ikirouta = prf.Prf().rajaa( (doy.lat.min(), doy.lat.max()+1) ).data.mean(dim='time')
    ikirstr = prf.luokittelu_str_xr(ikirouta).data.flatten()
    #rajataan tarkemmin määrittelyalueeseen
    doy = doy.data.flatten()
    valinta = doy==doy
    koppdf = koppdf[valinta]
    ikirstr = ikirstr[valinta]
    doy = doy[valinta]
    #yhdistetään ikirouta
    ikirluokat = prf.luokat
    for i,ikirluok in enumerate(ikirluokat):
        df = koppdf.loc[ikirstr==ikirluok,:]
        df.to_csv('prf_köppen_%s%i.csv' %(startend,i))

if __name__ == '__main__':
    print("Tämä on vanhentunut. Lataa data erillisinä paloina.")

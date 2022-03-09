#!/usr/bin/python3
import pandas as pd
import xarray as xr
import numpy as np
from matplotlib.pyplot import *
import warnings
import prf_extent as prf
import talven_ajankohta as taj
import köppen_laatikko_plot as klp

if __name__ == '__main__':
    rcParams.update({'font.size':13,'figure.figsize':(12,10)})
    koppdoy = klp.dataframe_luokka_doy('start')
    print(koppdoy)
    exit()
    with warnings.catch_warnings():
        warnings.filterwarnings( action='ignore', message='Mean of empty slice' )
        koppdoy = koppdoy.mean(dim='time')
    print(koppdoy)

    exit()
    doy = taj.lue_doyt()
    with warnings.catch_warnings():
        warnings.filterwarnings( action='ignore', message='Mean of empty slice' )
        doy = doy.mean(dim='time')

    ikirouta = prf.Prf('1x1').rajaa( (doy.lat.min(), doy.lat.max()+1) ) #pitäisi olla 25km, koska tämä vääristää tuloksia
    ikirstr = prf.luokittelu_str(np.mean(ikirouta.data,axis=0))

    kopp = klp.lue_luokitus()
    kluokat = np.unique(kopp)
    data = np.empty(kluokat,object)
    for i,kluok in enumerate(kluokat):
        doydata = doy.data.copy()
        with np.errstate(invalid='ignore'):
            doydata[ (doydata<-300) | (kopp!=laji) ] = np.nan

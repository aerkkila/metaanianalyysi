#!/usr/bin/python3
import pandas as pd
import xarray as xr
import numpy as np
from matplotlib.pyplot import *
import prf_extent as prf
import talven_ajankohta as taj
import köppen_laatikko_plot as klp

if __name__ == '__main__':
    rcParams.update({'font.size':13,'figure.figsize':(12,10)})
    
    koppdoy,doy = klp.dataframe_luokka_avgdoy('start',palauta_doy=True) #pd.DataFrame,xr.DataArray

    ikirouta = prf.Prf('1x1').rajaa( (doy.lat.min(), doy.lat.max()+1) ) #pitäisi olla 25km, koska tämä vääristää tuloksia
    ikirstr = prf.luokittelu_str(np.mean(ikirouta.data,axis=0)) #np.2Darray

    ikirluokat = prf.luokat
    data = np.empty(len(ikirluokat),object)
    for i,ikirluok in enumerate(ikirluokat):
        a = ikirstr.flatten()==ikirluok
        data[i] = koppdoy.copy().loc[a,:]
    print(data[1])

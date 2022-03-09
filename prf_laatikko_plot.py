#!/usr/bin/python3
import pandas as pd
import numpy as np
from matplotlib.pyplot import *
import warnings
import prf_extent as prf
import talven_ajankohta as taj

if __name__ == '__main__':
    rcParams.update({'font.size':13,'figure.figsize':(12,10)})
    doy = taj.lue_doyt()
    with warnings.catch_warnings():
        warnings.filterwarnings( action='ignore', message='Mean of empty slice' )
        doy = doy.mean(dim='time')
    ikirouta = prf.Prf('1x1').rajaa( (doy.lat.min(), doy.lat.max()+1) ) #pitäisi olla 25km, koska tämä vääristää tuloksia
    ikirstr = prf.luokittelu_str(np.mean(ikirouta.data,axis=0))

    df = pd.DataFrame(columns=prf.luokat)
    for i,laji in enumerate(prf.luokat):
        data = doy.data.copy()
        with np.errstate(invalid='ignore'):
            data[ (data<-300) | (ikirstr!=laji) ] = np.nan
        df[laji] = data.flatten()
    df.boxplot(whis=(5,95))
    show()

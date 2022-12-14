#!/usr/bin/python3
import pandas as pd
import numpy as np
import xarray as xr
from matplotlib.pyplot import *
import warnings,sys
import luokat
import talven_ajankohta as taj

def argumentit():
    global startend, tallenna
    for a in sys.argv:
        if a == '-s':
            tallenna = True
        elif a == 'start' or a == 'end':
            startend = a
    return

if __name__ == '__main__':
    tallenna = False
    startend = 'start'
    argumentit()
    rcParams.update({'font.size':13,'figure.figsize':(10,8)})
    doy = taj.lue_avgdoy(startend)
    ikirluok = xr.open_dataset('prfdata_avg.nc')['luokka'].sel({'lat':slice(doy.lat.min(),doy.lat.max())})

    df = pd.DataFrame(columns=luokat.ikir)
    for i,laji in enumerate(luokat.ikir):
        data = doy.data.copy()
        with np.errstate(invalid='ignore'):
            data[ (data<-300) | (ikirluok!=i) ] = np.nan
        df[laji] = data.flatten()
    with warnings.catch_warnings():
         warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)
         df.drop('non permafrost', axis=1).boxplot(whis=(5,95))
    ylabel('winter %s doy' %startend)
    tight_layout()
    if tallenna:
        savefig('kuvia/%s_%s.png' %(sys.argv[0][:-3],startend))
    else:
        show()

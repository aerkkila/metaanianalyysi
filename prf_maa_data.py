#!/usr/bin/python3
import numpy as np
import pandas as pd
import prf
import talven_ajankohta as taj
import maalajit as ml
import sys

tallenna = False
osuusraja = 30
verbose = False

def argumentit(argv):
    global tallenna,osuusraja,verbose
    i=1
    while i<len(argv):
        a = sys.argv[i]
        if a == '-s':
            tallenna = True
        elif a == '-v':
            verbose = True
        elif a == '-o' or a == '--osuusraja':
            i+=1
            osuusraja = float(sys.argv[i])
        i+=1
    return

def valmista_data(startend):
    turha,maa = ml.lue_maalajit(ml.tunnisteet.keys()) #xr.DataSet (lat,lon)
    maa = ml.maalajien_yhdistamiset(maa,pudota=True)
    maadf = maa.to_dataframe() #index = lat,lon
    
    doy = taj.lue_avgdoy(startend)
    maadf.where( maadf >= osuusraja, np.nan, inplace=True )
    maadf.where( maadf != maadf,     1,      inplace=True )
    if verbose:
        print('\n'+vari1+'Datapisteitä:'+vari0)
        print(maadf.sum(axis='index').astype(int))
    maadf_DOY = maadf.mul( doy.data.flatten(), axis='index' )
    jarj = maadf_DOY.median().to_numpy().argsort() #järjestetään maalajit mediaanin mukaan
    if startend == 'end':
        jarj = jarj[::-1]
    maadf_DOY = maadf_DOY.iloc[:,jarj]
    maadf = maadf.iloc[:,jarj]

    ikirouta = prf.Prf('1x1','xarray').rajaa((doy.lat.min(), doy.lat.max()+1)).data.mean(dim='time')
    ikirstr = prf.luokittelu1_str_xr(ikirouta)

    ml.nimen_jako(maadf_DOY)
    ikirluokat = prf.luokat1
    for i,ikirluok in enumerate(ikirluokat):
        maski = ikirstr.data.flatten()==ikirluok
        maadf_DOY.loc[maski,:].to_csv("prf_maa_DOY_%s%i.csv" %(startend,i))
        maadf.loc[maski,:].to_csv("prf_maa_osuus_%i.csv" %(i))

if __name__ == '__main__':
    argumentit(sys.argv[1:])
    valmista_data('start')
    valmista_data('end')

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
    #tehdään maa_osuus-data
    turha,maa = ml.lue_maalajit(ml.tunnisteet.keys()) #xr.DataSet (lat,lon)
    maa = ml.maalajien_yhdistamiset(maa,pudota=False)
    maadf = maa.to_dataframe() #index = lat,lon
    maadf.where( maadf >= osuusraja, np.nan, inplace=True )
    #tehdään maa_DOY-data
    ikirluokat = prf.luokat
    doy = taj.lue_avgdoy(startend)
    ikirouta = prf.Prf('1x1').rajaa((doy.lat.min(), doy.lat.max()+1)).data.mean(dim='time')
    ikirstr = prf.luokittelu_str_xr(ikirouta)
    maadf_DOY = maadf.where(maadf!=maadf, 1).mul(doy.data.flatten(), axis='index')

    #järjestetään maalajit mediaanin mukaan
    jarj = maadf_DOY.median().to_numpy().argsort()
    if startend == 'end':
        jarj = jarj[::-1]
    maadf_DOY = maadf_DOY.iloc[:,jarj]
    maadf = maadf.iloc[:,jarj]
    #lisätään ft-päivä
    maadf['day'] = doy.data.flatten()*100 # myöhemmin jaetaan sadalla, koska osuudet ovat %

    #tallennetaan
    ikirluokat = prf.luokat
    for i,ikirluok in enumerate(ikirluokat):
        maski = ikirstr.data.flatten()==ikirluok
        maadf_DOY.loc[maski,:].round(6).to_csv("prf_maa_DOY_%s%i.csv" %(startend,i))
        maadf.loc[maski,:].round(6).mul(0.01).to_csv("prf_maa_osuus_%i.csv" %(i))

if __name__ == '__main__':
    argumentit(sys.argv[1:])
    valmista_data('start')
    valmista_data('end')

#!/usr/bin/python3
import pandas as pd
import xarray as xr
import numpy as np
from matplotlib.pyplot import *
import sys, warnings
import prf_extent as prf
import talven_ajankohta as taj
import maalajit as ml

ikir_ind = 0
verbose = False

vari1 = '\033[1;32m'
vari2 = '\033[1;93m'
vari0 = '\033[0m'

def argumentit():
    global tallenna,startend,osuusraja,verbose
    tallenna = False
    startend = 'start'
    osuusraja = 30
    verbose = False
    for i,a in enumerate(sys.argv):
        if a == '-s':
            tallenna = True
        elif a == 'end':
            startend = 'end'
        elif a == '-o' or a == '--osuusraja':
            osuusraja = float(argv[i+1])
        elif a == '-v':
            verbose = True
    return

def viimeistele():
    title(ikirluokat[ikir_ind])
    ax.set_ylim(mmin,mmax)
    ylabel('winter %s doy' %startend)

def vaihda_ikirluokka(hyppy:int,dflista):
    global ikir_ind # myös dflista, ax ja ikirluokat ovat pääfunktiosta
    ikir_ind = ( ikir_ind + len(dflista) + hyppy ) % len(dflista)
    ax.clear()
    with warnings.catch_warnings():
         warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)
         dflista[ikir_ind].boxplot( whis=(5,95), ax=ax )
    viimeistele()
    draw()

def nappainfunk(tapaht):
    if tapaht.key == 'right':
        vaihda_ikirluokka(1,dflista)
    elif tapaht.key == 'left':
        vaihda_ikirluokka(-1,dflista)

if __name__ == '__main__':
    rcParams.update({'font.size':13,'figure.figsize':(10,8)})
    argumentit()
    
    turha,maa = ml.lue_maalajit(ml.tunnisteet.keys()) #xr.DataSet (lat,lon)
    maa = ml.maalajien_yhdistamiset(maa,pudota=True)
    maadf = maa.to_dataframe() #index = lat,lon
    
    with warnings.catch_warnings():
        warnings.filterwarnings( action='ignore', message='Mean of empty slice' )
        doy = taj.lue_doyt(startend).mean(dim='time')
    maadf.where( maadf >= osuusraja, np.nan, inplace=True )
    maadf.where( maadf != maadf,     1,      inplace=True )
    if verbose:
        print('\n'+vari1+'Datapisteitä:'+vari0)
        print(maadf.sum(axis='index').astype(int))
    maadf = maadf.mul( doy.data.flatten(), axis='index' )
    jarj = maadf.median().to_numpy().argsort() #järjestetään maalajit mediaanin mukaan
    if startend == 'end':
        jarj = jarj[::-1]
    maadf = maadf.iloc[:,jarj]

    ikirouta = prf.Prf('1x1','xarray').rajaa( (doy.lat.min(), doy.lat.max()+1) ).data.mean(dim='time')
    ikirstr = prf.luokittelu_str_xr(ikirouta)

    ml.nimen_jako(maadf)
    ikirluokat = prf.luokat[1:] #distinguishing_isolated puuttuu datasta
    dflista = np.empty(len(ikirluokat),object)
    for i,ikirluok in enumerate(ikirluokat):
        maski = ikirstr.data.flatten()==ikirluok
        dflista[i] = maadf.loc[maski,:].reset_index().drop(['lon','lat','wetland'],axis=1)
    mmin = np.inf
    mmax = -np.inf
    for df in dflista:
        mmin = min((min(df.min()),mmin))
        mmax = max((max(df.max()),mmax))
    mmin = np.floor(mmin/10)*10
    mmax = np.ceil(mmax/10)*10
    if verbose:
        print('min/max:',mmin,mmax)
        print('\n'+vari1+'Datapisteitä ikiroutaluokissa:'+vari0,end='')
        for df,luok in zip(dflista,ikirluokat):
            print('\n'+vari2+luok+vari0)
            print(np.isfinite(df).sum())
    fig = figure()
    with warnings.catch_warnings():
         warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)
         ax = dflista[ikir_ind].boxplot( whis=(5,95) )
    viimeistele()
    tight_layout()
    if not tallenna:
        fig.canvas.mpl_connect('key_press_event',nappainfunk)
        show()
        exit()
    while 1:
        savefig('kuvia/%s_%s%i.png' %(sys.argv[0][:-3],startend,ikir_ind))
        if(ikir_ind == len(dflista)-1):
            exit()
        vaihda_ikirluokka(1,dflista)

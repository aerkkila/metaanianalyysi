#!/usr/bin/python3
import pandas as pd
import xarray as xr
import numpy as np
from matplotlib.pyplot import *
import sys, warnings
import prf as prf
import talven_ajankohta as taj
import köppen_laatikko as klaat

tallenna = False
startend = 'start'

def argumentit(argv):
    global ikir_ind,tallenna,startend
    ikir_ind = 0
    for a in argv:
        if a == '-s':
            tallenna = True
        if a == 'start' or a == 'end':
            startend = a

def viimeistele():
    ax.set_ylim(mmin,mmax)
    ylabel('winter %s doy' %startend)
    title(ikirluokat[ikir_ind])

def vaihda_ikirluokka(hyppy:int):
    global ikir_ind # myös data, ax ja ikirluokat ovat pääfunktiosta
    ikir_ind = ( ikir_ind + len(ikirdatalis) + hyppy ) % len(ikirdatalis)
    ax.clear()
    with warnings.catch_warnings():
         warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)
         ikirdatalis[ikir_ind].boxplot( whis=(5,95), ax=ax )
    viimeistele()
    draw()

def nappainfunk(tapaht):
    if tapaht.key == 'right' or tapaht.key == 'o' or tapaht.key == 'i':
        vaihda_ikirluokka(1)
    elif tapaht.key == 'left' or tapaht.key == 'g' or tapaht.key == 'a':
        vaihda_ikirluokka(-1)

def valmista_data():
    koppdoy,doy = klaat.dataframe_luokka_avgdoy(startend,palauta_doy=True) #pd.DataFrame,xr.DataArray
    ikirouta = prf.Prf().rajaa( (doy.lat.min(), doy.lat.max()+1) )
    ikirstr = prf.luokittelu_str_xr(ikirouta.data.mean(dim='time'))
    ikirluokat = prf.luokat
    ikirdatalis = np.empty(len(ikirluokat),object)
    for i,ikirluok in enumerate(ikirluokat):
        a = ikirstr==ikirluok
        ikirdatalis[i] = koppdoy[a.data.flatten()]
    return ikirdatalis,ikirluokat

if __name__ == '__main__':
    rcParams.update({'font.size':13,'figure.figsize':(10,8)})
    argumentit(sys.argv[1:])
    ikirdatalis,ikirluokat = valmista_data()
    mmin = np.inf
    mmax = -np.inf
    for d in ikirdatalis:
        mmin = min( d.min().min(), mmin )
        mmax = max( d.max().max(), mmax )
    mmin = np.floor(mmin/10)*10
    mmax = np.ceil(mmax/10)*10
    fig = figure()
    ax = axes()
    vaihda_ikirluokka(0)
    #ax = ikirdatalis[ikir_ind].boxplot( whis=(5,95) )
    #viimeistele()
    tight_layout()
    if not tallenna:
        fig.canvas.mpl_connect('key_press_event',nappainfunk)
        show()
        exit()
    while 1:
        savefig('kuvia/%s_%s%i.png' %(sys.argv[0][:-3],startend,ikir_ind))
        if(ikir_ind == len(ikirdatalis)-1):
            exit()
        vaihda_ikirluokka(1)

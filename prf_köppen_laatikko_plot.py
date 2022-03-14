#!/usr/bin/python3.9
import pandas as pd
import xarray as xr
import numpy as np
from matplotlib.pyplot import *
import sys
import prf_extent as prf
import talven_ajankohta as taj
import köppen_laatikko_plot as klp

ikir_ind = 0

def vaihda_ikirluokka(hyppy:int):
    global ikir_ind # myös data, ax ja ikirluokat ovat pääfunktiosta
    ikir_ind = ( ikir_ind + len(ikirdatalis) + hyppy ) % len(ikirdatalis)
    ax.clear()
    ikirdatalis[ikir_ind].boxplot( whis=(5,95), ax=ax )
    ax.set_ylim(mmin,mmax)
    title(ikirluokat[ikir_ind])
    draw()

def nappainfunk(tapaht):
    if tapaht.key == 'right':
        vaihda_ikirluokka(1)
    elif tapaht.key == 'left':
        vaihda_ikirluokka(-1)

if __name__ == '__main__':
    rcParams.update({'font.size':13,'figure.figsize':(12,10)})
    tallenna = False
    for a in sys.argv:
        if a == '-s':
            tallenna = True
    
    koppdoy,doy = klp.dataframe_luokka_avgdoy('start',palauta_doy=True) #pd.DataFrame,xr.DataArray

    ikirouta = prf.Prf('1x1','xarray').rajaa( (doy.lat.min(), doy.lat.max()+1) ) #pitäisi olla 25km, koska tämä vääristää tuloksia
    ikirstr = prf.luokittelu_str_xr(ikirouta.data.mean(dim='time'))

    ikirluokat = prf.luokat[1:] #distinguishing_isolated puuttuu datasta
    ikirdatalis = np.empty(len(ikirluokat),object)
    for i,ikirluok in enumerate(ikirluokat):
        a = ikirstr==ikirluok
        ikirdatalis[i] = koppdoy[a.data.flatten()]
    fig = figure()
    ax = ikirdatalis[ikir_ind].boxplot( whis=(5,95) )
    title(ikirluokat[ikir_ind])
    mmin = np.inf
    mmax = -np.inf
    for d in ikirdatalis:
        mmin = min( d.min().min(), mmin )
        mmax = max( d.max().max(), mmax )
    mmin = np.floor(mmin/10)*10
    mmax = np.ceil(mmax/10)*10
    ax.set_ylim(mmin,mmax)
    tight_layout()
    if not tallenna:
        fig.canvas.mpl_connect('key_press_event',nappainfunk)
        show()
        exit()
    while 1:
        savefig('kuvia/prf_köppen_laatikko%i.png' %ikir_ind)
        if(ikir_ind == len(ikirdatalis)-1):
            exit()
        vaihda_ikirluokka(1)

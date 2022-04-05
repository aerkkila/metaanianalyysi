#!/usr/bin/python3
import pandas as pd
import xarray as xr
import numpy as np
from matplotlib.pyplot import *
import sys, warnings, prf, maalajit

ikir_ind = 0
vari1 = '\033[1;32m'
vari2 = '\033[1;93m'
vari0 = '\033[0m'

tallenna = False
startend = 'start'
osuusraja = 30
verbose = False

def argumentit():
    global tallenna,startend,osuusraja,verbose
    i=1
    while i<len(sys.argv):
        a = sys.argv[i]
        if a == '-s':
            tallenna = True
        elif a == 'end':
            startend = 'end'
        elif a == '-v':
            verbose = True
        elif a == '-o' or a == '--osuusraja':
            i+=1
            osuusraja = float(sys.argv[i])
        i+=1
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
    return

def min_ja_max():
    global mmin,mmax
    mmin = np.inf
    mmax = -np.inf
    for df in dflista:
        mmin = min((min(df.drop(['lat','lon'],axis=1).min()),mmin))
        mmax = max((max(df.drop(['lat','lon'],axis=1).max()),mmax))
    mmin = np.floor(mmin/10)*10
    mmax = np.ceil(mmax/10)*10

if __name__ == '__main__':
    rcParams.update({'font.size':13,'figure.figsize':(10,8)})
    argumentit()

    ikirluokat = prf.luokat1
    dflista = np.full(len(ikirluokat),None,object)
    for i in range(dflista.shape[0]):
        dflista[i] = maalajit.nimen_jako(pd.read_csv('prf_maa_DOY_%s%i.csv' %(startend,i)))
        
    min_ja_max()
    
    for l in dflista:
        l.drop(['lat','lon'],axis=1,inplace=True)
    
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

#!/usr/bin/python3
import pandas as pd
import xarray as xr
import numpy as np
from matplotlib.pyplot import *
import sys, warnings
from valitse_painottaen import valitse_painottaen
from multiprocessing import Process

bawlajit = ['boreal_forest', 'lake', 'bog+fen', #'tundra_wetland',
            'permafrost_bog', 'tundra_dry', 'wetland']
alm = ['talven_alku', 'talven_loppu']
aln = ['start', 'end']
osuusraja = 0.3
kerroin = 8

def kuva(alind,ftnum):
    kausidata = xr.open_dataset("kausien_pituudet%i.nc" %ftnum)
    indeksit = valitse_painottaen(kausidata.lat.data, kausidata.lon.data, kerroin)
    df = pd.DataFrame(columns=bawlajit)
    resol = baw.bog.data.flatten().size
    vuosia = len(kausidata.vuosi)
    for i,laji in enumerate(bawlajit):
        flat_maa = baw[laji].data.flatten()
        maski = flat_maa < osuusraja
        data = np.empty(resol*vuosia*kerroin)
        for v in range(vuosia):
            paivat = kausidata[alm[alind]].data[v,...].flatten()
            paivat[maski] = np.nan
            data[v*resol*kerroin: (v+1)*resol*kerroin] = paivat[indeksit]
        df[laji] = data
    kausidata.close()
    jarj = df.median().to_numpy().argsort() #järjestetään bawld-lajit mediaanin mukaan
    if alind:
        jarj = jarj[::-1]
    df = df.iloc[:,jarj]
    #joka toinen sarake alemmalle riville
    for i,c in enumerate(df.columns):
        if i%2:
            df.rename(columns={c: '\n'+c}, inplace=True)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)
        df.boxplot(whis=(5,95), widths=0.7)
    xticks(rotation=0)
    ylabel('winter %s, data %i' %(aln[alind],ftnum))
    if(alind==0): #talven alku
        ylim([-135,100])
    else: # talven loppu
        ylim([-50,220])
    tight_layout()
    if('-s' in sys.argv):
        savefig('kuvia/yksittäiset/vanha_bawld_laatikko_w%s_ft%i.png' %(aln[alind],ftnum))
        clf()
    else:
        show()

def aja(ftnum):
    for alind in range(2):
        kuva(alind,ftnum)

def main():
    global baw
    rcParams.update({'figure.figsize':(8,11), 'font.size':16})
    baw = xr.open_dataset("BAWLD1x1.nc")
    pros = np.empty(3,object)
    for i in range(3):
        pros[i] = Process(target=aja, args=[i])
        pros[i].start()
    for p in pros:
        p.join()

if __name__=='__main__':
    main()

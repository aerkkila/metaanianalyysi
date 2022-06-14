#!/usr/bin/python3
import pandas as pd
import xarray as xr
import numpy as np
from matplotlib.pyplot import *
import sys, warnings
from valitse_painottaen import valitse_painottaen

bawlajit = ['boreal_forest', 'lake', 'bog+fen', #'tundra_wetland',
            'permafrost_bog', 'tundra_dry', 'wetland']
al = ['talven_alku', 'talven_loppu']
osuusraja = 0.3
alind = 0
ftdataind = 0

def kuva(baw):
    pitdet = xr.open_dataset("kausien_pituudet%i.nc" %ftdataind)
    indeksit = valitse_painottaen(pitdet.lat.data, pitdet.lon.data, 8)
    df = pd.DataFrame(columns=bawlajit)
    for i,laji in enumerate(bawlajit):
        flat_maa = baw[laji].data.flatten()
        maski = flat_maa < osuusraja
        data = np.empty(len(flat_maa)*len(pitdet.vuosi))
        for v in range(len(pitdet.vuosi)):
            data1 = pitdet[al[alind]].data[v,...].flatten()
            data1[maski] = np.nan
            data[ v*len(flat_maa) : (v+1)*len(flat_maa) ] = data1
        df[laji] = data[np.repeat(indeksit,len(pitdet.vuosi))]
    pitdet.close()
    jarj = df.median().to_numpy().argsort() #järjestetään bawld-lajit mediaanin mukaan
    if alind:
        jarj = jarj[::-1]
    df = df.iloc[:,jarj]
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)
        df.boxplot(whis=(5,95))
    xticks(rotation=0)
    s_e = ['start','end'][alind]
    ylabel('winter %s day' %(s_e))
    if(alind==0):
        ylim([-135,175])
    else:
        ylim([-90,220])
    tight_layout()
    if('-s' in sys.argv):
        savefig('kuvia/BAWLD_laatikko_%s%i.png' %(s_e,ftdataind))
        clf()
    else:
        show()

def main():
    global alind, ftdataind
    rcParams.update({'figure.figsize':(13,11), 'font.size':14})
    baw = xr.open_dataset("BAWLD1x1.nc")
    for alind in range(2):
        for ftdataind in range(3):
            kuva(baw)

if __name__=='__main__':
    main()

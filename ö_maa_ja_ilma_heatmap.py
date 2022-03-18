#!/usr/bin/python3
from matplotlib.pyplot import *
import numpy as np
import xarray as xr
import pandas as pd
import maalajit as ml
import maalajit_plot as pml
import köppen_laatikko_plot as pkl
import seaborn as sns

if __name__ == '__main__':
    args = pkl.argumentit()
    args.luokat = 'CDE'
    args.keski_pois = 1
    kopp = pkl.lue_luokitus('köppen1x1.nc')
    ilmluokat = np.unique(kopp)
    ilmluokat = ilmluokat[ilmluokat!='']

    args = pml.argumentit()
    turha,maa = ml.lue_maalajit(args.maalajit,False,True)
    maa = ml.maalajien_yhdistamiset( maa, pudota=True )
    dt = np.empty( [len(ilmluokat),len(maa.keys())], int )
    for j,ilml in enumerate(ilmluokat):
        for i,mlaji in enumerate(maa.keys()):
            dt[j,i] = np.sum( (kopp==ilml) & (maa[mlaji].data.flatten()>30) )
    df = pd.DataFrame( data=dt, columns=maa.keys(), index=ilmluokat, dtype=int )
    pml.nimen_jako(df)
    sns.heatmap( df.transpose(), center=0, cmap='seismic', square=True, annot=True, fmt='d', annot_kws={'fontsize':10} )
    tight_layout()
    if args.tallenna:
        savefig('maa_ja_ilma.png')
    else:
        show()

#!/usr/bin/python3
import numpy as np
import xarray as xr
import pandas as pd
import seaborn as sns
from matplotlib.pyplot import *
import matplotlib
import os, re
from scipy.interpolate import interp2d
from argparse import ArgumentParser
import maalajit as ml
from talven_ajankohta import lue_doyt

def argumentit():
    pars = ArgumentParser()
    pars.add_argument( 'startend', nargs='?', default='end' )
    pars.add_argument( '-t', '--toiminto', default='pisteet', help='Jokin tässä määritellyistä funktioista.' )
    pars.add_argument( '-m', '--maalaji', default='', help='Ota vain kyseinen maalaji. Kumoaa argumentin -A/--kaikki.' )
    pars.add_argument( '-A', '--kaikki', nargs='?', type=int, const=1, default=0, help='Ilman tätä otetaan vain osa maalajeista.' )
    pars.add_argument( '-s', '--tallenna', nargs='?', type=int, const=1, default=0 )
    pars.add_argument( '-r', '--osuusraja', type=int, default=30 )
    args = pars.parse_args()
    if(args.maalaji):
        args.maalajit = [args.maalaji] #vain yksi
    elif not args.kaikki:
        args.maalajit = list(ml.tunnisteet.keys()) #rajattu joukko
    else:
        args.maalajit = list(ml.tunnisteet_kaikki.keys()) #kaikki
    return args

def pisteet(args):
    doy = lue_doyt(args.startend)
    turha,maa = ml.lue_maalajit(args.maalajit,False,True)
    maa = ml.maalajien_yhdistamiset(maa, pudota=True)
    for i,maalaji in enumerate(maa.keys()):
        sys.stdout.write('\r%i/%i\t%s\033[0K ' %(i+1,len(maa.keys()),maalaji))
        maski0 = maa[maalaji].data.flatten() > 0.5
        for vuosi in doy.time:
            doy1 = doy.loc[vuosi,:,:].data.flatten()
            with np.errstate(invalid='ignore'):
                maski = maski0 & (doy1 > -300)
            plot( maa[maalaji].data.flatten()[maski], doy1[maski], '.', color='b' )
            xlabel(f'{maalaji} (%)')
            ylabel(f'winter {args.startend} doy')
            tight_layout()
        if(args.tallenna):
            savefig(f'BAWLD_DOY_{args.startend}_{maalaji}.png')
            clf()
        else:
            show()
    sys.stdout.write('\r\033[0K')

def korrelaatiot(args):
    mlajit = ['wetland', 'bog', 'fen', 'marsh', 'permafrost_bog', 'tundra_wetland']#, 'boreal_forest', 'tundra_dry']
    alkup,muunn = ml.lue_maalajit(mlajit,True,True)
    muunn_map = muunn.to_dataframe().corr()
    '''
    alkup_map = alkup.to_dataframe().corr()
    for j in range(len(muunn_map)):
        for i in range(len(muunn_map)):
            if i > j:
                muunn_map.iloc[j,i] = alkup_map.iloc[j,i]
    '''
    sns.heatmap( muunn_map, center=0, cmap='seismic', square=True, annot=True, annot_kws={'fontsize':10} )
    xticks(rotation=30, ha='right')
    tight_layout()
    if(args.tallenna):
        savefig('BAWLD_korrelaatiot.png')
        clf()
    else:
        show()

if __name__ == '__main__':
    args = argumentit()
    rcParams.update({'font.size': 17,
                     'figure.figsize': (14,10)})
    eval( args.toiminto + '(args)' )

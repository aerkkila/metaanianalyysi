#!/usr/bin/python3
import numpy as np
import pandas as pd
from matplotlib.pyplot import *
import sys

def piirra(df, luku):
    suo = suot[suoind]
    taul_osuus = df[suo] / wetl
    jarj = np.argsort(taul_osuus)
    x = taul_osuus[jarj]
    y = df.vuo[jarj]
    yhattu = taul_raja[jarj]
    plot(x,y,color='k')
    maski = (y<=yhattu)
    plot(x[maski], yhattu[maski], '.', color='b')
    plot(x[~maski], yhattu[~maski], '.', color='r')

def main():
    rcParams.update({'figure.figsize':(14,10), 'font.size':14})
    d = np.load('./wetlandvuo_randomforest.npz')
    df = pd.read_csv('./wetlandvuo_randomforest_data.csv',index_col=0)
    wetl = np.array(df.drop('vuo',axis=1).sum(axis=1))
    #järjestetään suotyypin osuuden mukaan
    suot = df.drop('vuo',axis=1).columns
    raja = 50
    ajo = 0 # on monta ajoa eri satunnaisluvuilla
    rindex = np.where(d['rajat']==raja)[0][0]
    taul_raja = d['rajat_hattu'][ajo,rindex,:]
    for i,suo in enumerate(suot):
        taul_osuus = df[suo] / wetl
        jarj = np.argsort(taul_osuus)
        x = np.array(taul_osuus[jarj])
        y = np.array(df.vuo[jarj]) / wetl
        yhattu = taul_raja[jarj]
        plot(x,y,'.',color='k')
        maski = (y<=yhattu)
        plot(x[maski], yhattu[maski], '.', color='b')
        plot(x[~maski], yhattu[~maski], '.', color='r')
        xlabel('frac(%s)' %suo)
        ylabel('CH$_4$ (nmol/m$^2$/s$^2$)')
        tight_layout()
        show()
    return 0

if __name__ == '__main__':
    sys.exit(main())

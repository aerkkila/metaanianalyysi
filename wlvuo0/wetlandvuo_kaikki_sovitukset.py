#!/usr/bin/python3
import pandas as pd
import numpy as np
from wetlandvuo_data import tee_data, kaudet
from matplotlib.pyplot import *
import sys

class Yhtalo():
    def __init__(self, df, t_ind):
        self.df = df
        self.i = t_ind
    def __call__(self, nselitt, rajaus, mk=''):
        indeksi = "%s_%isel.%s" %(rajaus, nselitt, '_'+mk if len(mk) else '') #rajaus on 'kaikki' tai 'rajattu'
        if nselitt == 1:
            return lambda x: self.df.loc[indeksi,'a0'] + self.df.loc[indeksi,'a1']*x[:,self.i]
        return lambda x: self.df.loc[indeksi,'a0'] + self.df.loc[indeksi,'a1']*x[:,self.i] + self.df.loc[indeksi,'a2']*x[:,-1]

def aja(k_ind):
    dt = tee_data(kaudet[k_ind])
    dtx = dt[0]
    dty = dt[1]
    wnimet = dt[2][:-1]
    #lat = dt[3]
    #kauden_pituus = dt[4]
    for i in range(len(wnimet)):
        yht = Yhtalo(pd.read_csv("./wetlandvuo_tulos/parametrit_%s_%s.csv" %(kaudet[k_ind], wnimet[i]), index_col=0), i)
        maski = dtx[:,i]>=0.03
        ax = subplot(221)
        plot(dtx[:,i][maski], dty[maski], '.')
        plot(dtx[:,i], yht(2, 'kaikki', '')(dtx), '.', label='prediction')
        plot(dtx[:,i], yht(2, 'kaikki', 'm')(dtx), '.', label='low prediction')
        plot(dtx[:,i], yht(2, 'kaikki', 'k')(dtx), '.', label='high prediction')
        title("%s %s 2 kaikki" %(kaudet[k_ind], wnimet[i]))
        ax = subplot(222)
        plot(dtx[:,i][maski], dty[maski], '.')
        plot(dtx[:,i], yht(2, 'rajattu', '')(dtx), '.', label='prediction')
        plot(dtx[:,i], yht(2, 'rajattu', 'm')(dtx), '.', label='low prediction')
        plot(dtx[:,i], yht(2, 'rajattu', 'k')(dtx), '.', label='high prediction')
        title("%s %s 2 rajattu" %(kaudet[k_ind], wnimet[i]))
        ax = subplot(223)
        plot(dtx[:,i][maski], dty[maski], '.')
        plot(dtx[:,i], yht(1, 'kaikki', '')(dtx), '.', label='prediction')
        plot(dtx[:,i], yht(1, 'kaikki', 'm')(dtx), '.', label='low prediction')
        plot(dtx[:,i], yht(1, 'kaikki', 'k')(dtx), '.', label='high prediction')
        title("%s %s 1 kaikki" %(kaudet[k_ind], wnimet[i]))
        ax = subplot(224)
        plot(dtx[:,i][maski], dty[maski], '.')
        plot(dtx[:,i], yht(1, 'rajattu', '')(dtx), '.', label='prediction')
        plot(dtx[:,i], yht(1, 'rajattu', 'm')(dtx), '.', label='low prediction')
        plot(dtx[:,i], yht(1, 'rajattu', 'k')(dtx), '.', label='high prediction')
        title("%s %s 1 rajattu" %(kaudet[k_ind], wnimet[i]))
        legend(loc='upper right')
        tight_layout()
        savefig("./kuvia/wetlandvuo_kaikki_sovitukset/%s_%s.png" %(kaudet[k_ind], wnimet[i]))
        clf()

def main():
    rcParams.update({'figure.figsize':(12,10)})
    for i in range(len(kaudet)):
        aja(i)
    return

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

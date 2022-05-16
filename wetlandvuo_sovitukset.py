#!/usr/bin/python3
import pandas as pd
import numpy as np
from wetlandvuo_data import tee_data, kaudet
from matplotlib.pyplot import *
import sys

class Yhtalo():
    def __init__(self, df, w_ind):
        self.df = df
        self.i = w_ind
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
    for i in range(len(wnimet)):
        yht = Yhtalo(pd.read_csv("./wetlandvuo_tulos/parametrit_%s_%s.csv" %(kaudet[k_ind], wnimet[i]), index_col=0), i)
        maski = dtx[:,i]>=0.03
        ax = subplot(2,3,1+i)
        plot(dtx[:,i], dty, '.', label='data')
        plot(dtx[:,i], yht(2, 'kaikki', '')(dtx), '.', markersize=4, label='prediction')
        plot(dtx[:,i], yht(2, 'kaikki', 'm')(dtx), '.', markersize=4, label='low prediction')
        plot(dtx[:,i], yht(2, 'kaikki', 'k')(dtx), '.', markersize=4, label='high prediction')
        xlabel((wnimet[i]))
        ylabel('CH$_4$ flux')
        legend(loc='upper left')
    suptitle(kaudet[k_ind])
    tight_layout()
    savefig("./kuvia/wetlandvuo_%s.png" %(kaudet[k_ind]))
    clf()

def main():
    rcParams.update({'figure.figsize':(13,10)})
    for i in range(len(kaudet)):
        aja(i)
    return

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

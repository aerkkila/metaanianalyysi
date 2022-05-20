#!/usr/bin/python3
import pandas as pd
import numpy as np
from wetlandvuo_data import tee_data, kaudet
from matplotlib.pyplot import *
import sys
 
class Yhtalo():
    def __init__(self, df, w_ind, x1_ind, onkoprf):
        self.df = df
        self.i = w_ind
        self.x1_ind = x1_ind
        self.onkoprf = onkoprf
    def __call__(self, pmk=0):
        ind = len(self.df.index)//3 * pmk + self.i
        if not self.onkoprf:
            return lambda x: self.df.iloc[ind,0] + self.df.iloc[ind,1]*x[:,self.x1_ind] + self.df.iloc[ind,2]*x[:,-1]
        return lambda x: (self.df.iloc[ind,0] + self.df.iloc[ind,1]*x[:,self.x1_ind] + self.df.iloc[ind,2]*x[:,-2] +
                          self.df.iloc[ind,3]*x[:,-1])

def aja(k_ind):
    dt = tee_data(kaudet[k_ind])
    dtx = dt[0]
    dty = dt[1]
    wnimet = dt[2][:-1]
    if onkoprf:
        yht = Yhtalo(pd.read_csv("./wetlandvuo_tulos/prf_parametrit_%s.csv" %(kaudet[k_ind]), index_col=0), 0, 0, onkoprf)
    else:
        yht = Yhtalo(pd.read_csv("./wetlandvuo_tulos/parametrit_%s.csv" %(kaudet[k_ind]), index_col=0), 0, 0, onkoprf)
    for w in range(len(wnimet)):
        yht.x1_ind = w
        yht.i = w
        ax = subplot(2,3,1+w)
        plot(dtx[:,w], dty, '.', label='data')
        plot(dtx[:,w], yht(0)(dtx), '.', markersize=4, label='prediction')
        plot(dtx[:,w], yht(1)(dtx), '.', markersize=4, label='low prediction')
        plot(dtx[:,w], yht(2)(dtx), '.', markersize=4, label='high prediction')
        xlabel((wnimet[w]))
        ylabel('CH$_4$ flux')
        legend(loc='upper left')
    suptitle(kaudet[k_ind])
    tight_layout()
    #savefig("./kuvia/wetlandvuo_%s.png" %(kaudet[k_ind]))
    show()
    clf()

def tasokuvaajat(k_ind):
    dt = tee_data(kaudet[k_ind])
    dtx = dt[0]
    dty = dt[1]
    wnimet = dt[2][:-1]
    vanhat = np.seterr(invalid='ignore')
    df = pd.read_csv("./wetlandvuo_tulos/parametrit_%s.csv" %(kaudet[k_ind]), index_col=0)
    yht = Yhtalo(df, 0, 0)
    skoko = 512
    piste = 3
    tmp = np.arange(skoko)/skoko
    mx,my = np.meshgrid(tmp,tmp)
    sovit_x = np.concatenate([my.flatten(),mx.flatten()]).reshape([mx.size,2], order='F')
    for w,wnimi in enumerate(wnimet[:-1]):
        yht.i = w
        subplot(2,3,w+1)
        cgrid = yht(0)(sovit_x)
        cgrid = cgrid.reshape([skoko,skoko])
        for k in range(len(dty)):
            xy = int(dtx[k,-1]*skoko)
            xx = int(dtx[k,w]*skoko)
            cgrid[xy:xy+piste, xx:xx+piste] = dty[k]
        pcolormesh(mx,my,cgrid, cmap=get_cmap('gnuplot2_r'))
        gca().set_aspect('equal')
        colorbar()
    tight_layout()
    show()
    #clf()
    np.seterr(**vanhat)

def main():
    global onkoprf
    rcParams.update({'figure.figsize':(13,10)})
    onkoprf = '-prf' in sys.argv
    for i in range(len(kaudet)):
        aja(i)
        #tasokuvaajat(i)
    return 

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

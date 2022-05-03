#!/usr/bin/python3
from sklearn import linear_model
import numpy as np
from voting_model import Voting
import wetlandvuo_data as wldata
import multiprocessing as mp
from wetlandvuo_voting import pintaalat1x1, pintaalan_painotus
import sys

def yksi_tyyppi(ind, nimi):
    malli = Voting(linear_model.LinearRegression(), 'numpy', n_estimators=10000)
    datax = np.concatenate((datax0[:,[ind]], wetl), axis=1)
    malli.fit(datax, datay, samp_kwargs={'n':10, 'limits':painotus})
    enn_y = malli.predict(enn_x)
    enn_yL = malli.prediction(11)
    enn_yH = malli.prediction(89)
    print("%14s:\t%.3f\t%.3f\t%.3f" %(nimi, enn_yL, enn_y, enn_yH))

def main():
    global enn_x, datax0, datay, wetl, painotus
    njobs=1
    if '-j' in sys.argv:
        njobs = int(sys.argv[sys.argv.index('-j')+1])
    dt = wldata.tee_data('numpy')
    datax = dt[0]
    datay = dt[1]
    nimet = dt[2]
    lat = dt[3]
    
    alat = pintaalat1x1(lat)
    painotus = pintaalan_painotus(lat)
    wetl = np.array([np.sum(datax, axis=1),]).transpose()
    datax0 = datax.copy()

    enn_x = np.array([1.0,1.0]).reshape([1,2])
    prosessit = np.empty(njobs,object)
    print("%14s \t%d %%\t avg\t%d %%" %("", 11, 89))

    for i,nimi in enumerate(nimet):
        if(i<njobs-1):
            prosessit[i] = mp.Process(target=yksi_tyyppi, args=(i,nimi))
            prosessit[i].start()
        else:
            yksi_tyyppi(i,nimi)
    for i in range(njobs-1):
        prosessit[i].join()

    return 0

if __name__=='__main__':
    main()

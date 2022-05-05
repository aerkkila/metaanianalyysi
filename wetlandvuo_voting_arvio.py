#!/usr/bin/python3
from sklearn import linear_model
import numpy as np
from voting_model import Voting
import wetlandvuo_data as wldata
import multiprocessing as mp
from wetlandvuo_voting import pintaalat1x1, pintaalan_painotus
import sys

def yksi_tyyppi(ind, nimi):
    global datax
    pohjamalli = linear_model.LinearRegression()
    malli = Voting(pohjamalli, 'numpy', n_estimators=10000)
    maski = datax[:,ind] >= 0.03
    dtx = datax[:,[ind,-1]]
    malli.fit(dtx[maski], datay[maski], samp_kwargs={'n':10, 'limits':painotus[maski]})
    enn_yvot = malli.predict(enn_x)
    enn_y = pohjamalli.fit(dtx[maski],datay[maski]).predict(enn_x)
    enn_yL = malli.prediction(10)
    enn_yH = malli.prediction(90)
    print("%14s:\t%.3f\t%.3f\t%.3f\t%.3f" %(nimi, enn_yL, enn_y, enn_yvot, enn_yH))

def main():
    global enn_x, datax, datay, wetl, painotus
    njobs=1
    if '-j' in sys.argv:
        njobs = int(sys.argv[sys.argv.index('-j')+1])
    dt = wldata.tee_data()
    datax = dt[0]
    datay = dt[1]
    nimet = dt[2][:-1]
    lat = dt[3]
    
    alat = pintaalat1x1(lat)
    painotus = pintaalan_painotus(lat)

    enn_x = np.array([1.0,1.0]).reshape([1,2])
    prosessit = np.empty(njobs,object)
    print("%14s \t%d %%\t avg\tjoukkio\t%d %%" %("", 10, 90))

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
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

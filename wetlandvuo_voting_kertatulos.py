#!/usr/bin/python3
from wetlandvuo_data import tee_data
import sklearn.linear_model as lm
import numpy as np
import sys,time
from voting_model import Voting
import wetlandvuo_voting as wv

def main():
    dt = tee_data('numpy')
    datax = dt[0]
    datay = dt[1]
    nimet = dt[2]
    lat = dt[3]
    wetl = np.sum(datax,axis=1).reshape([datax.shape[0],1])
    datax = np.concatenate([datax,wetl], axis=1)
    rajat = wv.pintaalan_painotus(wv.pintaalat1x1(lat))

    prpist = np.arange(1,100)
    yhat = np.empty([len(nimet),len(datay)], np.float32)
    yhat_voting = np.empty_like(yhat)
    yhat_raja = np.empty([len(nimet),len(prpist),len(datay)], np.float32)

    #ajat: sovitus = 16,9, +predict = 19,9, +prediction = 26,8
    pohjamalli = lm.LinearRegression()
    malli = Voting(pohjamalli, n_estimators=10000)
    alku = time.process_time()
    for i,nimi in enumerate(nimet):
        x = datax[:,[i,-1]]
        malli.fit(x,datay, samp_kwargs={'n':10, 'limits':rajat})
        yhat_voting[i,...] = malli.predict(x)
        yhat_raja[i,...] = malli.prediction(prpist)
        yhat[i,...] = pohjamalli.fit(x,datay).predict(x)

    print("aika = %.3f" %(time.process_time()-alku))
    np.savez('wetlandvuo_kertatulos.npz', x=datax, y=datay, yhat=yhat, yhat_voting=yhat_voting, yhat_raja=yhat_raja, rajat=prpist)
    return 0

if __name__=='__main__':
    main()

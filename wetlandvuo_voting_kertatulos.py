#!/usr/bin/python3
from wetlandvuo_data import tee_data
import sklearn.linear_model as lm
import numpy as np
import sys
from voting_model import Voting
import wetlandvuo_voting as wv

def main():
    if '-f' in sys.argv:
        dt = tee_data(pakota=True)
    else:
        dt = tee_data()
    datax = dt[0]
    datay = dt[1]
    nimet = dt[2]
    lat = dt[3]
    rajat = wv.pintaalan_painotus(wv.pintaalat1x1(lat))

    prpist = np.arange(1,100)
    yhat = np.empty([len(nimet),len(datay)], np.float32)
    yhat_voting = np.empty_like(yhat)
    yhat_raja = np.empty([len(nimet),len(prpist),len(datay)], np.float32)

    #ajat: sovitus = 16,9, +predict = 19,9, +prediction = 26,8
    pohjamalli = lm.LinearRegression()
    malli = Voting(pohjamalli, n_estimators=10000)
    raja_tyyppi = 0.03
    for i,nimi in enumerate(nimet[:-1]):
        print('\r%i/%i' %(i+1,len(nimet)-1), end='')
        sys.stdout.flush()
        x = datax[:,[i,-1]]
        maski = x[:,0] >= raja_tyyppi
        malli.fit(x[maski],datay[maski], samp_kwargs={'n':10, 'limits':rajat[maski]})
        yhat_voting[i,...] = malli.predict(x)
        yhat_raja[i,...] = malli.prediction(prpist)
        yhat[i,...] = pohjamalli.fit(x,datay).predict(x)
    print('\r\033[K', end='')
    np.savez('%s.npz' %(sys.argv[0][:-3]), x=datax, y=datay, yhat=yhat, yhat_voting=yhat_voting, yhat_raja=yhat_raja, rajat=prpist)
    return 0

if __name__=='__main__':
    main()

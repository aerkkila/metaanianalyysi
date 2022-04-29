#!/usr/bin/python3
from sklearn import linear_model
import numpy as np
from voting_model import Voting
import wetlandvuo_data as wldata
import time

def taita_sarja(x, y, n_taitteet, n_sij):
    pit = len(y) // n_taitteet
    if(n_sij != n_taitteet-1):
        validx = x[pit*n_sij : pit*(n_sij+1), ...]
        validy = y[pit*n_sij : pit*(n_sij+1), ...]
        harjx = np.concatenate((x[:pit*n_sij, ...], x[pit*(n_sij+1):]))
        harjy = np.concatenate((y[:pit*n_sij, ...], y[pit*(n_sij+1):]))
    else:
        validx = x[pit*n_sij:]
        validy = y[pit*n_sij:]
        harjx = x[:pit*n_sij]
        harjy = y[:pit*n_sij]
    return harjx, harjy, validx, validy

def ristivalidointidata(x, y, malli, n_taitteet, ennusrajat=()):
    if(n_taitteet > len(y)):
        print("Varoitus n_taitteet (%i) > len(df) (%i). n_taitteet muutetaan kokoon len(df)" %(n_taitteet,len(df.index())))
        n_taitteet = len(y)
    yhatut = np.empty(len(y))
    ennushatut = np.empty([len(y), len(ennusrajat)])
    print('')
    ind = 0
    alku = time.process_time()
    for ind_taite in range(n_taitteet):
        harjx,harjy,validx,validy = taita_sarja(x, y, n_taitteet, ind_taite)
        malli.fit(harjx, harjy)
        ind1 = ind+len(validy)
        yhatut[ind:ind1] = malli.predict(validx)
        for i,e in enumerate(ennusrajat):
            ennushatut[ind:ind1,i] = malli.prediction(e)
        print("\033[F%i/%i\033[K" %(ind_taite+1,n_taitteet))
    print("\033[F\033[K", end='')
    return yhatut, ennushatut, time.process_time()-alku

def main():
    np.random.seed(12345)
    tyyppi = 'numpy'
    dt = wldata.tee_data(tyyppi)
    if tyyppi == 'pandas':
        datax = dt.drop('vuo', axis=1)
        datay = dt.vuo
    elif tyyppi == 'numpy':
        datax = dt[0]
        datay = dt[1]
        nimet = dt[2]

    #datax = np.array([np.sum(datax, axis=1),]).transpose() #vain wetland

    vm = Voting(linear_model.LinearRegression(), tyyppi, n_estimators=500, samp_kwargs={'n':100})
    ennusrajat = (5,20,50,80,95)
    yhatut, ehatut, aika = ristivalidointidata(datax, datay, vm, 8, ennusrajat)
    print('aika = %.4f s' %aika)
    varlin = np.mean((yhatut-np.mean(datay))**2)
    var = np.var(datay)
    print("selitetty osuus = %.4f\n"
          "alkup. varianssi = %.4f" %(1-varlin/var,var))
    return 0

if __name__=='__main__':
    main()

#!/usr/bin/python3
from sklearn import *
import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
from wetlandvuo_data import tee_data
import wetlandtyypin_pisteet_tulos as wpt
import config, time, sys

def taita_sarja(lista, n_taitteet, n_sij):
    pit = len(lista[1]) // n_taitteet
    harj = np.empty(len(lista),object)
    valid = np.empty(len(lista),object)
    if(n_sij < n_taitteet-1):
        for i in range(len(lista)):
            valid[i] = lista[i][pit*n_sij : pit*(n_sij+1), ...]
            harj[i] = np.concatenate((lista[i][:pit*n_sij, ...], lista[i][pit*(n_sij+1):]))
    else:
        for i in range(len(lista)):
            valid[i] = lista[i][pit*n_sij:]
            harj[i] = lista[i][:pit*n_sij]
    return harj, valid

def ristivalidoi(datax, datay, malli, n_yht):
    neliosumma = 0
    alku = time.process_time()
    for i in range(n_yht):
        print('\r%i/%i\033[K' %(i+1,n_yht), end='')
        sys.stdout.flush()
        harj,valid = taita_sarja([datax,datay], n_yht, i)
        malli.fit(harj[0], harj[1])
        yhattu = malli.predict(valid[0])
        neliosumma += np.sum((yhattu-valid[1])**2)
    print('')
    return neliosumma, time.process_time()-alku

class Dummy():
    def fit(self,x,y):
        self.v = y.mean()
        return self
    def predict(self,x):
        return [self.v]*len(x)

def main():
    plt.rcParams.update({'figure.figsize':(14,12)})
    if '-f' in sys.argv:
        dt = tee_data(pakota=True)
    else:
        dt = tee_data()
    datax = dt[0]
    datay = dt[1]
    nimet = dt[2]
    mnimet = ['dummy','ols','ridge','SVR']
    mallit = [
        Dummy(),
        linear_model.LinearRegression(fit_intercept=True),
        linear_model.Ridge(fit_intercept=True, alpha=1),
        svm.SVR(kernel='linear',cache_size=4000, **{'C': 2070, 'epsilon': 1.224, 'gamma': 5.5540816326530615})
    ]

    maskit = wpt.tee_maskit(datax,nimet)
    yhtalot = wpt.Yhtalot()

    #kuvaaja valituista pisteistä ja yhtälöstä
    if 0:
        for i in range(len(nimet[:-1])):
            plt.plot(datax[:,i], yhtalot(i)(datax[:,i]))
            plt.plot(datax[:,i], datax[:,-1], '.')
            plt.plot(datax[maskit[i,:],i], datax[maskit[i,:],-1], '.')
            plt.show()

    #ennusteet yhden luokan voista
    x = np.array([[1,1],[0,0],[0,1],[1,0]])
    #x = np.array([[1],[0]])
    taulukko = pd.DataFrame(0,
                            index = mnimet,
                            columns = nimet[:-1])
    for m,mnimi in enumerate(mnimet):
        malli = mallit[m]
        for i,nimi in enumerate(nimet[:-1]):
            malli.fit(datax[maskit[i,:]][:,[i,-1]], datay[maskit[i,:]])
            taulukko.iloc[m,i] = malli.predict(x)[0]
    print(taulukko)

    #luotettavuuden ristivalidointi
    if 0:
        taulukko = pd.DataFrame(0,
                                index = mnimet,
                                columns = ['std','R2','aika'])
        nsum_data = np.sum((datay-np.mean(datay))**2)
        for mnimi,malli in zip(taulukko.index,mallit):
            nsum_sovit,aika = ristivalidoi(datax, datay, malli, 16)
            taulukko.loc[mnimi,:] = [np.sqrt(nsum_sovit/len(datay)), 1-nsum_sovit/nsum_data, aika]
        print(taulukko)

    #kuvaaja sovitetuista suorista
    for n,nimi in enumerate(nimet[:-1]):
        x = datax[maskit[n,:]][:,[nimet.index(nimi)]]
        y = datay[maskit[n,:]]
        plt.clf()
        plt.plot(x[:,0], y, '.')
        plt.waitforbuttonpress()
        viivat, = plt.plot(x[:,0], y, '.') #tähän ydataksi vaihdetaan sovitus
        for mnimi in mnimet:
            malli = mallit[mnimet.index(mnimi)].fit(x,y)
            viivat.set_ydata(malli.predict(x))
            plt.title("%s, %s" %(nimi,mnimi))
            plt.waitforbuttonpress()

if __name__ == '__main__':
    if 'svr' in sys.argv:
        exit(main_tutki_svr())
    else:
        exit(main())

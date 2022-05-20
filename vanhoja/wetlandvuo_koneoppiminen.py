#!/usr/bin/python3
from sklearn import *
import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
from wetlandvuo_data import tee_data
import wetlandtyypin_pisteet_tulos as wpt
import config, time, sys

class Dummy():
    def fit(self,x,y):
        self.v = y.mean()
        return self
    def predict(self,x):
        return [self.v]*len(x)

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
        sys.stdout.flush()
        harj,valid = taita_sarja([datax,datay], n_yht, i)
        malli.fit(harj[0], harj[1])
        yhattu = malli.predict(valid[0])
        neliosumma += np.sum((yhattu-valid[1])**2)
    return neliosumma, time.process_time()-alku

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
        svm.SVR(kernel='linear', cache_size=4000, **{'C': 2000, 'epsilon': 0.224, 'gamma': 5.5540816326530615})
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
    print("Vuo")
    print(taulukko)

    #luotettavuuden ristivalidointi
    if 0:
        print('\nR²\n')
        for i,nimi in enumerate(nimet[:-1]):
            y = datay[maskit[i,:]]
            x = datax[:,[i,-1]][maskit[i,:]]
            nsum_data = np.sum((y-np.mean(y))**2)
            print("\033[F\033[K%i/%i" %(i+1,len(nimet)))
            sys.stdout.flush()
            for m,mnimi in enumerate(mnimet):
                nsum_sovit,aika = ristivalidoi(x, y, mallit[m], 16)
                taulukko.iloc[m,i] = 1-nsum_sovit/nsum_data
        print('\033[F\033[K', end='')
        print(taulukko)

    #tasokuvaaja: x = luokka, y = wetland, c = vuo
    if 0:
        vanhat = np.seterr(invalid='ignore')
        for n,nimi in enumerate(nimet[:-1]):
            x = datax[:,[n,-1]][maskit[n,:]]
            y = datay[maskit[n,:]]
            skoko = 512
            piste = 3
            tmp = np.arange(skoko)/skoko
            m1,m2 = np.meshgrid(tmp,tmp)
            sovit_x = np.concatenate([m2.flatten(),m1.flatten()]).reshape([m1.size,2], order='F')
            plt.clf()
            fig,axs = plt.subplots(2,2)
            for m,mnimi in enumerate(mnimet):
                plt.sca(axs.flatten()[m])
                sovit = mallit[m].fit(x,y).predict(sovit_x)
                cgrid = np.empty([skoko,skoko],np.float32) + np.nan
                for i in range(len(sovit)):
                    cgrid[int(sovit_x[i,1]*skoko),int(sovit_x[i,0]*skoko)] = sovit[i]
                for k in range(len(y)):
                    xy = int(x[k,1]*skoko)
                    xx = int(x[k,0]*skoko)
                    cgrid[xy:xy+piste, xx:xx+piste] = y[k]
                plt.pcolormesh(m1,m2,cgrid, cmap=plt.get_cmap('gnuplot2_r'))
                plt.gca().set_aspect('equal')
                plt.colorbar()
            plt.tight_layout()
            plt.waitforbuttonpress()
        np.seterr(**vanhat)

    #kuvaaja, jossa on vain luokka
    fig,axs = plt.subplots(2,3)
    for n,nimi in enumerate(nimet[:-1]):
        plt.sca(axs.flatten()[n])
        x = datax[:,[n]][maskit[n,:]]
        y = datay[maskit[n,:]]
        sovit_x = np.linspace(0,1,101).reshape([101,1])
        plt.plot(x,y,'.',color="#000000",markersize=1)
        for m,mnimi in enumerate(mnimet):
            sovit = mallit[m].fit(x,y).predict(sovit_x)
            plt.plot(sovit_x,sovit)
    plt.show()
    return

    #kuvaaja sovitetuista suorista
    for n,nimi in enumerate(nimet[:-1]):
        x = datax[maskit[n,:]][:,[n]]
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
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

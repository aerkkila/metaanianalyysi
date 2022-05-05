#!/usr/bin/python3
from sklearn import *
import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
from wetlandvuo_data import tee_data
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
    taulukko = pd.DataFrame(0,
                            index = mnimet,
                            columns = ['std','R2','aika'])
    mallit = [
        Dummy(),
        linear_model.LinearRegression(fit_intercept=True),
        linear_model.Ridge(fit_intercept=True, alpha=1),
        svm.SVR(cache_size=4000, **{'C': 2070, 'epsilon': 1.224, 'gamma': 5.5540816326530615})
    ]

    for m,mnimi in enumerate(mnimet):
        malli = mallit[m].fit(datax,datay)
        print('\033[1;32m%s\033[0m' %(mnimi))
        for i,nimi in enumerate(nimet):
            x = np.zeros([1,datax.shape[1]], np.float32)
            x[0,i] = 1
            print('%s\t%.3f' %(nimi,malli.predict(x)[0]))

    nsum_data = np.sum((datay-np.mean(datay))**2)
    for mnimi,malli in zip(taulukko.index,mallit):
        nsum_sovit,aika = ristivalidoi(datax, datay, malli, 16)
        taulukko.loc[mnimi,:] = [np.sqrt(nsum_sovit/len(datay)), 1-nsum_sovit/nsum_data, aika]
    print(taulukko)

    if 0:
        x = datax[:,[nimet.index('bog')]]
        plt.plot(x, datay, '.')
        plt.waitforbuttonpress()
        viivat, = plt.plot(x, datay, '.')
        for mnimi in mnimet:
            malli = mallit[nimet.index(mnimi)].fit(x,datay)
            viivat.set_ydata(malli.predict(x))
            plt.title(mnimi)
            plt.waitforbuttonpress()

    return 0
    pit = int(len(x['bog'])//10*8.5)
    for suo in suot:
        fig,axs = plt.subplots(2,3)
        axs = axs.flatten()
        plt.sca(axs[0])
        xnp = x[suo].to_numpy()
        jarj = np.argsort(xnp)
        xnp = xnp[jarj]
        ynp = y.to_numpy()[jarj]
        plt.plot(xnp, ynp, '.')
        for mnimi,ax in zip(muutama_malli,axs[1:]):
            plt.sca(ax)
            plt.plot(xnp, ynp, '.')
            ind = np.where(taulukko.index==mnimi)[0][0]
            malli = mallit[ind].fit(x[:pit],y[:pit])
            plt.plot(xnp[:pit], malli.predict(x[:pit]), '.', label='model fit')
            plt.plot(xnp[pit:], malli.predict(x[pit:]), '.', label='model extrapolation')
            plt.legend(loc='upper right')
            plt.title('%s, %s' %(suo,mnimi))
        plt.show()
    return 0

def svr_param(df,param,args={}):
    pit = 50
    if param=='C':
        arvot = np.geomspace(0.1, 16000, pit) #C
    elif param=='gamma':
        arvot = np.linspace(0.01, 8, pit) #gamma
    elif param=='epsilon':
        arvot = np.linspace(0.1, 3, pit) #epsilon
    else:
        print('tuntematon parametri')
        exit(1)
    nsum_data = np.sum((df.vuo-np.mean(df.vuo))**2)
    pisteet = np.zeros(pit)
    print('')
    for i,c in enumerate(arvot):
        print("\033[F%i/%i\033[K" %(i+1,pit))
        args.update({param:c}) #gamma=2.58, epsilon=1.3
        a,b = ristivalidoi(df, svm.SVR(tol=0.005, **args), 5)
        pisteet[i] = 1-a/nsum_data
    return arvot, pisteet

def svr_param_kaikki(df,args={}):
    if True:
        a,p = svr_param(df,'C',args)
        ind = np.argmax(p)
        m = a[ind]
        print('C = %.0f\t R2 = %.3f' %(m,p[ind]))
        args.update({'C':m})
        plt.plot(a,p)
        plt.gca().set_xscale('log')
        plt.show()
    elif 'C' not in args:
        args.update({'C':4570})

    if False:
        a,p = svr_param(df,'epsilon',args)
        ind = np.argmax(p)
        m = a[ind]
        print('epsilon = %.3f\t R2 = %.3f' %(m,p[ind]))
        args.update({'epsilon':m})
        plt.plot(a,p)
        plt.gca().set_xscale('log')
        plt.show()
    elif 'epsilon' not in args:
        args.update({'epsilon':1.224})

    if False:
        a,p = svr_param(df,'gamma',args)
        ind = np.argmax(p)
        m = a[ind]
        print('gamma = %.3f\t R2 = %.3f' %(m,p[ind]))
        args.update({'gamma':m})
        plt.plot(a,p)
        plt.gca().set_xscale('log')
        plt.show()
    elif 'gamma' not in args:
        args.update({'gamma':5.717})
    return args

def main_tutki_svr():
    np.random.seed(12345)
    prf_ind = 0
    df = tee_data(prf_ind)
    df.vuo = df.vuo*1e9 #pienet luvut sotkevat menetelmiä
    args = {'C': 900, 'epsilon': 1.5204081632653061, 'gamma': 5.391020408163265} #jäätymiskausi C=17700, mutta hidas
    args = {'C': 500, 'epsilon': 1.4612244897959183, 'gamma': 0.4991836734693878} #jäätymiskausi sis prf ja lat
    args = svr_param_kaikki(df,args)
    print(args)
    return 0

class RandomSubspace():
    def __init__(self, df, nmax, samp_kwargs={}):
        self.df = df
        self.nmax = nmax
        self.samp_kwargs = samp_kwargs
    def __iter__(self):
        self.n = 0
        return self
    def __next__(self):
        if self.n >= self.nmax:
            raise StopIteration
        self.n += 1
        return self.df.sample(**self.samp_kwargs)

class OmaRandomForest():
    def __init__(self, n_estimators=100, samp_kwargs={'frac':0.025}, tree_kwargs={}):
        self.n_estimators = n_estimators
        self.samp_kwargs = samp_kwargs
        self.tree_kwargs = tree_kwargs
    def fit(self,x,y):
        df = pd.concat([x,y],axis=1)
        self.puut = np.empty(self.n_estimators, object)
        for i,dt in enumerate(RandomSubspace(df, self.n_estimators, samp_kwargs=self.samp_kwargs)):
            self.puut[i] = tree.DecisionTreeRegressor(**self.tree_kwargs).fit(dt.drop(y.name,axis=1), dt[y.name])
        return self
    def predict(self, x, palauta=True):
        self.yhatut = np.empty([x.shape[0], len(self.puut)])
        for i,puu in enumerate(self.puut):
            self.yhatut[:,i] = puu.predict(x)
        return np.mean(self.yhatut, axis=1) if palauta else None
    def confidence(arvo,x=None):
        if not x is None:
            self.predict(x, palauta=False)
        return (np.percentile(self.yhatut, arvo, axis=1), np.percentile(self.yhatut, 1-arvo, axis=1))

def main_random_forest():
    np.random.seed(12345)
    prf_ind = 0
    df = tee_data(prf_ind).drop('yksi',axis=1)
    df.vuo = df.vuo*1e9
    npist = len(df)
    nsum_data = np.sum((df.vuo-np.mean(df.vuo))**2)

    #malli = ensemble.RandomForestRegressor(n_estimators=100)
    malli = OmaRandomForest(n_estimators=100, samp_kwargs={'frac':0.5})
    nsum_sovit, aika = ristivalidoi(df, malli, 15)
    print(np.sqrt(nsum_sovit/npist), 1-nsum_sovit/nsum_data, aika)

if __name__ == '__main__':
    if 'svr' in sys.argv:
        exit(main_tutki_svr())
    elif 'rf' in sys.argv:
        exit(main_random_forest())
    else:
        exit(main())

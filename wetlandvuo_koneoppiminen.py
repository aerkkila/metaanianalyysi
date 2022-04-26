#!/usr/bin/python3
from sklearn import *
import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
import config, time, sys

suot = ['bog','fen','marsh','tundra_wetland','permafrost_bog']

def tee_data(prf_ind):
    raja_wl = 0.2
    dsbaw = xr.open_dataset('prf_maa.nc').isel({'time':range(1,10)}).median(dim='time')\
        [['wetland','bog','fen','marsh','tundra_wetland','permafrost_bog']]
    dsvuo = xr.open_dataarray(config.edgartno_dir+'posterior.nc').mean(dim='time').\
        sel({'lat':slice(dsbaw.lat.min(), dsbaw.lat.max())})
    #dsvuo = xr.open_dataarray('flux1x1_jäätymiskausi.nc').mean(dim='time')
    dsbaw = xr.where(dsbaw.wetland>=raja_wl, dsbaw, np.nan)
    df = dsbaw.to_dataframe().reset_index('prf')
    df = df.assign(vuo=dsvuo.to_dataframe()).reset_index()
    df = df.drop('wetland',axis=1)#.div(df.wetland, axis='index')
    df = df[df.prf==prf_ind]
    df.drop(['lat','lon','prf'], axis=1, inplace=True)
    df.dropna(how='any', subset=df.drop('vuo',axis=1).keys(), inplace=True)
    df.dropna(subset='vuo',inplace=True)
    #df.insert(0, 'yksi', [1]*len(df.vuo))
    dsbaw.close()
    dsvuo.close()
    return df.sample(frac=1)

class Dummy():
    def fit(self,x,y):
        self.v = y.mean()
        return self
    def predict(self,x):
        return [self.v]*len(x)

def taita_sarja(sarja, n_yht, n_sij):
    pit = len(sarja) // n_yht
    if(n_sij == n_yht-1):
        valid = sarja.iloc[pit*n_sij:]
        harj  = sarja.iloc[:pit*n_sij]
    else:
        valid = sarja.iloc[pit*n_sij:pit*(n_sij+1)]
        harj  = pd.concat([sarja.iloc[:pit*n_sij], sarja.iloc[pit*(n_sij+1):]])
    return harj,valid

def ristivalidoi(df, malli, n_yht):
    neliosumma = 0
    alku = time.process_time()
    for i in range(n_yht):
        harj,valid = taita_sarja(df, n_yht, i)
        malli.fit(harj.drop('vuo', axis=1), harj.vuo)
        yhattu = malli.predict(valid.drop('vuo', axis=1))
        neliosumma += np.sum((yhattu-valid.vuo)**2)
    return neliosumma, time.process_time()-alku

def main():
    plt.rcParams.update({'figure.figsize':(14,12)})
    np.random.seed(12345)
    prf_ind = 0
    df = tee_data(prf_ind)
    df.vuo = df.vuo*1e9 #pienet luvut sotkevat menetelmiä
    viivat = None
    taulukko = pd.DataFrame(0,
                            index = ['dummy','ols','ridge','RANSAC(ols)','RANSAC(ridge)','Theil-Sen','random_forest','SVR'],
                            columns = ['std','R2','aika'])
    mallit = [Dummy(),
              linear_model.LinearRegression(fit_intercept=True),
              linear_model.Ridge(fit_intercept=True, alpha=1),
              linear_model.RANSACRegressor(base_estimator=linear_model.LinearRegression(fit_intercept=True),
                                           min_samples=20),
              linear_model.RANSACRegressor(base_estimator=linear_model.Ridge(fit_intercept=True, alpha=1)),
              linear_model.TheilSenRegressor(),
              ensemble.RandomForestRegressor(n_estimators=50, random_state=12345),
              svm.SVR(cache_size=4000, **{'C': 2070, 'epsilon': 1.224, 'gamma': 5.5540816326530615})]
    nsum_data = np.sum((df.vuo-np.mean(df.vuo))**2)
    npist = len(df)
    if 0:
        for mnimi,malli in zip(taulukko.index,mallit):
            nsum_sovit,aika = ristivalidoi(df, malli, 20)
            taulukko.loc[mnimi,:] = [np.sqrt(nsum_sovit/npist), 1-nsum_sovit/nsum_data, aika]
        print(taulukko)

    muutama_malli = ['ols','Theil-Sen','RANSAC(ols)','RANSAC(ridge)','ridge','random_forest']
    x = df.drop('vuo',axis=1)
    y = df.vuo

    if 0:
        plt.plot(x['bog'].to_numpy(),y.to_numpy(),'.')
        plt.waitforbuttonpress()
        viivat, = plt.plot(x['bog'].to_numpy(),y.to_numpy(),'.')
        for mnimi in muutama_malli:
            ind = np.where(taulukko.index==mnimi)[0][0]
            malli = mallit[ind].fit(x,y)
            viivat.set_ydata(malli.predict(x))
            plt.title(mnimi)
            plt.waitforbuttonpress()

    pit = int(len(x['bog'])//10*8.5)
    for mnimi in muutama_malli:
        ind = np.where(taulukko.index==mnimi)[0][0]
        malli = mallit[ind].fit(x,y)
        print('\033[1;32m%s\033[0m' %(mnimi))
        for suo in suot:
            _df = df.drop('vuo',axis=1).iloc[0].copy() 
            _df[:] = 0
            _df.at[suo] = 1
            _df = pd.DataFrame(_df).transpose()
            print('%s\t%.3f' %(suo,malli.predict(_df)))

    #return 0
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

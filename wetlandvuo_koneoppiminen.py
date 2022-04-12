#!/usr/bin/python3
from sklearn import *
import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
import config, time, sys

def tee_data(prf_ind):
    raja_wl = 0.25
    dsbaw = xr.open_dataset('prf_maa.nc').isel({'time':range(1,10)}).median(dim='time')\
        [['wetland','bog','fen','marsh','tundra_wetland','permafrost_bog']]
    dsvuo = xr.open_dataarray(config.edgartno_dir+'posterior.nc').mean(dim='time').\
        sel({'lat':slice(dsbaw.lat.min(), dsbaw.lat.max())})
    #dsvuo = xr.open_dataarray('flux1x1_jäätymiskausi.nc').mean(dim='time')
    dsbaw = xr.where(dsbaw.wetland>=raja_wl, dsbaw, np.nan)
    df = dsbaw.drop_vars('wetland').to_dataframe().reset_index('prf')
    df = df.assign(vuo=dsvuo.to_dataframe()).reset_index()
    #df = df[df.prf==prf_ind]
    df.drop(['lat','lon','prf'], axis=1, inplace=True)
    df.dropna(how='any', subset=df.drop('vuo',axis=1).keys(), inplace=True)
    df.dropna(subset='vuo',inplace=True)
    df.insert(0, 'yksi', [1]*len(df.vuo))
    dsbaw.close()
    dsvuo.close()
    return df.sample(frac=1,random_state=12345)

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
    prf_ind = 0
    df = tee_data(prf_ind)
    df.vuo = df.vuo*1e9 #pienet luvut sotkevat menetelmiä
    taulukko = pd.DataFrame(0,
                            index = ['dummy','linregr','ridge','random_forest','SVR'],
                            columns = ['std','R2','aika'])
    mallit = [Dummy(),
              linear_model.LinearRegression(fit_intercept=False),
              linear_model.Ridge(fit_intercept=False, alpha=1),
              ensemble.RandomForestRegressor(n_estimators=50, random_state=12345),
              svm.SVR(cache_size=4000, **{'C': 4570, 'epsilon': 1.224, 'gamma': 5.5540816326530615})]
    #mallit[4] = svm.SVR(cache_size=4000, **{'C': 250, 'epsilon': 1.461, 'gamma': 0.499}) #prf ja lat mukana
    nsum_data = np.sum((df.vuo-np.mean(df.vuo))**2)
    npist = len(df)
    for mnimi,malli in zip(taulukko.index,mallit):
        nsum_sovit,aika = ristivalidoi(df, malli, 20)
        taulukko.loc[mnimi,:] = [np.sqrt(nsum_sovit/npist), 1-nsum_sovit/nsum_data, aika]
    print(taulukko)
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
    prf_ind = 0
    df = tee_data(prf_ind)
    df.vuo = df.vuo*1e9 #pienet luvut sotkevat menetelmiä
    args = {'C': 900, 'epsilon': 1.5204081632653061, 'gamma': 5.391020408163265} #jäätymiskausi C=17700, mutta hidas
    args = {'C': 500, 'epsilon': 1.4612244897959183, 'gamma': 0.4991836734693878} #jäätymiskausi sis prf ja lat
    args = svr_param_kaikki(df,args)
    print(args)
    return 0

if __name__ == '__main__':
    if 'svr' in sys.argv:
        exit(main_tutki_svr())
    else:
        exit(main())

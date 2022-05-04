#!/usr/bin/python3
from sklearn import tree
import numpy as np
import pandas as pd
import xarray as xr
import config, time

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
    def luottamusvali(self, arvo, x=None):
        if not x is None:
            self.predict(x, palauta=False)
        return np.percentile(self.yhatut, arvo, axis=1)

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
    dsbaw.close()
    dsvuo.close()
    return df.sample(frac=1).reset_index(drop=True)

def taita_sarja(sarja, n_taitteet, n_sij):
    pit = len(sarja) // n_taitteet
    if(n_sij != n_taitteet-1):
        valid = sarja.iloc[pit*n_sij:pit*(n_sij+1)]
        harj  = pd.concat([sarja.iloc[:pit*n_sij], sarja.iloc[pit*(n_sij+1):]])
    else:
        valid = sarja.iloc[pit*n_sij:]
        harj  = sarja.iloc[:pit*n_sij]
    return harj,valid

def ristivalidoi_kohdittain(df, ynimi, malli, n_taitteet, luottamusrajat=()):
    if(n_taitteet > len(df.index)):
        print("Varoitus n_taitteet (%i) > len(df) (%i). n_taitteet muutetaan kokoon len(df)" %(n_taitteet,len(df.index())))
        n_taitteet = len(df.index())
    yhatut = np.empty(len(df.index))
    luotthatut = np.empty([len(df.index), len(luottamusrajat)])
    #neliosumma = 0
    alku = time.process_time()
    print('')
    for ind_taite in range(n_taitteet):
        harj,valid = taita_sarja(df, n_taitteet, ind_taite)
        malli.fit(harj.drop(ynimi, axis=1), harj[ynimi])
        yhattu = malli.predict(valid.drop(ynimi, axis=1))
        #luottamusväli
        luotthattu = np.empty([len(yhattu),len(luottamusrajat)])
        for i,raja in enumerate(luottamusrajat):
            luotthattu[:,i] = malli.luottamusvali(raja)
        #palautettavaan taulukkoon oikeille kohdille
        for i, ind in enumerate(valid.index):
            yhatut[ind] = yhattu[i]
            luotthatut[ind,:] = luotthattu[i,:]
        #neliosumma += np.sum((yhattu-valid.vuo)**2)
        print("\033[F%i/%i\033[K" %(ind_taite+1,n_taitteet))
    return yhatut, np.transpose(luotthatut), time.process_time()-alku

def main():
    np.random.seed(12345)
    prf_ind = 0 # ei käytössä
    luottamusrajat = (90,95)
    df = tee_data(prf_ind)
    df.vuo = df.vuo*1e9
    npist = len(df)
    nelsum_data = np.sum((df.vuo-np.mean(df.vuo))**2)

    #malli = ensemble.RandomForestRegressor(n_estimators=100)
    malli = OmaRandomForest(n_estimators=150, samp_kwargs={'frac':0.5})
    yhattu, luotthattu, aika = ristivalidoi_kohdittain(df, 'vuo', malli, n_taitteet=50, luottamusrajat=luottamusrajat)
    print('aika: %.3f s' %aika)
    nelsum_sovit = np.sum((yhattu-df.vuo)**2)
    print('ŷ (σ,R²):\t%.5f\t%.5f' %(np.sqrt(nelsum_sovit/npist), 1-nelsum_sovit/nelsum_data))
    for i in range(len(luottamusrajat)):
        print('mean(ŷ%i < y): %.5f' %(luottamusrajat[i], np.mean(df.vuo < luotthattu[i,:])))

if __name__ == '__main__':
    exit(main())

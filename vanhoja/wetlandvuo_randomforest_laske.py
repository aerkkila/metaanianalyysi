#!/usr/bin/python3
from sklearn import tree
import numpy as np
import pandas as pd
import xarray as xr
import config, sys
from threading import Thread

#Tekee datan randomforest-menetelmän validointia varten

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
    df = dsbaw.to_dataframe().reset_index('prf')
    df = df.assign(vuo=dsvuo.to_dataframe()).reset_index()
    df = df.drop('wetland',axis=1).div(df.wetland, axis='index')
    #df = df[df.prf==prf_ind]
    df.drop(['lat','lon','prf'], axis=1, inplace=True)
    df.dropna(how='any', subset=df.drop('vuo',axis=1).keys(), inplace=True)
    df.dropna(subset='vuo',inplace=True)
    dsbaw.close()
    dsvuo.close()
    return df.reset_index(drop=True)

def taita_sarja(sarja, n_taitteet, n_sij):
    pit = len(sarja) // n_taitteet
    if(n_sij != n_taitteet-1):
        valid = sarja.iloc[pit*n_sij:pit*(n_sij+1)]
        harj  = pd.concat([sarja.iloc[:pit*n_sij], sarja.iloc[pit*(n_sij+1):]])
    else:
        valid = sarja.iloc[pit*n_sij:]
        harj  = sarja.iloc[:pit*n_sij]
    return harj,valid

def ristivalidoi_kohdittain(df, ynimi, malli, n_taitteet=10, luottamusrajat=(), yhatut=None, luotthatut=None, saie_num=0):
    if(n_taitteet > len(df.index)):
        print("Varoitus n_taitteet (%i) > len(df) (%i). n_taitteet muutetaan kokoon len(df)" %(n_taitteet,len(df.index())))
        n_taitteet = len(df.index())
    if yhatut is None:
        yhatut = np.empty(len(df.index))
    if luotthatut is None:
        luotthatut = np.empty([len(df.index), len(luottamusrajat)])
    #neliosumma = 0
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
        print(("\033["+("%i"%(saie_num+1))+"F%i/%i\033[K\033["+("%i"%(saie_num+1))+"E") %(ind_taite+1,n_taitteet), end='')
        sys.stdout.flush()
    return #yhatut, np.transpose(luotthatut), time.process_time()-alku

def main():
    np.random.seed(12345)
    prf_ind = 0 # ei käytössä
    verbose = True
    luottamusrajat = np.arange(1,100,1)
    df = tee_data(prf_ind)
    df.vuo = df.vuo*1e9
    npist = len(df)
    nelsum_data = np.sum((df.vuo-np.mean(df.vuo))**2)

    #luodaan säikeet
    toistoja = 4
    saikeita = 4
    saikeet = np.empty(toistoja,object)
    yhatut = np.empty([toistoja,len(df.index)])
    luotthatut = np.empty([toistoja, len(df.index), len(luottamusrajat)])
    print('\n'*toistoja, end='')
    for i in range(toistoja):
        malli = OmaRandomForest(n_estimators=180, samp_kwargs={'frac':0.2})
        saikeet[i] = Thread(target=ristivalidoi_kohdittain,
                            kwargs={'df':df.sample(frac=1), 'ynimi':'vuo', 'malli':malli,
                                    'yhatut':yhatut[i,...], 'luotthatut':luotthatut[i,...],
                                    'n_taitteet':16, 'luottamusrajat':luottamusrajat, 'saie_num':i})
    i=0
    while i<toistoja:
        for j in range(saikeita):
            saikeet[i].start()
            i+=1
        for s in saikeet[i-saikeita:i]:
            s.join()

    #yhattu, luotthattu, aika = ristivalidoi_kohdittain(df, 'vuo', malli, n_taitteet=20, luottamusrajat=luottamusrajat)

    nelsum_sovit = 0
    for i in range(toistoja):
        nelsum_sovit += np.sum((yhatut[i,...]-df.vuo)**2)
    nelsum_sovit /= toistoja
    print('ŷ (σ,R²):\t%.5f\t%.5f' %(np.sqrt(nelsum_sovit/npist), 1-nelsum_sovit/nelsum_data))

    np.savez('wetlandvuo_randomforest', yhattu=yhatut, rajat_hattu=luotthatut.transpose(0,2,1), rajat=luottamusrajat)
    df.to_csv('wetlandvuo_randomforest_data.csv', index=False)
    return 0

    #nämä eivät toimi
    if verbose:
        for i in range(len(luottamusrajat)):
            print('mean(ŷ%i ≤ y): %.5f' %(luottamusrajat[i], np.mean(df.vuo <= luotthatut[i,:])))
    summa = 0
    for i,r in enumerate(luottamusrajat):
        summa += np.abs(r-np.mean(df.vuo <= luotthatut[i,:])*100)
    print("mean(q-osuus) = %.5f" %(summa/len(luottamusrajat)))
    return 0

if __name__ == '__main__':
    sys.exit(main())

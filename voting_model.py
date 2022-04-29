import numpy as np
import pandas as pd
import copy

def _sample(dt, n=None, frac=None, axis=0):
    n_or_frac = 2 - int(n is None) - int(frac is None)
    if n_or_frac == 0:
        n = 1
    elif n_or_frac == 2:
        n = max([n, int(dt.shape[axis]*frac)])
    elif n is None:
        n = int(dt.shape[axis]*frac)
    if axis==0:
        return dt[np.random.Generator.permutation(dt.shape[0])[:n], ...]

    if axis==1:
        return dt[:,np.random.Generator.permutation(dt.shape[1])[:n], ...]
    if axis==2:
        return dt[:,:,np.random.Generator.permutation(dt.shape[2])[:n], ...]
    komento = 'return dt[%s np.random.Generator.permutation(dt.shape[%i])[:n], ...]' %(':,'*axis, axis)
    eval(komento)

class RandomSubspace():
    def __init__(self, dt, nmax, engine='numpy', samp_kwargs={}):
        self.dt = dt
        self.nmax = nmax
        self.samp_kwargs = samp_kwargs
        if engine == 'numpy':
            self.sampfun = lambda kwargs: _sample(self.dt, **kwargs)
        elif engine == 'pandas':
            self.sampfun = lambda kwargs: self.dt.sample(**kwargs)
    def __iter__(self):
        self.n = 0
        return self
    def __next__(self):
        if self.n >= self.nmax:
            raise StopIteration
        self.n += 1
        return self.sampfun(self.samp_kwargs)

class Voting():
    def __init__(self, model, n_estimators=200, samp_engine='numpy', samp_kwargs={}):
        self.n_estimators = n_estimators
        self.samp_kwargs = samp_kwargs
        self.model = model
        self.samp_engine = samp_engine
    def fit(self,x,y):
        df = pd.concat([x,y],axis=1)
        self.estimators = np.empty(self.n_estimators, object)
        dt = x.assign(**{y.name:y})
        rss = RandomSubspace(dt, self.n_estimators, engine=self.samp_engine, samp_kwargs=self.samp_kwargs)
        for i,dt in enumerate(rss):
            self.estimators[i] = copy.copy(self.model).fit(dt.drop(y.name,axis=1), dt[y.name])
        return self
    def predict(self, x, palauta=True):
        self.yhats = np.empty([x.shape[0], len(self.estimators)])
        for i,estimator in enumerate(self.estimators):
            self.yhats[:,i] = estimator.predict(x)
        return np.mean(self.yhats, axis=1) if palauta else None
    def get_yhats(self, x=None):
        if not x is None:
            self.predict(x, palauta=False)
        return self.yhats
    def prediction(self, confidence, x=None):
        if not x is None:
            self.predict(x, palauta=False)
        return np.percentile(self.yhats, confidence, axis=1)

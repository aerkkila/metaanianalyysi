import numpy as np
import pandas as pd
import copy

def _sample(dt, n=None, frac=None):
    n_or_frac = 2 - int(n is None) - int(frac is None)
    if n_or_frac == 0:
        n = 1
    elif n_or_frac == 2:
        n = max([n, int(dt[0].shape[0]*frac)])
    elif n is None:
        n = int(dt[0].shape[0]*frac)
    order = np.random.permutation(dt[0].shape[0])
    return [dt[0][order[:n],...], dt[1][order[:n],...]]

class RandomSubspace():
    def __init__(self, dt, nmax, dtype, samp_kwargs={}):
        self.dt = dt
        self.nmax = nmax
        self.samp_kwargs = samp_kwargs
        if dtype == 'numpy':
            self.sampfun = lambda kwargs: _sample(self.dt, **kwargs)
        elif dtype == 'pandas':
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
    def __init__(self, model, dtype, n_estimators=200, samp_kwargs={}):
        self.n_estimators = n_estimators
        self.samp_kwargs = samp_kwargs
        self.model = model
        self.dtype = dtype #'pandas' || 'numpy'
    def fit(self,x,y):
        self.estimators = np.empty(self.n_estimators, object)
        ran = lambda dt: RandomSubspace(dt, self.n_estimators, dtype=self.dtype, samp_kwargs=self.samp_kwargs)
        if self.dtype == 'pandas':
            dt = x.assign(**{y.name:y})
            rss = ran(dt)
            for i,dt in enumerate(rss):
                self.estimators[i] = copy.copy(self.model).fit(dt.drop(y.name,axis=1), dt[y.name])
        elif self.dtype == 'numpy':
            dt = [x,y]
            rss = ran(dt)
            for i,dt in enumerate(rss):
                self.estimators[i] = copy.copy(self.model).fit(dt[0], dt[1])
        return self
    def predict(self, x, palauta=True):
        self.yhats = np.empty([x.shape[0], len(self.estimators)])
        for i,estimator in enumerate(self.estimators):
            self.yhats[:,i] = estimator.predict(x)
        return np.mean(self.yhats, axis=1) if palauta else None
    def prediction(self, confidence, x=None):
        if not x is None:
            self.predict(x, palauta=False)
        return np.percentile(self.yhats, confidence, axis=1)

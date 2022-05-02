import numpy as np
import pandas as pd
import copy

def sample(dt, n, rng):
    order = rng.permutation(dt[0].shape[0])
    return [dt[0][order[:n],...], dt[1][order[:n],...]]

def search_ind(ran, limits):
    length = len(limits)
    lower = 0
    upper = length-1
    while True:
        ind = (lower+upper)//2
        if ran < limits[ind]:
            if ind==0 or limits[ind-1] <= ran:
                return ind
            upper = ind
            continue
        lower = ind

def sample_with_weights(dt, n, limits, rng):
    num = 0
    negation = False
    if n > len(dt)//2:
        negation=True
        n = len(dt)-n
    used = np.zeros(len(dt), bool)
    inds = np.empty(n, int)
    while num < n:
        while True:
            ran = rng.random()
            ind = search_ind(ran, limits)
            if not used[ind]:
                used[ind] = True
                inds[num] = ind
                num += 1
                break
    if negation:
        return dt[~used]
    return dt[inds]

def weights_to_limits(weights):
    for i in range(1,len(weights)):
        weights[i] += weights[i-1]
    for i in range(len(weights)):
        weights[i] /= weights[-1]

def make_sample_function(dt, n=None, frac=None, limits=None):
    n_or_frac = 2 - int(n is None) - int(frac is None)
    if n_or_frac == 0:
        n = 1
    if n_or_frac == 2:
        n = max([n, int(dt[0].shape[0]*frac)])
    if n is None:
        n = int(dt[0].shape[0]*frac)
    rng = np.random.default_rng(12345)
    if limits is None:
        return sample, (dt, n, rng)
    return sample_with_weights, (dt, n, limits, rng)

class RandomSubspace():
    def __init__(self, dt, nmax, samp_kwargs={}):
        self.dt = dt
        self.nmax = nmax
        self.sampfun, self.samp_args = make_sample_function(dt, **samp_kwargs)
    def __iter__(self):
        self.n = 0
        return self
    def __next__(self):
        if self.n >= self.nmax:
            raise StopIteration
        self.n += 1
        return self.sampfun(*self.samp_args)

class Voting():
    def __init__(self, model, dtype, n_estimators=200, samp_kwargs={}):
        self.n_estimators = n_estimators
        self.samp_kwargs = samp_kwargs
        self.model = model
        self.dtype = dtype #has to be numpy
    def fit(self,x,y):
        self.estimators = np.empty(self.n_estimators, object)
        ran = lambda dt: RandomSubspace(dt, self.n_estimators, samp_kwargs=self.samp_kwargs)
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

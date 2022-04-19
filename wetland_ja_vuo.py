#!/usr/bin/python3
from matplotlib.pyplot import *
import numpy as np
import xarray as xr
import sklearn.linear_model as sk_lm

np.random.seed(12345)

ch4 = xr.open_dataarray('../edgartno_lpx/posterior.nc').mean('time')
maa = xr.open_dataset('BAWLD1x1.nc')
ch4 = ch4.sel({'lat':slice(maa.lat.min(),maa.lat.max())})

x=maa.wetland.data.flatten()
maski = x > 0.25
x = x[maski]
X = np.array([np.zeros(len(x))+1, x]).transpose()
y = ch4.data.flatten()[maski]# / x
#malli = sk_lm.TheilSenRegressor().fit(X,y)
malli = sk_lm.RANSACRegressor().fit(X,y)
plot(x, y, '.')
#plot(x, x*tulos.slope+tulos.intercept)
#x = x.reshape(-1,1)
plot(x, malli.predict(X))
show()

#!/usr/bin/python3
from sklearn.linear_model import LinearRegression
import numpy as np

class Residmalli(LinearRegression):
    def __init__(self, x, **kwargs):
        self.korr_malli = LinearRegression()
        self.korr_malli.fit(x[:,[1]], x[:,0])
        super().__init__(**kwargs)
    def muunna(self, x):
        resid = x[:,0] - self.korr_malli.predict(x[:,[1]])
        return np.concatenate([resid.reshape([len(resid),1]), x[:,[1]]], axis=1)
    def fit(self, x, y, **kwargs):
        return super().fit(self.muunna(x), y, **kwargs)
    def predict(self, x, **kwargs):
        return super().predict(self.muunna(np.array(x)), **kwargs)

def main():
    rcParams.update({'figure.figsize':(13,12)})
    dt = tee_data('whole_year')
    monistus = 8
    dtx = dt[0]
    dty = dt[1]
    wnimet = dt[2][:-1]
    indeksit = valitse_painottaen(dt[3], monistus)
    dtx0 = dtx[indeksit]
    dty0 = dty[indeksit]
    xplot = np.linspace(0,1,101).reshape([101,1])
    for i,w in enumerate([0,1,3,4,5]):
        maski = dtx0[:,w] >= 0.03
        dtx = dtx0[maski,:]
        dtx = dtx[:,[w,-1]]
        ax = subplot(2,3,i+1)
        y = dty0[maski]
        #malli = Residmalli(dtx)
        malli = LinearRegression()
        malli.fit(dtx,y)
        print(malli.coef_)
        plot(dtx[:,0],y, '.')
        plot(dtx[:,0],malli.predict(dtx), '.')
        print("%s: %.4f" %(wnimet[w], malli.predict([[1,1]])))
        title(wnimet[w])
    show()
    return

if __name__=='__main__':
    from wetlandvuo_data import tee_data
    from wetlandtyypin_pisteet import valitse_painottaen
    from matplotlib.pyplot import *
    main()

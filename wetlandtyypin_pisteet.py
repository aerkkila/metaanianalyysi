#!/usr/bin/python3
from sklearn import linear_model as lm
from matplotlib.pyplot import *
from wetlandvuo_data import tee_data
import numpy as np

aste = 0.0174532925199
R2 = 40592558970441
PINTAALA1x1 = lambda _lat: aste*R2*( np.sin((_lat+1)*aste) - np.sin(_lat*aste) )*1.0e-6
def pintaalat1x1(lat):
    alat = np.empty_like(lat)
    for i,la in enumerate(lat):
        alat[i] = PINTAALA1x1(la)
    return alat

def pintaalan_painotus(alat):
    painot = alat/alat[0]
    for i in range(1,len(painot)):
        painot[i] += painot[i-1]
    for i in range(len(painot)):
        painot[i] /= painot[-1]
    return painot

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
        if lower == upper-1:
            return upper
    return

#Eteläisimmät hilaruudut ovat noin 8 kertaa niin suuria kuin pohjoisimmat.
#Tällä valitaan datasta hilaruutuja painottaen todennäköisyyksiä pituuspiirin mukaan.
#Mieluiten kerroin > 8, jotta eteläisimpiäkin hilaruutuja tulee keskimäärin vähintään 1.
def valitse_painottaen(lat,kerroin):
    n_samp = int(len(lat)*kerroin)
    painot = pintaalan_painotus(pintaalat1x1(lat))
    indeksit = np.empty(n_samp,int)
    luvut = np.random.default_rng(12345).random(n_samp)
    for i in range(n_samp):
        indeksit[i] = search_ind(luvut[i], painot)
    return indeksit

def ortogonaali_regressio(dtx,dty):
    n11 = 1/(dtx.shape[0]-1)
    dtym = np.mean(dty)
    dtxm = np.mean(dtx)
    sxx = n11*np.sum((dtx-dtxm)**2)
    syy = n11*np.sum((dty-dtym)**2)
    sxy = n11*(np.sum((dty-dtym)*(dtx-dtxm)))
    a1 = (syy-sxx+np.sqrt((syy-sxx)**2 + 4*sxy**2)) / (2*sxy)
    a0 = dtym - a1*dtxm
    return [a0,a1]

def piirra_ortog(t_ind, piirtox, dtx, nimet):
    datax = dtx[:,[t_ind+1]]
    wetl = dtx[:,[-1]]
    maski = (datax>=0.03).flatten()
    a0,a1 = ortogonaali_regressio(datax[maski],wetl[maski])
    tausta, = plot(datax[maski,:],wetl[maski,:],'.',color='b')
    tausta, = plot(datax[~maski,:],wetl[~maski,:],'.',color='r')
    piirtoy = piirtox[:,1]*a1 + a0
    print(a0,a1)
    sovit, = plot(piirtox[:,1],piirtoy)
    xlabel(nimet[t_ind])
    ylabel('wetland')
    show()

class Ortog():
    def __init__(self,suure=0):
        self.suure = suure
        return
    def fit(self,x,y):
        self.a0,self.a1 = ortogonaali_regressio(x[:,self.suure],y)
    def predict(self,x):
        return x[:,self.suure]*self.a1 + self.a0
    def get_params(self,deep):
        return {'suure':self.suure}
    def set_params(self,**kwargs):
        for k in kwargs.keys():
            if k == 'suure':
                self.suure = kwargs[k]

def piirra(t_ind, piirtox, dtx, nimet):
    datax1 = dtx[:,[0,t_ind+1]]
    datax = dtx[:,[t_ind+1]]
    wetl = dtx[:,[-1]]

    pohjamalli = lm.LinearRegression(fit_intercept=False)
    #pohjamalli = Ortog(suure=1)
    resid = 0.15
    malli = lm.RANSACRegressor(pohjamalli,
                               random_state=12345,
                               min_samples=15,
                               residual_threshold=resid,
                               stop_probability=0.999,
                               max_trials=1000)
    maski = (datax>=0.03).flatten()

    malli.fit(datax1[maski,:],wetl[maski,:])
    print(malli.n_trials_)
    maski1 = malli.inlier_mask_
    plot(datax[maski,:][maski1,:],wetl[maski,:][maski1,:],'.',color='#ff000005')
    plot(datax[maski,:][~maski1,:],wetl[maski,:][~maski1,:],'.',color='#ff000005')
    plot(datax[~maski,:],wetl[~maski,:],'.',color='#ff000005')
    piirtoy = malli.predict(piirtox)
    print(malli.estimator_.coef_[0])
    plot(piirtox[:,1],piirtoy+resid,color='b')
    plot(piirtox[:,1],piirtoy-resid,color='b')
    xlabel(nimet[t_ind])
    ylabel('wetland')
    show()

def main():
    rcParams.update({'figure.figsize':(10,8),'font.size':12})
    dt       = tee_data()
    dtx      = dt[0]
    nimet    = dt[2]
    lat      = dt[3]
    indeksit = valitse_painottaen(lat,12)
    dtx      = dtx[indeksit]
    #Pienen kohinan lisääminen auttaa näkemään kuvaajasta, missä pisteitä on paljon.
    #Muuten monet pisteet ovat täsmälleen päällekkäin.
    rng = np.random.default_rng(12345)
    for i in range(dtx.shape[0]):
        for j in range(dtx.shape[1]-1):
            dtx[i,j] += rng.normal(dtx[i,j], 0.006)
        dtx[i,-1] = np.sum(dtx[i,:-1])
    num      = 20
    piirtox  = np.linspace(0,1,num).reshape([num,1])
    yhdet    = np.zeros([num,1])+1
    piirtox  = np.concatenate([yhdet,piirtox], axis=1)
    yhdet    = np.zeros([dtx.shape[0],1]) + 1
    dtx      = np.concatenate([yhdet,dtx], axis=1)
    for t_ind in range(5):
        piirra(t_ind, piirtox, dtx, nimet)

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

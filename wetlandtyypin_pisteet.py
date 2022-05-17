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
#Tällä valitaan datasta hilaruutuja painottaen todennäköisyyksiä leveyspiirin mukaan.
#Mieluiten kerroin > 8, jotta eteläisimpiäkin hilaruutuja tulee keskimäärin vähintään 1.
def valitse_painottaen(lat,kerroin):
    n_samp = int(len(lat)*kerroin)
    painot = pintaalan_painotus(pintaalat1x1(lat))
    indeksit = np.empty(n_samp,int)
    luvut = np.random.default_rng(12345).random(n_samp)
    for i in range(n_samp):
        indeksit[i] = search_ind(luvut[i], painot)
    return indeksit

axs = None
on_axs = False
resids = [0.15, 0.12, 0.055, 0.3, 0.2, 0.15]

def sovita(t_ind, piirtox, dtx, nimet):
    global axs, on_axs
    datax1 = dtx[:,[0,t_ind+1]] #sarake 0 on ykkössarake
    datax = dtx[:,[t_ind+1]]
    wetl = dtx[:,[-1]]

    pohjamalli = lm.LinearRegression(fit_intercept=False)
    kynnysarvo = 0.03
    resid = resids[t_ind]
    malli = lm.RANSACRegressor(pohjamalli,
                               random_state=12345,
                               min_samples=15,
                               residual_threshold=resid,
                               stop_probability=0.999,
                               max_trials=1000)
    maski = (datax>=kynnysarvo).flatten()

    malli.fit(datax1[maski,:],wetl[maski,:])
    print(malli.n_trials_)
    maski1 = malli.inlier_mask_

    piirtoy = malli.predict(piirtox)
    print(malli.estimator_.coef_[0])
    r = list(malli.estimator_.coef_[0])
    r.extend([resid,kynnysarvo])
    if piirretaan:
        if not on_axs:
            fig,axs = subplots(2,3)
            on_axs = True
        sca(axs.flatten()[t_ind])
        #Pienen kohinan lisääminen auttaa näkemään kuvaajasta, missä pisteitä on paljon.
        #Muuten monet pisteet ovat täsmälleen päällekkäin, koska valitse_painottaen monistaa niitä.
        rng = np.random.default_rng(12345)
        datax_c = datax.flatten().copy()
        wetl_c = wetl.flatten().copy()
        for i in range(len(datax_c)):
            satunn     = rng.normal(0, 0.004)
            datax_c[i] += satunn
            wetl_c[i]  += satunn
        plot(datax_c[maski][maski1],wetl_c[maski][maski1],'.',color='#33cc0003') #valitut pisteet
        plot(datax_c[maski][~maski1],wetl_c[maski][~maski1],'.',color='#ff000003')
        plot(datax_c[~maski],wetl_c[~maski],'.',color='#ff000003')
        #plot(piirtox[:,1],piirtoy+resid,color='b')
        #plot(piirtox[:,1],piirtoy-resid,color='b')
        gca().set_ylim([0,1])
        xlabel(nimet[t_ind])
        ylabel('wetland')
    return r

def main():
    global piirretaan
    piirretaan = False
    if "-p" in sys.argv:
        piirretaan = True
    rcParams.update({'figure.figsize':(12,10),'font.size':13})
    dt       = tee_data()
    dtx      = dt[0]
    nimet    = dt[2]
    lat      = dt[3]
    indeksit = valitse_painottaen(lat,12)
    dtx      = dtx[indeksit]
    num      = 20
    piirtox  = np.linspace(0.03,1,num).reshape([num,1])
    yhdet    = np.zeros([num,1])+1
    piirtox  = np.concatenate([yhdet,piirtox], axis=1)
    yhdet    = np.zeros([dtx.shape[0],1]) + 1
    dtx      = np.concatenate([yhdet,dtx], axis=1)

    f = open("%s.csv" %(sys.argv[0][:-3]), 'w')
    f.write("tyyppi,a0,a1,resid,kynnysarvo\n")
    for t_ind in range(len(nimet)-1):
        param = sovita(t_ind, piirtox, dtx, nimet)
        print(param)
        f.write("%s,%.5f,%.5f,%.5f,%.5f\n" %(nimet[t_ind],param[0],param[1],param[2],param[3]))
    f.close()
    if piirretaan:
        tight_layout()
        savefig("kuvia/%s.png" %(sys.argv[0][:-3]))
    return

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

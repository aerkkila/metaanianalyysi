#!/bin/python
from netCDF4 import Dataset
from matplotlib.pyplot import *
import numpy as np
import sys, os

kansio = '%s/smos_uusi/ft_percent' %(os.getenv('HOME'))

def rajaa(dt, maski):
    a = dt.shape[0]
    b = np.product(dt.shape[1:])
    dt = dt.reshape([a,b])
    uusi = np.empty([a, np.sum(maski)], dt.dtype)
    for t in range(dt.shape[0]):
        uusi[t,:] = dt[t,:][maski]
    return uusi

def aikamuunnos(dt, dt1, tpit, alat):
    alku = 220 # tämä on joskus elokuussa
    loppu = alku+365
    ret    = np.empty([len(tpit)-1, dt.shape[1], 100], dt.dtype)
    ret1   = np.empty_like(ret)
    rind   = np.zeros(len(tpit)-1, int)
    määrät = np.zeros(len(tpit), np.float64) # viimeiseen tulee ohitettu pinta-ala
    for p in range(dt.shape[1]):
        t0 = 0
        t1 = 999999999
        for t in range(alku,loppu):
            if(dt[t,p] >= 0.1):
                t0 = t
                break
        for t in range(t,loppu):
            if(dt[t,p] >= 0.9):
                t1 = t
                break
        ind = np.searchsorted(tpit, t1-t0)
        pit = t1-t0
        if(ind == 0 or pit > tpit[-1]):
            määrät[-1] += alat[p]
            continue
        ind -= 1
        indek = np.linspace(t0-pit, t1, 100).astype(int)
        ret[ind,rind[ind],:] = dt[indek,p]
        ret1[ind,rind[ind],:] = dt1[indek,p]
        määrät[ind] += alat[p]
        rind[ind] += 1
    return ret, ret1, määrät, rind

vuosi = 2015

def lue(nimi):
    i = 0
    a = Dataset(nimi %(kansio, vuosi))
    b = np.ma.getdata(a['data'][:])
    a.close()
    a = Dataset(nimi %(kansio, vuosi+1))
    b = np.concatenate([b, np.ma.getdata(a['data'][:])], axis=0)
    a.close()
    return b

def main():
    rcParams.update({'figure.figsize':(12,10), 'font.size':19})
    ft = np.empty(2, object)

    a = Dataset("aluemaski.nc")
    maski = np.ma.getdata(a['maski'][:]).flatten().astype(bool)
    a.close()

    ft[0] = lue("%s/frozen_percent_pixel_%i.nc")
    ft[0] = rajaa(ft[0], maski)
    ft[1] = lue("%s/partly_frozen_percent_pixel_%i.nc")
    ft[1] = rajaa(ft[1], maski)
    alat = np.load('pintaalat.npy')[maski]

    rajat = [1, 8, 15, 35, 60]

    ft[0],ft[1],alat,pitdet = aikamuunnos(ft[0], ft[1], rajat, alat)
    a = np.empty([ft[0].shape[0],ft[0].shape[2]], ft[0].dtype)
    b = np.empty_like(a)
    for i,p in enumerate(pitdet):
        a[i,:] = np.mean(ft[0][i,:p,:], axis=0)
        b[i,:] = np.mean(ft[1][i,:p,:], axis=0)

    x = np.linspace(-100,100,a.shape[-1])
    ala = np.sum(alat)

    for r in range(len(rajat)-1):
        plot(x, a[r,:], label='frozen', linewidth=2)
        plot(x, b[r,:], label='partly_frozen', linewidth=2)
        xlabel('freezing period elapsed (%)')
        title('%i < freezing period length ≤ %i, %.0f %% of area' %(rajat[r], rajat[r+1], alat[r]/ala*100))
        legend(loc='upper left', fancybox=0)
        tight_layout()
        if '-s' in sys.argv:
            savefig('kuvia/osajää%i.png' %(r))
            clf()
        else:
            show()

    # yhdistetään erilliskuvat käyttäen komentiriviohjelmaa gm
    if '-s' in sys.argv:
        kuvia = len(rajat)-1
        xpit = int(np.ceil(np.sqrt(kuvia)))
        ypit = int(np.ceil((kuvia) / xpit))
        str = 'gm convert'
        ind=0
        for y in range(ypit):
            if not ind < kuvia:
                break
            str += ' +append'
            for x in range(xpit):
                if not ind < kuvia:
                    break
                str += ' kuvia/osajää%i.png' %(ind); ind+=1
        str += ' -append kuvia/osajää.png'
        print(str)
        try:
            os.system(str)
        except Exception as e:
            print('epäonnistui: %s' %(str(e)))

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

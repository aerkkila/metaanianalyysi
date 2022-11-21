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

def aikamuunnos(dt, dt1, tpit):
    alku = 220 # tämä on joskus elokuussa
    loppu = alku+365
    ret = np.empty([len(tpit)-1, dt.shape[1], 100], dt.dtype)
    ret1 = np.empty_like(ret)
    rind = np.zeros(len(tpit)-1, int)
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
            continue
        ind -= 1
        indek = np.round(np.linspace(t0-pit, t1, 100)).astype(int)
        ret[ind,rind[ind],:] = dt[indek,p]
        ret1[ind,rind[ind],:] = dt1[indek,p]
        rind[ind] += 1
    return ret, ret1, rind

vuosi = 2015

def lue(nimi, maski):
    i = 0
    a = Dataset(nimi %(kansio, vuosi))
    b = np.ma.getdata(a['data'][:])
    a.close()
    a = Dataset(nimi %(kansio, vuosi+1))
    b = np.concatenate([b, np.ma.getdata(a['data'][:])], axis=0)
    a.close()
    return rajaa(b, maski)

def main():
    rcParams.update({'figure.figsize':(12,10), 'font.size':19})
    ft = np.empty(2, object)

    a = Dataset("aluemaski.nc")
    maski = np.ma.getdata(a['maski'][:]).flatten().astype(bool)
    a.close()

    ft[0] = lue("%s/frozen_percent_pixel_%i.nc", maski)
    ft[1] = lue("%s/partly_frozen_percent_pixel_%i.nc", maski)

    rajat = [5, 15, 30, 50, 70]

    ft[0],ft[1],pitdet = aikamuunnos(ft[0], ft[1], rajat)
    a = np.empty([ft[0].shape[0],ft[0].shape[2]], ft[0].dtype)
    b = np.empty_like(a)
    for i,p in enumerate(pitdet):
        a[i,:] = np.mean(ft[0][i,:p,:], axis=0)
        b[i,:] = np.mean(ft[1][i,:p,:], axis=0)

    x = np.linspace(-100,100,a.shape[-1])

    for r in range(len(rajat)-1):
        plot(x, a[r,:], label='frozen', linewidth=2)
        plot(x, b[r,:], label='partly_frozen', linewidth=2)
        xlabel('freezing period state (%)')
        title('%i < freezing period length ≤ %i' %(rajat[r], rajat[r+1]))
        legend(loc='upper left', fancybox=0)
        tight_layout()
        if '-s' in sys.argv:
            savefig('kuvia/osajää%i.png' %(r))
            clf()
        else:
            show()

    # yhdistetään erilliskuvat käyttäen komentiriviohjelmaa gm
    if '-s' in sys.argv:
        xpit = int(np.ceil(np.sqrt(len(rajat))-1))
        ypit = int(np.ceil((len(rajat)-1) / xpit))
        str = 'gm convert'
        ind=0
        for y in range(ypit):
            str += ' +append'
            for x in range(xpit):
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

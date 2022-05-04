#!/usr/bin/python3
from sklearn import linear_model
import numpy as np
from voting_model import Voting
import wetlandvuo_data as wldata
import multiprocessing as mp
import multiprocessing.shared_memory as shm
import time, locale, sys

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
    #tehdään painoista rajat, joihin voidaan sijoittaa satunnaisluku [0,1[,
    #jolloin todennäköisyys painottuu oikein huomioiden hilaruutujen koon eroavuuden leveyspiirin suhteen
    for i in range(1,len(painot)):
        painot[i] += painot[i-1]
    for i in range(len(painot)):
        painot[i] /= painot[-1]
    return painot

def taita_sarja(lista, n_taitteet, n_sij):
    pit = len(lista[1]) // n_taitteet
    harj = np.empty(len(lista),object)
    valid = np.empty(len(lista),object)
    if(n_sij < n_taitteet-1):
        for i in range(len(lista)):
            valid[i] = lista[i][pit*n_sij : pit*(n_sij+1), ...]
            harj[i] = np.concatenate((lista[i][:pit*n_sij, ...], lista[i][pit*(n_sij+1):]))
    else:
        for i in range(len(lista)):
            valid[i] = lista[i][pit*n_sij:]
            harj[i] = lista[i][:pit*n_sij]
    return harj, valid

def ristivalidointisaie(datax, datay, yhatname, yhatvotname, yhatrajaname, alku, loppu, n_taitteet, pind, wind):
    #global ennusrajat, datax, datay, eh0, yh0, alat
    yhat_shm = shm.SharedMemory(name=yhatname)
    yhat = np.ndarray(muoto0, np.float32, buffer=yhat_shm.buf)
    yhat_voting_shm = shm.SharedMemory(name=yhatvotname)
    yhat_voting = np.ndarray(muoto0, np.float32, buffer=yhat_voting_shm.buf)
    yhat_raja_shm = shm.SharedMemory(name=yhatrajaname)
    yhat_raja = np.ndarray(muoto1, np.float32, buffer=yhat_raja_shm.buf)

    yind = len(datay)//n_taitteet * alku
    muoto = "\033[%iF%%i/%%i\033[K\033[%iE" %(pind,pind)
    for ind_taite in range(alku,loppu):
        print(muoto %(ind_taite,loppu), end='')
        sys.stdout.flush()
        harj,valid = taita_sarja([datax, datay, alat], n_taitteet, ind_taite)
        painotus = pintaalan_painotus(harj[2])
        malli.fit(harj[0], harj[1], samp_kwargs={'n':10, 'limits':painotus})
        yind1 = yind+len(valid[1])
        yhat_voting[wind,yind:yind1] = malli.predict(valid[0])
        yhat_raja[wind,:,yind:yind1] = malli.prediction(prpist)
        yhat[wind,yind:yind1] = pohjamalli.fit(harj[0], harj[1]).predict(valid[0])
        yind = yind1
    muoto = "\033[%iF\033[K\033[%iE" %(pind,pind)
    print(muoto, end='')
    sys.stdout.flush()
    yhat_shm.close()
    yhat_voting_shm.close()
    yhat_raja_shm.close()

def ristivalidointidata(datax, datay, n_taitteet, njobs, wind):
    if(n_taitteet > len(datay)):
        print("Varoitus n_taitteet (%i) > len(df) (%i). n_taitteet muutetaan kokoon len(df)" %(n_taitteet,len(df.index())))
        n_taitteet = len(datay)
    print('\n'*njobs, end='')
    prosessit = np.empty(njobs-1, object) #jakoperuste on taitteet
    i=-1
    for i in range(njobs-1):
        alku = int(n_taitteet/njobs*i)
        loppu = int(n_taitteet/njobs*(i+1))
        prosessit[i] = mp.Process(target=ristivalidointisaie, args=(datax, datay, yhat_shm.name, yhat_voting_shm.name, yhat_raja_shm.name, alku, loppu, n_taitteet, njobs-i, wind))
        prosessit[i].start()
    i += 1
    alku = int(n_taitteet/njobs*i)
    loppu = n_taitteet
    ristivalidointisaie(datax, datay, yhat_shm.name, yhat_voting_shm.name, yhat_raja_shm.name, alku, loppu, n_taitteet, njobs-i, wind)
    for i in range(njobs-1):
        prosessit[i].join()
    return

#a/b, missä a on summa jakajaa pienempien dt:n pisteitten etäisyydestä jakajaan
#     ja b on summa kaikkien pisteitten absoluuttisista etäisyyksistä jakajaan
#     jakajan ollessa keskiarvo tämä siis palauttaa 0,5 jne.
def massojen_suhde(jakaja, dt):
    maski = dt<jakaja
    a = np.sum(jakaja[maski] - dt[maski])
    maski = ~maski
    b = a + np.sum(dt[maski] - jakaja[maski])
    return a/b

def main():
    global alat, tmp, yhat_shm, yhat_voting_shm, yhat_raja_shm, muoto0, muoto1, malli, pohjamalli, prpist
    njobs = 1
    tmp = False
    if '-j' in sys.argv:
        njobs = int(sys.argv[sys.argv.index('-j')+1])
    if '-tmp' in sys.argv:
        tmp = True
    np.random.seed(12345)
    locale.setlocale(locale.LC_ALL, '')
    dt = wldata.tee_data('numpy', tmp=tmp)
    datax = dt[0]
    datay = dt[1]
    nimet = dt[2]
    lat = dt[3]

    alat = pintaalat1x1(lat)
    wetl = np.sum(datax, axis=1).reshape([datax.shape[0],1])
    datax = np.concatenate([datax,wetl],axis=1)
    prpist = np.arange(1,100)

    muoto0 = [len(nimet),len(datay)]
    muoto1 = [len(nimet),len(prpist),len(datay)]
    yhat_shm = shm.SharedMemory(create=True, size=np.product(muoto0)*4)
    yhat_voting_shm = shm.SharedMemory(create=True, size=np.product(muoto0)*4)
    yhat_raja_shm = shm.SharedMemory(create=True, size=np.product(muoto1)*4)

    yhat = np.ndarray(muoto0, np.float32, buffer=yhat_shm.buf)
    yhat_voting = np.ndarray(muoto0, np.float32, buffer=yhat_voting_shm.buf)
    yhat_raja = np.ndarray(muoto1, np.float32, buffer=yhat_raja_shm.buf)
    
    pohjamalli = linear_model.LinearRegression()
    malli = Voting(pohjamalli, n_estimators=10000)
    for i,nimi in enumerate(nimet):
        np.random.seed(12345) #lienee turha
        print("\033[92m%s\033[0m" %(nimi))
        x = datax[:,[i,-1]]
        ristivalidointidata(x, datay, 4, njobs, i)
        if 0:
            varlin = np.mean((yhatut-datay)**2)
            evarlin = np.mean((ehatut[:,2]-datay)**2)
            var = np.var(datay)
            muoto = "\033[%iF" %(njobs)
            print(muoto, end='')
            print(locale.format_string("selitetty varianssi = \033[1m%.4f\033[0m; %.4f", (1-varlin/var, 1-evarlin/var)))
            print("Arvioidun keskiarvon todellinen arvo: %.4f\n" %(massojen_suhde(yhatut,datay)), end='')

    np.savez('wetlandvuo_voting_data%s.npz' %("_tmp" if tmp else ""),
             x=datax, y=datay, yhat=yhat, yhat_voting=yhat_voting, yhat_raja=yhat_raja, rajat=prpist)
    yhat_shm.close()
    yhat_voting_shm.close()
    yhat_raja_shm.close()
    yhat_shm.unlink()
    yhat_voting_shm.unlink()
    yhat_raja_shm.unlink()
    return 0

if __name__=='__main__':
    main()

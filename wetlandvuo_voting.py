#!/usr/bin/python3
from sklearn import linear_model
import numpy as np
from voting_model import Voting
import wetlandvuo_data as wldata
import multiprocessing as mp
import multiprocessing.shared_memory as shm
import time, locale, sys

def taita_sarja(x, y, n_taitteet, n_sij):
    pit = len(y) // n_taitteet
    if(n_sij < n_taitteet-1):
        validx = x[pit*n_sij : pit*(n_sij+1), ...]
        validy = y[pit*n_sij : pit*(n_sij+1), ...]
        harjx = np.concatenate((x[:pit*n_sij, ...], x[pit*(n_sij+1):]))
        harjy = np.concatenate((y[:pit*n_sij, ...], y[pit*(n_sij+1):]))
    else:
        validx = x[pit*n_sij:]
        validy = y[pit*n_sij:]
        harjx = x[:pit*n_sij]
        harjy = y[:pit*n_sij]
    return harjx, harjy, validx, validy

def ristivalidointisaie(yhnimi, ehnimi, malli, alku, loppu, n_taitteet, ind):
    global ennusrajat, datax, datay, eh0, yh0
    y_shm = shm.SharedMemory(name=yhnimi)
    yhatut = np.ndarray(yh0.shape, yh0.dtype, buffer=y_shm.buf)
    e_shm = shm.SharedMemory(name=ehnimi)
    ennushatut = np.ndarray(eh0.shape, eh0.dtype, buffer=e_shm.buf)
    yind = len(datay)//n_taitteet * alku
    muoto = "\033[%iF%%i/%%i\033[K\033[%iE" %(ind,ind)
    for ind_taite in range(alku,loppu):
        print(muoto %(ind_taite,loppu), end='')
        sys.stdout.flush()
        harjx,harjy,validx,validy = taita_sarja(datax, datay, n_taitteet, ind_taite)
        malli.fit(harjx, harjy)
        yind1 = yind+len(validy)
        yhatut[yind:yind1] = malli.predict(validx)
        for i,e in enumerate(ennusrajat):
            ennushatut[yind:yind1,i] = malli.prediction(e)
        yind = yind1
    muoto = "\033[%iF\033[K\033[%iE" %(ind,ind)
    print(muoto, end='')
    sys.stdout.flush()
    y_shm.close()
    e_shm.close()

def ristivalidointidata(malli, n_taitteet, ennusrajat=(), njobs=4):
    global eh0, yh0, datax, datay
    #luodaan jaettu muisti, koska pythonia ei voi säikeistää jakamatta prosesseihin
    eh0 = np.empty([len(datay), len(ennusrajat)])
    e_shm = shm.SharedMemory(create=True, size=eh0.nbytes)
    eh = np.ndarray(eh0.shape, eh0.dtype, buffer=e_shm.buf)
    eh[:] = eh0[:]
    yh0 = np.empty(len(datay))
    y_shm = shm.SharedMemory(create=True, size=yh0.nbytes)
    yh = np.ndarray(yh0.shape, yh0.dtype, buffer=y_shm.buf)
    yh[:] = yh0[:]
    if(n_taitteet > len(datay)):
        print("Varoitus n_taitteet (%i) > len(df) (%i). n_taitteet muutetaan kokoon len(df)" %(n_taitteet,len(df.index())))
        n_taitteet = len(datay)
    print('\n'*njobs, end='')
    ind = 0
    alku = time.process_time()
    saikeet = np.empty(njobs-1, object) #jakoperuste on taitteet
    for i in range(njobs-1):
        alku = int(n_taitteet/njobs*i)
        loppu = int(n_taitteet/njobs*(i+1))
        saikeet[i] = mp.Process(target=ristivalidointisaie, args=(y_shm.name, e_shm.name, malli, alku, loppu, n_taitteet, njobs-i))
        saikeet[i].start()
    i += 1
    alku = int(n_taitteet/njobs*i)
    loppu = n_taitteet
    ristivalidointisaie(y_shm.name, e_shm.name, malli, alku, loppu, n_taitteet, njobs-i)
    for i in range(njobs-1):
        saikeet[i].join()
    eh0[:] = eh[:]
    yh0[:] = yh[:]
    y_shm.unlink()
    e_shm.unlink()
    return yh0, eh0, time.process_time()-alku

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
    global ennusrajat, datax, datay
    np.random.seed(12345)
    locale.setlocale(locale.LC_ALL, '')
    tyyppi = 'numpy'
    dt = wldata.tee_data(tyyppi)
    if tyyppi == 'pandas':
        datax = dt.drop('vuo', axis=1)
        datay = dt.vuo
    elif tyyppi == 'numpy':
        datax = dt[0]
        datay = dt[1]
        nimet = dt[2]

    wetl = np.array([np.sum(datax, axis=1),]).transpose()
    datax0 = datax.copy()
    yhatut_list = np.empty(len(nimet), object)
    ehatut_list = np.empty(len(nimet), object)
    ennusrajat = np.arange(1,100,2)
    for i,nimi in enumerate(nimet):
        np.random.seed(12345)
        print("\033[92m%s\033[0m" %(nimi))
        datax = np.concatenate((datax0[:,[i]], wetl), axis=1)
        vm = Voting(linear_model.LinearRegression(), tyyppi, n_estimators=10000, samp_kwargs={'n':10})
        yhatut, ehatut, aika = ristivalidointidata(vm, 16, ennusrajat)
        #print('aika = %.4f s' %aika)
        varlin = np.mean((yhatut-datay)**2)
        evarlin = np.mean((ehatut[:,2]-datay)**2)
        var = np.var(datay)
        print(locale.format_string("selitetty osuus = \033[1m%.4f\033[0m; %.4f", (1-varlin/var, 1-evarlin/var)))        
        for e in range(len(ennusrajat)):
            print("\t%.4f;" %(massojen_suhde(ehatut[:,e],datay)), end='')
        print("\n%.4f" %(massojen_suhde(yhatut,datay)), end='')
        print("\n", end='')
        yhatut_list[i] = yhatut
        ehatut_list[i] = ehatut
    np.savez('wetlandvuo_voting_data.npz', yhatut_list=yhatut_list, ehatut_list=ehatut_list, ennusrajat=ennusrajat, nimet=nimet)
    return 0

if __name__=='__main__':
    main()

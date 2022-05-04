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

def ristivalidointisaie(yhnimi, ehnimi, malli, alku, loppu, n_taitteet, ind):
    global ennusrajat, datax, datay, eh0, yh0, alat
    y_shm = shm.SharedMemory(name=yhnimi)
    yhatut = np.ndarray(yh0.shape, yh0.dtype, buffer=y_shm.buf)
    e_shm = shm.SharedMemory(name=ehnimi)
    ennushatut = np.ndarray(eh0.shape, eh0.dtype, buffer=e_shm.buf)
    yind = len(datay)//n_taitteet * alku
    muoto = "\033[%iF%%i/%%i\033[K\033[%iE" %(ind,ind)
    for ind_taite in range(alku,loppu):
        print(muoto %(ind_taite,loppu), end='')
        sys.stdout.flush()
        harj,valid = taita_sarja([datax, datay, alat], n_taitteet, ind_taite)
        painotus = pintaalan_painotus(harj[2])
        malli.fit(harj[0], harj[1], samp_kwargs={'n':10, 'limits':painotus})
        yind1 = yind+len(valid[1])
        yhatut[yind:yind1] = malli.predict(valid[0])
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
    i=-1
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
    global ennusrajat, datax, datay, alat, tmp
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
    wetl = np.array([np.sum(datax, axis=1),]).transpose()
    datax0 = datax.copy()
    yhatut_list = np.empty(len(nimet), object)
    ehatut_list = np.empty(len(nimet), object)
    ennusrajat = np.arange(1,100,2)
    for i,nimi in enumerate(nimet):
        np.random.seed(12345)
        print("\033[92m%s\033[0m" %(nimi))
        datax = np.concatenate((datax0[:,[i]], wetl), axis=1)
        vm = Voting(linear_model.LinearRegression(), 'numpy', n_estimators=10000)
        yhatut, ehatut, aika = ristivalidointidata(vm, 8, ennusrajat, njobs=njobs)
        #print('aika = %.4f s' %aika)
        varlin = np.mean((yhatut-datay)**2)
        evarlin = np.mean((ehatut[:,2]-datay)**2)
        var = np.var(datay)
        muoto = "\033[%iF" %(njobs)
        print(muoto, end='')
        print(locale.format_string("selitetty varianssi = \033[1m%.4f\033[0m; %.4f", (1-varlin/var, 1-evarlin/var)))
        print("Arvioidun keskiarvon todellinen arvo: %.4f\n" %(massojen_suhde(yhatut,datay)), end='')
        yhatut_list[i] = yhatut
        ehatut_list[i] = ehatut
    np.savez('wetlandvuo_voting_data%s.npz' %("_tmp" if tmp else ""),
             yhatut_list=yhatut_list, ehatut_list=ehatut_list, ennusrajat=ennusrajat, nimet=nimet)
    return 0

if __name__=='__main__':
    main()

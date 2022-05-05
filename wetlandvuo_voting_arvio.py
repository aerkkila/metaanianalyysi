#!/usr/bin/python3
from sklearn import linear_model
import numpy as np
from voting_model import Voting
import wetlandvuo_data as wldata
import multiprocessing as mp
from wetlandvuo_voting import pintaalat1x1, pintaalan_painotus
import sys

def yksi_tyyppi(t_ind, nimi):
    global datax, hila, shmname
    pohjamalli = linear_model.LinearRegression()
    malli = Voting(pohjamalli, 'numpy', n_estimators=10000)
    maski = datax[:,t_ind] >= 0.03
    dtx = datax[:,[t_ind,-1]]
    malli.fit(dtx[maski], datay[maski], samp_kwargs={'n':10, 'limits':painotus[maski]})
    enn_yvot = malli.predict(enn_x)
    enn_y = pohjamalli.fit(dtx[maski],datay[maski]).predict(enn_x)
    enn_yL = malli.prediction(10)
    enn_yH = malli.prediction(90)
    print("%14s:\t%.3f\t%.3f\t%.3f\t%.3f" %(nimi, enn_yL, enn_y, enn_yvot, enn_yH))

    pit = hila.shape[0]
    hilat_shm = mp.shared_memory.SharedMemory(name=shmname)
    hilat = np.ndarray([5,4,pit], np.float32, buffer=hilat_shm.buf)
    hilat[t_ind,0,...] = pohjamalli.predict(hila)
    hilat[t_ind,1,...] = malli.predict(hila)
    hilat[t_ind,2,...] = malli.prediction(10)
    hilat[t_ind,3,...] = malli.prediction(90)
    hilat_shm.close()

def tee_hila():
    global hila
    n = 50
    x0 = np.linspace(0,1,n)
    x1 = x0
    mesh = np.meshgrid(x0,x1)
    x0 = mesh[0].reshape([n*n,1])
    x1 = mesh[1].reshape([n*n,1])
    hila = np.concatenate([x0,x1], axis=1)

def main():
    global enn_x, datax, datay, wetl, painotus, shmname
    njobs=1
    if '-j' in sys.argv:
        njobs = int(sys.argv[sys.argv.index('-j')+1])
    dt = wldata.tee_data()
    datax = dt[0]
    datay = dt[1]
    nimet = dt[2][:-1]
    lat = dt[3]
    tee_hila()
    
    alat = pintaalat1x1(lat)
    painotus = pintaalan_painotus(lat)

    enn_x = np.array([1.0,1.0]).reshape([1,2])
    prosessit = np.empty(njobs,object)
    print("%14s \t%d %%\t avg\tjoukkio\t%d %%" %("", 10, 90))

    pit = hila.shape[0]
    hilat_shm = mp.shared_memory.SharedMemory(create=True, size=pit*4*5*4) # 4 lajia, 5 tyyppiä, sizeof(float)
    shmname = hilat_shm.name
    hilat = np.ndarray([5,4,pit], np.float32, buffer=hilat_shm.buf)

    for i,nimi in enumerate(nimet):
        if(i<njobs-1):
            prosessit[i] = mp.Process(target=yksi_tyyppi, args=(i,nimi))
            prosessit[i].start()
        else:
            yksi_tyyppi(i,nimi)
    for i in range(njobs-1):
        prosessit[i].join()

    np.savez('wetlandvuo_voting_hila.npz', tulos=hilat, hila=hila)
    hilat_shm.close()
    hilat_shm.unlink()

    return 0

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

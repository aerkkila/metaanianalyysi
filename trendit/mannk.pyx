import numpy as np
from ctypes import *
import pymannkendall as fit1
#from sklearn.linear_model import TheilSenRegressor as fit2
from matplotlib.pyplot import *
import os

cdef extern from "lue.c":
    int kausia, vuosia
    struct taul:
        int vuodet[15],
        double data[4][15],
        char kausinimet[4][32],
        char lajinimi[40]
    int lue_tahan(char* muuttuja, int luok, int kosteikko, taul* dest)

muuttujat = [b"emissio", b"vuo", b"varianssi"]
variables = ["emission", "flux", "variance"]
cdef int varnum = 1

cdef taul tietue
lue_tahan(b"emissio", 1, 1, &tietue)

ydata = np.array(tietue.data)[:kausia,:vuosia]
xdata = np.array(tietue.vuodet)[:vuosia]

rcParams.update({'font.size':14})
cdef int i
xfun = np.array([0,vuosia], np.float64)

os.system("mkdir -p kuvat")
kulmak = np.empty([len(muuttujat),15], np.float32)
lajinimet = []

cdef int lajinum
for varnum in range(len(muuttujat)):
    lajinum = 0
    while True:
        for i in range(kausia):
            a = fit1.original_test(ydata[i,:])
            kulmak[varnum,lajinum] = a.slope
            plot(ydata[i,:], '.')
            plot(xfun, xfun*a.slope + a.intercept)
            nimi = "%s %s %s" %(variables[varnum],
                    tietue.lajinimi.decode('utf-8'),
                    tietue.kausinimet[i].decode('utf-8'))
            lajinimet.append(tietue.lajinimi.decode('utf-8'))
            title(nimi.replace('_', ' '))
            tight_layout()
            savefig('kuvat/%s.png' %nimi.replace(' ','_'))
            clf()
        if(lue_tahan(muuttujat[varnum], 1, 1, &tietue)):
            break
        ydata = np.array(tietue.data)[:kausia,:vuosia]
        lajinum += 1

#kulmak = kulmak[:,:lajinum]
print(kulmak)
print(lajinimet)

import numpy as np
from libc.stdio cimport *
from libc.string cimport strcpy
import pymannkendall as fit1
#from sklearn.linear_model import TheilSenRegressor as fit2
from matplotlib.pyplot import *
import os

cdef extern from "lue.c":
    int kausia_kau, kausia_vuo, vuosia
    int *vuodet
    char kohde_lajinimi[24]
    char **kohde_kausinimet;
    double* anna_data(int kausi)
    int aloita_luenta()
    int lue_seuraava(char* muuttuja)
    void poista_kausi(int)
    void luenta_olkoon(char* valinta)
    void luenta_ei(char* valinta)

cdef extern from "tulosta.c":
    struct tul_maarite:
        int nmuutt, kausia
        char* kaudet_ulos[6]
        char* muuttujat[6]
        char* variables[6]
        char latexmuutt[6]
    struct tul_jasen:
        float kulmak, parvot,
        char lajinimi[26]
    void alusta_lista(tul_maarite*, char*)
    void lopeta_lista()
    void tulosta_jasen(tul_jasen*, tul_maarite*)

cdef int tee_kuvat = 0

kuvakansio0 = 'kuvat'
kuvakansio = kuvakansio0

cdef aja():
    cdef tul_jasen tulos
    cdef int varnum, i, j
    cdef double* apudata
    xfun = np.array([0,vuosia], np.float64)
    xdata = np.empty(vuosia, np.int32)
    for i in range(vuosia):
        xdata[i] = vuodet[i]
    ydata = np.empty([vuosia], np.float64)
    listalista = []

    for varnum in range(len(muuttujat)):
        listalista.append([])
        if tee_kuvat:
            os.system("mkdir -p %s/%s" %(kuvakansio,variables[varnum]))
        while not lue_seuraava(muuttujat[varnum]):
            for i in range(kausia):
                apudata = anna_data(i)
                for j in range(vuosia):
                    ydata[j] = foo(apudata[j])
                a = fit1.original_test(ydata)
                tulos = tul_jasen(kulmak=a.slope, parvot=a.p)
                strcpy(tulos.lajinimi, kohde_lajinimi)
                if(kohde_kausinimet[i] != kaudet[i]):
                    fprintf(stderr, "\033[91mVirhe:\033[0m \"%s\" != \"%s\"\n", bytes(kohde_kausinimet[i]), bytes(kaudet[i]))
                listalista[varnum].append(tulos)

                if tee_kuvat:
                    plot(ydata, '.')
                    plot(xfun, xfun*a.slope + a.intercept)
                    nimi = "%s,%s" %(
                            kohde_kausinimet[i].decode('utf-8'),
                            kohde_lajinimi.replace(muuttujat[varnum],b'').decode('utf-8').replace('_',' ')
                            )
                    title('%s, p=%.4f' %(nimi.replace(',',', '),a.p))
                    ylabel(variables[varnum])
                    tight_layout()
                    savefig('%s/%s/%s.png' %(kuvakansio,variables[varnum],nimi.replace(' ','_')))
                    clf()
    return listalista

cdef tul_maarite maar

cpdef tulosta_listalista(listalista):
    cdef int i, k, vnum
    cdef tul_jasen jasen
    for i in range(0, len(listalista[0]), len(kaudet)):
        for vnum in range(len(muuttujat)):
            for k in range(len(kaudet)):
                a = listalista[vnum][i+k]
                jasen.kulmak = a['kulmak']
                jasen.parvot = a['parvot']
                strcpy(jasen.lajinimi, a['lajinimi'])
                tulosta_jasen(&jasen, &maar)
    return

rcParams.update({'font.size':14})

cdef tee_tulmaar():
    global maar
    cdef i
    for i in range(len(kaudet_ulos)):
        maar.kaudet_ulos[i] = kaudet_ulos[i]
    for i in range(len(muuttujat)):
        maar.muuttujat[i] = muuttujat[i]
        maar.variables[i] = bvariables[i]
        maar.latexmuutt[i] = 1
    for i in range(len(latexmuutt)):
        maar.latexmuutt[i] = latexmuutt[i]
    maar.nmuutt = len(muuttujat)
    maar.kausia = len(kaudet)

kaudet      = [b"whole_year", b"summer", b"freezing", b"winter"]
kaudet_ulos = [b'wh',b'su',b'fr',b'wi']
muuttujat   = [b"emissio", b"vuo", b"varianssi"]
variables   = ["emission", "flux", "variance"]
bvariables  = [b"emission", b"flux", b"variance"]
latexmuutt  = [1,1,0]

foo = lambda x: x

cdef int kausia = kausia_vuo
tee_tulmaar()
assert(not aloita_luenta())
listalista = aja()
alusta_lista(&maar, b"trendit0")
tulosta_listalista(listalista)
lopeta_lista()

tee_tulmaar()
luenta_olkoon(b"antro")
kuvakansio = '%s/antro' %(kuvakansio0)
assert(not aloita_luenta())
listalista = aja()
alusta_lista(&maar, b"trendit0_antro")
tulosta_listalista(listalista)
lopeta_lista()
luenta_ei(b"antro");
kuvakansio = kuvakansio0

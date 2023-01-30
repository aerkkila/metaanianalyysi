import numpy as np
from libc.stdio cimport *
from libc.string cimport strcpy
import pmk as fit1
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

cdef int tee_kuvat = os.system('[ -f tee ]') == 0

kuvakansio0 = 'kuvat'
kuvakansio = kuvakansio0

kokonais = np.zeros([5,20])

def tekeminen(ydata, xdata, i, varnum):
    cdef tul_jasen tulos
    maski = ~np.isnan(ydata)
    ynyt = ydata[maski]
    xnyt = xdata[maski]
    a = fit1.original_test(ynyt, xnyt)
    tulos = tul_jasen(kulmak=a.slope, parvot=a.p)
    strcpy(tulos.lajinimi, kohde_lajinimi)
    if(kohde_kausinimet[i] != kaudet[i]):
        fprintf(stderr, "\033[91mVirhe:\033[0m \"%s\" != \"%s\"\n", bytes(kohde_kausinimet[i]), bytes(kaudet[i]))

    if tee_kuvat and variables[varnum] != 'variance':
        plot(xnyt, ynyt, '.')
        plot(xnyt, xnyt*a.slope + a.intercept)
        nimi = "%s,%s" %(
                kohde_kausinimet[i].decode('utf-8'),
                kohde_lajinimi[kohde_lajinimi.index(b'_')+1:].decode('utf-8')
                )
        print(nimi)
        title('%s, p=%.4f' %(nimi.replace(',',', '),a.p))
        ylabel(variables[varnum])
        #xticks(range(0,11,2), labels=strxdata[::2])
        tight_layout()
        savefig('%s/%s/%s.png' %(kuvakansio,variables[varnum],nimi.replace(' ','_')))
        clf()
    return tulos

cdef aja():
    cdef int varnum, i, j
    cdef double* apudata
    xfun = np.array([0,vuosia], np.float64)
    xdata = np.empty(vuosia, np.int32)
    for i in range(vuosia):
        xdata[i] = vuodet[i]
    #strxdata = [str(a) for a in xdata]
    ydata = np.empty([vuosia], np.float64)
    listalista = []

    for varnum in range(len(muuttujat)):
        listalista.append([])
        if tee_kuvat:
            os.system("mkdir -p %s/%s" %(kuvakansio,variables[varnum]))
        while not lue_seuraava(muuttujat[varnum]):
            totalko = b"total" in kohde_lajinimi and muuttujat[varnum] == b"emissio"
            for i in range(kausia):
                apudata = anna_data(i)
                for j in range(vuosia):
                    ydata[j] = apudata[j]
                if totalko:
                    kokonais[i,:len(ydata)] += ydata
                tulos = tekeminen(ydata, xdata, i, varnum)
                listalista[varnum].append(tulos)
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

cdef int kausia = kausia_vuo
tee_tulmaar()
assert(not aloita_luenta())
listalista = aja()
alusta_lista(&maar, b"trendit0")
tulosta_listalista(listalista)
lopeta_lista()

# antrosta ei tehdä taulukkoa, joten tämä ei tuota mitään ellei kuvia tallenneta
tee_tulmaar()
luenta_olkoon(b"antro")
kuvakansio = '%s/antro' %(kuvakansio0)
assert(not aloita_luenta())
listalista = aja()
alusta_lista(&maar, b"trendit0_antro")
#tulosta_listalista(listalista)
lopeta_lista()
luenta_ei(b"antro");
kuvakansio = kuvakansio0

# bio- ja antroemissiot yhteensä
xdata = np.empty(vuosia, np.int32)
kuvakansio = '%s/yhteensä' %(kuvakansio0)
os.system('mkdir -p %s/%s' %(kuvakansio, variables[0]))
for i in range(vuosia):
    xdata[i] = vuodet[i]
for i in range(len(kaudet)):
    tekeminen(kokonais[i,:vuosia], xdata, i, 0)
kuvakansio = kuvakansio0

luenta_olkoon(b'kausi')
kaudet = kaudet[1:]
kaudet_ulos = kaudet_ulos[1:]
kausia = kausia_kau
muuttujat = [b"start", b"end", b"length"]
variables = ["start", "end", "length"]
bvariables = muuttujat

tee_tulmaar()
assert(not aloita_luenta())
listalista = aja()
alusta_lista(&maar, b"trendit0_kausi")
tulosta_listalista(listalista)
lopeta_lista()
luenta_ei(b"kausi")

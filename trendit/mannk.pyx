import numpy as np
from libc.stdio cimport *
import pymannkendall as fit1
#from sklearn.linear_model import TheilSenRegressor as fit2
from matplotlib.pyplot import *
import os

cdef extern from "lue.c":
    int kausia, vuosia, monesko_laji
    struct taul:
        int vuodet[15],
        double data[4][15],
        char kausinimet[4][32],
        char lajinimi[40]
    int lue_tahan(char* muuttuja, int luok, int kosteikko, taul* dest)
    void alusta_luenta()

kaudet = [b"whole_year", b"summer", b"freezing", b"winter"]
kaudet_ulos = [b'wh',b'su',b'fr',b'wi']
muuttujat = [b"emissio", b"vuo", b"varianssi"]
variables = ["emission", "flux", "variance"]
latexmuutt = [0,1]
cdef int varnum = 1

cdef taul tietue
alusta_luenta()

ydata = np.array(tietue.data)[:kausia,:vuosia]
xdata = np.array(tietue.vuodet)[:vuosia]

rcParams.update({'font.size':14})
cdef int i
xfun = np.array([0,vuosia], np.float64)

cdef struct Tulos:
    float kulmak, parvot,
    char* nimi

listalista = []

cdef char* csvvari(float arvo):
    return (
            b'' if 0
            else b'\033[1;91m' if arvo < 0.01
            else b'\033[94m' if arvo < 0.02
            else b'\033[92m' if arvo < 0.05
            else b''
            )

cdef char _palaute[32]
cdef char* latexluku(float arvo, float luku):
    if arvo < 0.01:
        sprintf(_palaute, "\\textbf{%.3f}", luku)
    elif arvo < 0.02:
        sprintf(_palaute, "\\textbf{(%.3f)}", luku)
    elif arvo < 0.05:
        sprintf(_palaute, "%.3f", luku)
    else:
        sprintf(_palaute, "(%.3f)", luku)
    return _palaute

cdef tulosta_lista(listalista):
    cdef FILE* csv = fopen("trendit.csv", "w")
    cdef FILE* tex = fopen("trendit.tex", "w")
    cdef int i, j, k, ntexmuutt=len(latexmuutt), nmuutt=len(muuttujat)
    cdef float luku, arvo
    assert(kausia==4)

    # latex-tiedoston alustaminen
    fprintf(tex, "\\begin{tabular}{l")
    for i in range(ntexmuutt):
        fprintf(tex, b"|")
        fprintf(tex, b"r"*kausia)
    fprintf(tex, "}\n")
    for i in range(ntexmuutt):
        fprintf(tex, " & \\multicolumn{%i}{c}{%s}", kausia, bytes(variables[latexmuutt[i]].encode('utf-8')))
    fprintf(tex, " \\\\\n");
    for i in range(ntexmuutt):
        for j in range(kausia):
            fprintf(tex, " & {%s}", bytes(kaudet_ulos[j]))
    fprintf(tex, " \\\\\n\\midrule\n")

    # csv:n alustaminen
    for i in range(nmuutt):
        fprintf(csv, ",%s", bytes(muuttujat[i]))
        fprintf(csv, b","*(kausia-1))
    fprintf(csv, '\n')
    for i in range(nmuutt):
        for j in range(kausia):
            fprintf(csv, ",%s", bytes(kaudet_ulos[j]))
    fprintf(csv, '\n')

    cdef int kausijarj[4]
    for i in range(kausia):
        for j in range(kausia):
            if kaudet[i] == listalista[0][j]['nimi'].split(b',')[0]:
                kausijarj[i] = j
                break
        else:
            printf("varoitus: %s\n", bytes(kaudet[i]))

    for k in range(0,len(listalista[0]),4):
        nimi = bytes(listalista[0][k]['nimi'].split(b',')[1])
        fprintf(csv, "%s", bytes(nimi))
        fprintf(tex, "%s", bytes(nimi))
        for j in range(nmuutt):
            latex = j in latexmuutt
            for i in range(kausia):
                luku = listalista[j][k+kausijarj[i]]['kulmak']*100
                arvo = listalista[j][k+kausijarj[i]]['parvot']
                fprintf(csv, ",%s%.3f\033[0m", csvvari(arvo), luku)
                if latex:
                    fprintf(tex, " & %s", latexluku(arvo, luku))
        fprintf(csv, "\n")
        fprintf(tex, " \\\\\n")

    fprintf(tex, "\\end{tabular}")
    fclose(tex)
    fclose(csv)

cdef int lajinum, luokitusnum
cdef Tulos tulos
cdef int tee_kuvat = 0
for luokitusnum in range(3):
    for varnum in range(len(muuttujat)):
        listalista.append([])
        lajinum = 0
        os.system("mkdir -p kuvat/%s" %variables[varnum])
        while not lue_tahan(muuttujat[varnum], luokitusnum, 0, &tietue):
            for i in range(kausia):
                a = fit1.original_test(ydata[i,:])
                if tee_kuvat:
                    plot(ydata[i,:], '.')
                    plot(xfun, xfun*a.slope + a.intercept)
                    xlabel(variables[varnum])
                nimi = "%s,%s" %(
                        tietue.kausinimet[i].decode('utf-8'),
                        tietue.lajinimi.decode('utf-8').replace('_',' ')
                        )
                tulos = Tulos(kulmak=a.slope, parvot=a.p, nimi=bytes(nimi.encode('utf-8')))
                listalista[varnum].append(tulos)
                #lajinimet.append(tietue.lajinimi.decode('utf-8'))
                if tee_kuvat:
                    title(nimi.replace(',',', '))
                    ylabel(variables[varnum])
                    tight_layout()
                    savefig('kuvat/%s/%s.png' %(variables[varnum],nimi.replace(' ','_')))
                    clf()
            ydata = np.array(tietue.data)[:kausia,:vuosia]
            lajinum += 1
        monesko_laji = 0

tulosta_lista(listalista)

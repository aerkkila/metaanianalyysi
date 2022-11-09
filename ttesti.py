#!/bin/python
import numpy as np
import luokat
from scipy.stats import t

# kaikki s-termit ovat variansseja eivätkä keskihajontoja
welch_t = lambda x1,x2,s1,s2,n1,n2: (x1 - x2) / (s1/n1 + s2/n2)**0.5
dof = lambda s1,n1,s2,n2: (s1/n1 + s2/n2)**2 / (s1**2/(n1**3-n1**2) + s2**2/(n2**3-n2**2))

tiedosto = "vuotaulukot/kahtia/wetlandvuo_post_%s_k0.csv"

f = open(tiedosto %'summer', 'r')
f.readline()
teksti = f.readline()[:-1]
a = teksti.split(',')
ind = np.empty(3, int)
ind[0] = a.index('nmol/s/m²')
ind[1] = a.index('σ²')
ind[2] = a.index('N')
f.close();

def laske(d1,d2,suure):
    tsuure = welch_t(d1[0],d2[0],d1[1],d2[1],d1[2],d2[2])
    df = dof(d1[1], d1[2], d2[1], d2[2])
    print("%.5f, %.2f (%.0f), %s" %(tsuure, df, d1[2]+d2[2], suure))
    print("\033[1m%.4f\033[0m" %(t.cdf(tsuure, df)))

def työstä_kausi(tiedosto):
    lkt = luokat.wetl[1:]
    lkt.extend(['wetland_nonprf','wetland_prf'])
    for suure in lkt:
        f = open(tiedosto, 'r')
        for rivi in f:
            a = rivi[:-1].split(',')
            if a[0] == suure:
                d1 = np.array(a)[ind].astype(np.float32) # µ, σ², N
                break
        f.close()

        f = open(tiedosto.replace('kahtia','kahtia_keskiosa'), 'r')
        for rivi in f:
            a = rivi[:-1].split(',')
            if a[0] == suure:
                d2 = np.array(a)[ind].astype(np.float32)
                break
        f.close()
        laske(d1,d2,suure)

    # koko wetland erikseen molemmilta alueilta verrattuna keskiosaan
    f = open(tiedosto.replace('kahtia','kahtia_keskiosa'), 'r')
    for rivi in f:
        a = rivi[:-1].split(',')
        if a[0] == 'wetland':
            d2 = np.array(a)[ind].astype(np.float32)
            break
    f.close()
    f = open(tiedosto, 'r')
    for suure in ['wetland_nonprf', 'wetland_prf']:
        for rivi in f:
            a = rivi[:-1].split(',')
            if a[0] == suure:
                d1 = np.array(a)[ind].astype(np.float32)
                break
        laske(d1,d2,suure+'-wetland')
    f.close()

for kausi in luokat.kaudet[1:]:
    print("\033[1;92m%s\033[0m" %kausi)
    työstä_kausi(tiedosto %kausi)

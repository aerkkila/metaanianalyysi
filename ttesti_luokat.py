#!/bin/python
import numpy as np
import luokat, sys
from scipy.stats import t

# kaikki s-termit ovat variansseja eivätkä keskihajontoja
# samat varianssit (ei käytetä)
sp = lambda s1,s2,n1,n2: (((n1-1)*s1 + (n2-1)*s2) / (n1+n2-2)) ** 0.5
equal_t = lambda x1,x2,s1,s2,n1,n2: (x1 - x2) / (sp(s1,s2,n1,n2) * (1/n1 + 1/n2))**0.5
# erit varianssit
welch_t = lambda x1,x2,s1,s2,n1,n2: (x1 - x2) / (s1/n1 + s2/n2)**0.5
dof = lambda s1,n1,s2,n2: (s1/n1 + s2/n2)**2 / (s1**2/(n1**3-n1**2) + s2**2/(n2**3-n2**2))

tiedosto0 = "vuodata/%swetlandvuo_biopost_%%s_k0.csv" %('nontemperate/'   if 'nontemperate' in sys.argv
                                                        else 'temperate/' if 'temperate'    in sys.argv
                                                        else '')
tiedosto1 = "vuodata/ikirvuo_biopost_%s_k1.csv"
tiedosto2 = "vuodata/köppenvuo_biopost_%s_k1.csv"

def lue_indeksit(tiedosto):
    f = open(tiedosto %'summer', 'r')
    f.readline()
    teksti = f.readline()[:-1]
    a = teksti.split(',')
    ind = np.empty(3, int)
    ind[0] = a.index('nmol/s/m²')
    ind[1] = a.index('σ²')
    ind[2] = a.index('N')
    f.close();
    return ind

def laske(d1, d2, eri):
    if eri:
        tsuure = welch_t(d1[0],d2[0],d1[1],d2[1],d1[2],d2[2])
        df = dof(d1[1], d1[2], d2[1], d2[2])
    else:
        tsuure = equal_t(d1[0],d2[0],d1[1],d2[1],d1[2],d2[2])
        df = d1[2]+d2[2]
    if kaksipuoleinen:
        return 1 - np.abs(0.5 - t.cdf(tsuure, df)) * 2
    else:
        return t.cdf(tsuure, df)

def lue(f, suure, inds):
    for rivi in f:
        a = rivi[:-1].split(',')
        if a[0] == suure:
            return np.array(a)[inds].astype(np.float32) # µ, σ², N
    f.seek(0)
    return lue(f, suure, inds) # Tässä on periaatteessa riski päättymättömälle rekursiolle.

def työstä_kausi(tiedosto, taul, inds):
    eri = False if 'sama' in sys.argv else True
    f = open(tiedosto, 'r')
    for j,suure1 in enumerate(luokitus):
        d1 = lue(f, suure1, inds)
        f.seek(0)

        # Jo laskettuja on turha laskea uudestaan.
        for i in range(j):
            taul[j,i] = taul[i,j] if kaksipuoleinen else 1-taul[i,j]
        #taul[j,j] = 0.5

        for i in range(j,len(luokitus)):
            d2 = lue(f, luokitus[i], inds)
            taul[j,i] = laske(d1, d2, eri)
    f.close()
    return taul

def punainen():
    sys.stdout.write('\033[91m')
def vihreä():
    sys.stdout.write('\033[92m')
def keltainen():
    sys.stdout.write('\033[93m')
def perus():
    sys.stdout.write('\033[0m')
def korosta():
    sys.stdout.write('\033[1m')

def pri(teksti):
    sys.stdout.write(teksti)

def tulosta_kivasti(taul):
    korosta()
    lev = np.empty(taul.shape[1], np.int32)
    for i in range(taul.shape[1]):
        a = luokitus[i]
        lev[i] = max([len(a)+2, 8]) # 8 = 0. + desimaalit(4) + 2
        pri('%-*s' %(int(lev[i]), a if len(a)<lev[i] else a[-lev[i]+1:]))
    perus()
    pri('\n')
    for j in range(taul.shape[0]):
        for i in range(taul.shape[1]):
            a = taul[j,i]
            vihreä() if a < 0.01 else keltainen() if a < 0.03 else punainen() if a < 0.05 else perus()
            pri('%-*.4f' %(int(lev[i]),a))
        pri('\n')
    perus()

def main():
    global luokitus, tiedosto, kaksipuoleinen
    if 'köpp' in sys.argv:
        luokitus = luokat.köpp
        tiedosto = tiedosto2
        kaksipuoleinen = 0
    elif 'ikir' in sys.argv:
        luokitus = luokat.ikir
        tiedosto = tiedosto1
        kaksipuoleinen = 0
    else:
        luokitus = luokat.wetl[1:]
        tiedosto = tiedosto0
        kaksipuoleinen = 1
    tpit = len(luokitus)
    inds = lue_indeksit(tiedosto)
    taul = np.empty([tpit,tpit], np.float32)
    for kausi in luokat.kaudet[1:]:
        print("\033[1;92m%s\033[0m" %kausi)
        työstä_kausi(tiedosto %kausi, taul, inds)
        tulosta_kivasti(taul)
        pri('\n')

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

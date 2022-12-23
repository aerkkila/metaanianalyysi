#!/bin/python
import numpy as np
import luokat, sys
from scipy.stats import t

# kaikki s-termit ovat variansseja eivätkä keskihajontoja
# samat varianssit
sp = lambda s1,s2,n1,n2: (((n1-1)*s1 + (n2-1)*s2) / (n1+n2-2)) ** 0.5
equal_t = lambda x1,x2,s1,s2,n1,n2: (x1 - x2) / (sp(s1,s2,n1,n2) * (1/n1 + 1/n2))**0.5
# erit varianssit
welch_t = lambda x1,x2,s1,s2,n1,n2: (x1 - x2) / (s1/n1 + s2/n2)**0.5
dof = lambda s1,n1,s2,n2: (s1/n1 + s2/n2)**2 / (s1**2/(n1**3-n1**2) + s2**2/(n2**3-n2**2))

tiedosto = "vuotaulukot/%swetlandvuo_post_%%s_k0.csv" %('kahtia/'               if 'pure' in sys.argv
                                                        else 'kahtia_keskiosa/' if 'mixed' in sys.argv
                                                        else '')

f = open(tiedosto %'summer', 'r')
f.readline()
teksti = f.readline()[:-1]
a = teksti.split(',')
ind = np.empty(3, int)
ind[0] = a.index('nmol/s/m²')
ind[1] = a.index('σ²')
ind[2] = a.index('N')
f.close();

def laske(d1, d2, suure1, suure2, eri):
    if eri:
        tsuure = welch_t(d1[0],d2[0],d1[1],d2[1],d1[2],d2[2])
        df = dof(d1[1], d1[2], d2[1], d2[2])
    else:
        tsuure = equal_t(d1[0],d2[0],d1[1],d2[1],d1[2],d2[2])
        df = d1[2]+d2[2]
    return t.cdf(tsuure, df)

def lue(f, suure):
    for rivi in f:
        a = rivi[:-1].split(',')
        if a[0] == suure:
            return np.array(a)[ind].astype(np.float32) # µ, σ², N
    f.seek(0)
    return lue(f, suure) # Tässä on periaatteessa riski päättymättömälle rekursiolle.

def työstä_kausi(tiedosto, taul):
    f = open(tiedosto, 'r')
    luok = luokat.wetl[1:]
    imarsh = luok.index('marsh')
    for j,suure1 in enumerate(luok):
        d1 = lue(f, suure1)
        f.seek(0)
        for i,suure2 in enumerate(luok):
            d2 = lue(f, suure2)
            eri = False if 'sama' in sys.argv else\
                  True  if 'eri'  in sys.argv else\
                  (i<=imarsh or j<=imarsh) and (i>imarsh or j>imarsh)
            taul[j,i] = laske(d1,d2,suure1,suure2, eri)
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
        a = luokat.wetl[i+1]
        lev[i] = max([len(a)+2, 8]) # 8 = 0. + desimaalit(4) + 2
        pri('%-*s' %(int(lev[i]), a if len(a)<lev[i] else a[-lev[i]+1:]))
    perus()
    pri('\n')
    for j in range(taul.shape[0]):
        for i in range(taul.shape[1]):
            a = taul[j,i]
            if a > 0.5:
                a = 1-a
            punainen() if a < 0.01 else vihreä() if a < 0.03 else keltainen() if a < 0.05 else perus()
            pri('%-*.4f' %(int(lev[i]),a))
        pri('\n')
    perus()

def main():
    tpit = len(luokat.wetl[1:])
    for kausi in luokat.kaudet[1:]:
        taul = np.empty([tpit,tpit], np.float32)
        print("\033[1;92m%s\033[0m" %kausi)
        taul = työstä_kausi(tiedosto %kausi, taul)
        tulosta_kivasti(taul)
        pri('\n')

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

#!/bin/python
import numpy as np
import luokat
from scipy.stats import t

# kaikki s-termit ovat variansseja eivätkä keskihajontoja
# samat varianssit
sp = lambda s1,s2,n1,n2: (((n1-1)*s1 + (n2-1)*s2) / (n1+n2-2)) ** 0.5
equal_t = lambda x1,x2,s1,s2,n1,n2: (x1 - x2) / (sp(s1,s2,n1,n2) * (1/n1 + 1/n2))**0.5
# erit varianssit
welch_t = lambda x1,x2,s1,s2,n1,n2: (x1 - x2) / (s1/n1 + s2/n2)**0.5
dof = lambda s1,n1,s2,n2: (s1/n1 + s2/n2)**2 / (s1**2/(n1**3-n1**2) + s2**2/(n2**3-n2**2))

tiedosto = "vuotaulukot/wetlandvuo_post_%s_k0.csv"

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
    #print("%.5f, %.2f (%.0f), %s – %s" %(tsuure, df, d1[2]+d2[2], suure1, suure2))
    #print("\033[1m%.4f\033[0m" %(t.cdf(tsuure, df)))
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
    for j,suure1 in enumerate(luokat.wetl[1:]):
        d1 = lue(f, suure1)
        f.seek(0)
        for i,suure2 in enumerate(luokat.wetl[1:]):
            d2 = lue(f, suure2)
            taul[j,i] = laske(d1,d2,suure1,suure2, i<=3 or j<=3 and i>3 or j>3)
    f.close()
    print(taul)

def main():
    np.set_printoptions(precision=4, suppress=True)
    tpit = len(luokat.wetl[1:])
    for kausi in luokat.kaudet[1:]:
        taul = np.empty([tpit,tpit], np.float32)
        print("\033[1;92m%s\033[0m" %kausi)
        työstä_kausi(tiedosto %kausi, taul)

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

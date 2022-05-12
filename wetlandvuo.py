#!/usr/bin/python3
from sklearn import linear_model as lm
from matplotlib.pyplot import *
from wetlandvuo_data import tee_data
from wetlandtyypin_pisteet import valitse_painottaen
from wetlandtyypin_pisteet_tulos import tee_maskit
import numpy as np
import pandas as pd
import sys

sarakkeet = ['kaikki 2 sel.', 'rajattu 2 sel.', 'kaikki 1 sel.', 'rajattu 1 sel.']

class R2taul():
    def __init__(self, nimet):
        self.taulukko = pd.DataFrame(index=nimet, columns=sarakkeet, dtype=np.float32)
    def laita(self, nimi_ind, yhats, ylis):
        rivi = np.empty(4, np.float32)
        for i in range(len(sarakkeet)):
            rivi[i]= 1 - np.mean((yhats[i]-ylis[i])**2) / np.var(ylis[i])
        self.taulukko.iloc[nimi_ind,:] = rivi
    def __str__(self):
        return self.taulukko.to_string()

class R2taul_yla():
    def __init__(self, nimet, osuus):
        self.taulukko = pd.DataFrame(index=nimet, columns=sarakkeet, dtype=np.float32)
        self.osuus = osuus
    def laita(self, nimi_ind, yhats, ylis):
        rivi = np.empty(4, np.float32)
        for i in range(len(sarakkeet)):
            pit = len(yhats[i]) // self.osuus
            #if(pit < 300): #eriäviä pisteitä on reilusti alle tämä johtuen valitse_painottaen-funktiosta
            #    print("Varoitus (R2taul_yla, %s): lyhyt testidatan pituus (%i)" %(self.taulukko.index[nimi_ind],pit))
            yh = np.sort(yhats[i])[-pit:]
            yl = np.sort(ylis[i])[-pit:]
            rivi[i]= 1 - np.mean((yh-yl)**2) / np.var(yl)
        self.taulukko.iloc[nimi_ind,:] = rivi
    def __str__(self):
        return self.taulukko.to_string()

def sovitukset(dtx, dty, nimet, maskit):
    malli = lm.LinearRegression()
    yhats = np.empty(4, object)
    yhdet = np.empty(4, np.float32)
    ylis = np.empty(4, object)
    r2taul = R2taul(nimet)
    r2taul_yla = R2taul_yla(nimet, 10)
    x_yksi = [[[1,1]],[[1,1]],[[1]],[[1]]]
    for i in range(len(nimet)):
        pikamaski = dtx[:,i] >= 0.03
        maski = maskit[i,:]
        xmaskit = [pikamaski,maski,pikamaski,maski]
        for j in range(len(sarakkeet)):
            if j<2:
                x = dtx[:,[i,-1]][xmaskit[j],...] # 2 selittävää
                y = dty[xmaskit[j],...]
            else:
                x = (dtx[:,[i]] / dtx[:,[-1]])[xmaskit[j],...] # 1 selittävä jaetaan wetland-osuudella
                y = (dty / dtx[:,-1])[xmaskit[j],...]
            malli.fit(x,y)
            yhats[j] = malli.predict(x)
            yhdet[j] = malli.predict(x_yksi[j])
            ylis[j] = y
        r2taul.laita(i, yhats, ylis)
        r2taul_yla.laita(i, yhats, ylis)
    print("\033[94mR²\033[0m")
    print(r2taul)
    print("\033[94mR²_10%\033[0m")
    print(r2taul_yla)
    return

def aja(jakso):
    dt = tee_data(jakso)
    dtx = dt[0]
    dty = dt[1]
    nimet = dt[2][:-1]
    lat = dt[3]
    indeksit = valitse_painottaen(lat, 10)
    dtx = dtx[indeksit,:]
    dty = dty[indeksit]
    maskit = tee_maskit(dtx,nimet)
    print("\n\033[32m%s\033[0m" %(jakso))
    sovitukset(dtx, dty, nimet, maskit)
    return

def main():
    aja('whole_year')
    aja('winter')
    aja('summer')
    aja('freezing')

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

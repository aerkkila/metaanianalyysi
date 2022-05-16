#!/usr/bin/python3
from sklearn import linear_model as lm
from matplotlib.pyplot import *
from wetlandvuo_data import tee_data
from wetlandtyypin_pisteet import valitse_painottaen, pintaalat1x1
from wetlandtyypin_pisteet_tulos import tee_maskit
from voting_model import Voting
import numpy as np
import pandas as pd
import xarray as xr
import sys

sarakkeet = ['kaikki 2 sel.', 'rajattu 2 sel.', 'kaikki 1 sel.', 'rajattu 1 sel.']
kaudet = ['whole_year', 'summer', 'freezing', 'winter']
vari1 = "\033[92m"
vari2 = "\033[94m"
vari0 = "\033[0m"

class R2taul():
    def __init__(self, nimet):
        self.taulukko = np.empty([len(nimet),len(sarakkeet)], np.float32)
    def laita(self, i, j, yhattu, y):
        self.taulukko[i,j] = 1 - np.mean((yhattu-y)**2) / np.var(y)
    def get_taulukko(self):
        return pd.DataFrame(self.taulukko*1e-12, index=nimet, columns=sarakkeet, dtype=np.float32)
    def __str__(self):
        return self.get_taulukko().to_string()

class R2taul_yla():
    def __init__(self, nimet, osuus):
        self.taulukko = pd.DataFrame(index=nimet, columns=sarakkeet, dtype=np.float32)
        self.osuus = osuus
    def laita(self, i, j, yhattu, y):
        pit = len(yhattu) // self.osuus
        yhs = np.sort(yhattu)[-pit:]
        ys = np.sort(y)[-pit:]
        self.taulukko[i,j] = 1 - np.mean((yhs-ys)**2) / np.var(ys)
    def get_taulukko(self):
        return pd.DataFrame(self.taulukko*1e-12, index=nimet, columns=sarakkeet, dtype=np.float32)
    def __str__(self):
        return self.get_taulukko().to_string()

class Summataul():
    def __init__(self, dtx, alat):
        self.taulukko = np.zeros([len(kaudet),len(sarakkeet)], np.float64)
        self.alat = alat
        self.dtx = dtx
        self.maskit = dtx >= 0.03
    def laita(self, k_ind, t_ind, s_ind, taysvuo, kauden_pit):
        if t_ind == 2:
            return # bog+fen -luokka ohitetaan, koska bog ja fen on jo otettu
        #alla 1e-3, koska pintaalat muunnetaan km² --> m² (1e6) ja ainemäärät nmol --> mol (1e-9)
        self.taulukko[k_ind,s_ind] += (np.sum(taysvuo*
                                              (self.dtx[:,t_ind]/self.dtx[:,-1]*
                                               self.alat*kauden_pit)[self.maskit[:,t_ind]])*1e-3 *
                                       (12.01+4*1.0079) * 86400)
    def get_taulukko(self):
        return pd.DataFrame(self.taulukko*1e-12, index=kaudet, columns=sarakkeet, dtype=np.float32)
    def set_data(self, dtx, alat):
        self.dtx = dtx
        self.alat= alat
        self.maskit = dtx >= 0.03
        return self
    def to_csv(self, nimi, **kwargs):
        self.get_taulukko().to_csv(nimi, **kwargs)
    def __str__(self):
        return f("taulukko:\n{self.taulukko}"
                 "\nalat:\n{self.alat}"
                 "\ndtx:\n{self.dtx}"
                 "\nmassa:\n{self.massa}")

#a/b, missä a on summa jakajaa pienempien dt:n pisteitten etäisyydestä jakajaan
#     ja b on summa kaikkien pisteitten absoluuttisista etäisyyksistä jakajaan
#     jakajan ollessa keskiarvo tämä siis palauttaa 0,5 jne.
def massojen_suhde(jakaja, dt):
    maski = dt<jakaja
    a = np.sum(jakaja[maski] - dt[maski])
    maski = ~maski
    b = a + np.sum(dt[maski] - jakaja[maski])
    return a/b

#käyttäkääni newtonin menetelmää sellaisen vakiotermin löytämiseen, että massojen suhde menee oikein
#Funktio suhde(arvaus) on aidosti monotoninen.
#Derivaatta on luullakseni vakio muuten, mutta ei-derivoituva jonkin datapisteen siirtyessä suoran toiselle puolelle
def sijoita_suoran_vakiotermi(x, y, kerr, osuus, max_steps=10000, suhteen_tarkkuus=0.001, arvaus=0, daskel=0.01):
    tarkkuus2 = suhteen_tarkkuus**2
    for i in range(max_steps):
        yhattu = arvaus + np.sum(x*kerr, axis=1)
        suhde0 = massojen_suhde(yhattu, y)
        if (suhde0-osuus)**2 <= tarkkuus2:
            return arvaus
        darvaus = daskel
        for j in range(max_steps):
            suhde1 = massojen_suhde(yhattu+darvaus, y)
            ds_per_da = (suhde1-suhde0) / darvaus
            if ds_per_da == 0:
                print("Derivaatta oli yllättäen nolla")
                darvaus *= -1.8 #suunta vaihtelee, jolloin tämä ei jumitu, vaikka arvaus olisi yli tai ali kaikista pisteistä
                continue
            arvaus += (osuus-suhde0) / ds_per_da
            break
        else:
            print("Derivaatta pysyy nollassa. Arvaus = %f; Suhde = %f; darvaus = %f" %(arvaus,suhde0,darvaus))
            return arvaus
    print("Vakiotermiä ei löytynyt. Arvaus = %f; suhde = %f" %(arvaus, suhde0))
    return arvaus

def sovitukset(dtx, dty, nimet, maskit, k_ind):
    global summataul, summataul_k, summataul_m
    malli = lm.LinearRegression()
    vmalli = Voting(lm.LinearRegression(), 100)
    yhdet = np.empty([len(nimet),len(sarakkeet)], np.float32)
    yhdet_m = np.empty([len(nimet),len(sarakkeet)], np.float32)
    yhdet_k = np.empty([len(nimet),len(sarakkeet)], np.float32)
    r2taul = R2taul(nimet)
    r2taul_yla = R2taul_yla(nimet, 10)
    x_yksi = [[[1,1]],[[1,1]],[[1]],[[1]]]
    ijpit = len(nimet)*len(sarakkeet)
    ijind = 1
    for i in range(len(nimet)):
        pikamaski = dtx[:,i] >= 0.03
        pikamaski0 = pikamaskit0[i]
        maski = maskit[i,:]
        maski0 = maskit0[i,:]
        xmaskit = [pikamaski,maski,pikamaski,maski]
        xmaskit0 = [pikamaski0,maski0,pikamaski0,maski0]
        #Tässä on jokainen eri x ja y, jotka sovitetaan.
        for j in range(len(sarakkeet)):
            if j<2:
                x = dtx[:,[i,-1]][xmaskit[j],...] # 2 selittävää
                y = dty[xmaskit[j],...]
            else:
                x = (dtx[:,[i]] / dtx[:,[-1]])[xmaskit[j],...] # 1 selittävä jaetaan wetland-osuudella
                y = (dty / dtx[:,-1])[xmaskit[j],...]
            malli.fit(x,y)
            yhattu = malli.predict(x)
            yksi = malli.predict(x_yksi[j])
            kauden_pit = kauden_pituus
            summataul.laita(k_ind, i, j, yksi, kauden_pit)
            r2taul.laita(i, j, yhattu, y)
            r2taul_yla.laita(i, j, yhattu, y)
            yhdet[i,j] = yksi
            #korkeaa ja matalaa ei oteta suoraan prosenttipisteinä, vaan tehdään ensin kommervenkkejä
            print("\r%i/%i" %(ijind,ijpit), end='')
            sys.stdout.flush()
            ijind += 1
            vmalli.fit(x,y,{'n':10})
            kert = vmalli.get_coefs()
            pisteet = np.argsort(np.mean(kert, axis=1))
            kerr_mat = kert[pisteet[len(pisteet)//10],:]
            kerr_kork = kert[pisteet[len(pisteet)//10*9],:]
            vakio_mat = sijoita_suoran_vakiotermi(x, y, kerr_mat, 0.1)
            vakio_kork = sijoita_suoran_vakiotermi(x, y, kerr_kork, 0.9)
            yksi_m = vakio_mat + np.sum(x_yksi[j]*kerr_mat)
            yksi_k = vakio_kork + np.sum(x_yksi[j]*kerr_kork)
            summataul_m.laita(k_ind, i, j, yksi_m, kauden_pit)
            summataul_k.laita(k_ind, i, j, yksi_k, kauden_pit)
            yhdet_m[i,j] = yksi_m
            yhdet_k[i,j] = yksi_k
    print('\033[K')
    print("%sR²%s" %(vari2,vari0))
    print(r2taul)
    r2taul.get_taulukko().to_csv("./wetlandvuo_tulos/r2taul_%s.csv" %(kaudet[k_ind]))
    print("%sR²_10%%%s" %(vari2,vari0))
    print(r2taul_yla)
    r2taul.get_taulukko().to_csv("./wetlandvuo_tulos/r2taul_%s.csv" %(kaudet[k_ind]))
    r2taul_yla.get_taulukko().to_csv("./wetlandvuo_tulos/r2taul_yla_%s.csv" %(kaudet[k_ind]))
    pd.DataFrame(yhdet, index=nimet, columns=sarakkeet, dtype=np.float32).\
        to_csv("./wetlandvuo_tulos/täysvuo_%s.csv" %(kaudet[k_ind]))
    pd.DataFrame(yhdet_m, index=nimet, columns=sarakkeet, dtype=np.float32).\
        to_csv("./wetlandvuo_tulos/täysvuo10_%s.csv" %(kaudet[k_ind]))
    pd.DataFrame(yhdet_k, index=nimet, columns=sarakkeet, dtype=np.float32).\
        to_csv("./wetlandvuo_tulos/täysvuo90_%s.csv" %(kaudet[k_ind]))
    return

def aja(k_ind):
    global summataul, summataul_m, summataul_k, kauden_pituus
    dt = tee_data(kaudet[k_ind])
    dtx = dt[0]
    dty = dt[1]
    nimet = dt[2][:-1]
    lat = dt[3]
    kauden_pituus = dt[4]
    #otetaan vain northern high latitudes eli lat >= 50 °N
    maski = lat >= 50
    dtx = dtx[maski,:]
    dty = dty[maski]
    lat = lat[maski]
    kauden_pituus = kauden_pituus[maski]
    alat = pintaalat1x1(lat)
    if k_ind == 0:
        summataul = Summataul(dtx, alat)
        summataul_m = Summataul(dtx, alat)
        summataul_k = Summataul(dtx, alat)
    else:
        summataul.set_data(dtx, alat) #dropna osuu eri kohtiin eri kausilla, joten tämä päivitetään
        summataul_m.set_data(dtx, alat)
        summataul_k.set_data(dtx, alat)
    indeksit = valitse_painottaen(lat, 10)
    dtx = dtx[indeksit,:]
    dty = dty[indeksit]
    maskit = tee_maskit(dtx,nimet)
    print("\n%s%s%s" %(vari1,kaudet[k_ind],vari0))
    sovitukset(dtx, dty, nimet, maskit, k_ind)
    return

def main():
    global summataul, summataul_k, summataul_m
    for k_ind in range(len(kaudet)):
        aja(k_ind)
    print('\n%sSummat (Tg)%s' %(vari1,vari0))
    print(summataul.get_taulukko())
    print('\n%sMatalat summat (Tg)%s' %(vari1,vari0))    
    print(summataul_m.get_taulukko())
    print('\n%sKorkeat summat (Tg)%s' %(vari1,vari0))
    print(summataul_k.get_taulukko())
    summataul.to_csv("./wetlandvuo_tulos/summataul.csv")
    summataul_m.to_csv("./wetlandvuo_tulos/summataul_m.csv")
    summataul_k.to_csv("./wetlandvuo_tulos/summataul_k.csv")
    return 0

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

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
#funktio suhde(arvaus) on monotoninen, mutta derivaatta voi oleskella nollassa
def sijoita_suoran_vakiotermi(x, y, kerr, osuus, max_steps=10000, suhteen_tarkkuus=0.005, arvaus=0, dvihje=0.01):
    tarkkuus2 = suhteen_tarkkuus**2
    for i in range(max_steps):
        yhattu = arvaus + np.sum(x*kerr, axis=1)
        suhde0 = massojen_suhde(yhattu, y)
        if (suhde0-osuus)**2 <= tarkkuus2:
            return arvaus
        darvaus = dvihje
        for j in range(max_steps):
            suhde1 = massojen_suhde(yhattu+darvaus, y)
            ds_per_da = (suhde1-suhde0) / darvaus
            if ds_per_da == 0:
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
    vmalli = Voting(lm.LinearRegression(), 1000)
    yhats = np.empty(4, object)
    yhdet = np.empty(4, np.float32)
    yhdet_m = np.empty(4, np.float32)
    yhdet_k = np.empty(4, np.float32)
    ylis = np.empty(4, object)
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
            kauden_pit = kauden_pituus#[xmaskit0[j],...]
            summataul.laita(k_ind, i, j, yhdet[j], kauden_pit)
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
            yhdet_m[j] = vakio_mat + np.sum(x_yksi[j]*kerr_mat)
            yhdet_k[j] = vakio_kork + np.sum(x_yksi[j]*kerr_kork)
            summataul_m.laita(k_ind, i, j, yhdet_m[j], kauden_pit)
            summataul_k.laita(k_ind, i, j, yhdet_k[j], kauden_pit)
        r2taul.laita(i, yhats, ylis)
        r2taul_yla.laita(i, yhats, ylis)
    print('\033[K')
    print("%sR²%s" %(vari2,vari0))
    print(r2taul)
    print("%sR²_10%%%s" %(vari2,vari0))
    print(r2taul_yla)
    return

#maskit0 mahdollistaisi summan laskemisen vain niistä pisteistä, jotka on sovitettu
#summa lasketaan kuitenkin kaikista pisteistä, joten maskit0 on turha
def aja(k_ind):
    global summataul, summataul_m, summataul_k, maskit0, pikamaskit0, kauden_pituus
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
    pikamaskit0 = np.empty(dtx.shape[1]-1, object)
    for i in range(len(pikamaskit0)):
        pikamaskit0[i] = dtx[:,i] >= 0.03 #kauden pituuksia ei monisteta, joten tarvitsee oman maskin
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
    maskit0 = tee_maskit(dtx, nimet)
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
    return 0

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

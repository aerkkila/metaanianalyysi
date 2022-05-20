#!/usr/bin/python3
from sklearn import linear_model as lm
import wetlandvuo_data as wld
from wetlandtyypin_pisteet import valitse_painottaen, pintaalat1x1
from wetlandtyypin_pisteet_tulos import tee_maskit
from voting_model import Voting
from multiprocessing import Process
import multiprocessing.shared_memory as shm
import numpy as np
import pandas as pd
import xarray as xr
import sys, time

kaudet = ['whole_year', 'summer', 'freezing', 'winter']
vari1 = "\033[92m"
vari2 = "\033[94m"
vari0 = "\033[0m"

class R2taul():
    def __init__(self, nimet):
        self.taulukko = None
        self.shm = None
        self.taulukko_shm = shm.SharedMemory(create=True, size=len(kaudet)*len(nimet)*4)
        self.nimet = nimet
    def liity(self):
        self.shm = shm.SharedMemory(name=self.taulukko_shm.name)
        self.taulukko = np.ndarray([len(kaudet),len(self.nimet)], np.float32, buffer=self.shm.buf)
    def poistu(self):
        self.shm.close()
    def vapauta(self):
        self.shm.close()
        self.shm.unlink()
    def laita(self, k, w, yhattu, y):
        self.taulukko[k,w] = 1 - np.mean((yhattu-y)**2) / np.var(y)
    def get_taulukko(self):
        return pd.DataFrame(self.taulukko, index=kaudet, columns=self.nimet, dtype=np.float32)
    def __str__(self):
        return self.get_taulukko().to_string()

class Summataul():
    def __init__(self):
        self.taulukko = None
        self.shm = None
        self.taulukko_shm = shm.SharedMemory(create=True, size=len(kaudet)*3*8)
        self.alat = None
        self.dtx = None
        self.maskit = None
    def liity(self):
        self.shm = shm.SharedMemory(name=self.taulukko_shm.name)
        self.taulukko = np.ndarray([len(kaudet),3], np.float64, buffer=self.shm.buf)
    def poistu(self):
        self.shm.close()
    def vapauta(self):
        self.shm.close()
        self.shm.unlink()
    def laita(self, k_ind, t_ind, pmk, taysvuo, kauden_pit):
        if t_ind == 2:
            return # bog+fen -luokka ohitetaan, koska bog ja fen on jo otettu
        #alla 1e-3, koska pintaalat muunnetaan km² --> m² (1e6) ja ainemäärät nmol --> mol (1e-9)
        self.taulukko[k_ind,pmk] += (np.sum(taysvuo*
                                              (self.dtx[:,t_ind]/self.dtx[:,-1]*
                                               self.alat*kauden_pit)[self.maskit[:,t_ind]])*1e-3 *
                                       (12.01+4*1.0079) * 86400)
    def get_taulukko(self):
        return pd.DataFrame(self.taulukko*1e-12, index=kaudet, columns=('avg','low','high'), dtype=np.float32)
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
#Funktio suhde(arvaus) on monotoninen, mutta derivaatta pysyy nollassa, kun kaikki pisteet ovat suoran yhdellä puolella
#Derivaatta on vakio muuten, mutta ei-derivoituva jonkin datapisteen siirtyessä suoran toiselle puolelle
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
    global summataul
    malli = lm.LinearRegression()
    vmalli = Voting(lm.LinearRegression(), 10000)
    yhdet = np.empty([len(nimet),3], np.float32)
    x_yksi = [[1,1,1]] if onkoprf else [[1,1]]
    ijpit = len(nimet)*1
    ijind = 1
    for w in range(len(nimet)):
        maski = dtx[:,w] >= (0.03 if not '+' in nimet[w] else 0.06)
        if onkoprf:
            x = dtx[:,[w,-2,-1]][maski,...]
        else:
            x = dtx[:,[w,-1]][maski,...]
        y = dty[maski,...]
        if k_ind == 0:
            print("\r%i/%i" %(ijind,ijpit), end='')
            sys.stdout.flush()
        malli.fit(x,y)
        yhattu = malli.predict(x)
        yksi = malli.predict(x_yksi)
        kauden_pit = kauden_pituus
        summataul.laita(k_ind, w, 0, yksi, kauden_pit)
        r2taul.laita(k_ind, w, yhattu, y)
        yhdet[w,0] = yksi
        #korkeaa ja matalaa ei oteta suoraan prosenttipisteinä, vaan tehdään ensin kommervenkkejä
        ijind += 1
        vmalli.fit(x,y,{'n':10})
        if 1: # valitaan kulmakertoimista
            kert = vmalli.get_coefs()
            pisteet = np.argsort(np.mean(kert, axis=1))
            kerr_mat = kert[pisteet[len(pisteet)//10],:]
            kerr_kork = kert[pisteet[len(pisteet)//10*9],:]
            vakio_mat = sijoita_suoran_vakiotermi(x, y, kerr_mat, 0.1)
            vakio_kork = sijoita_suoran_vakiotermi(x, y, kerr_kork, 0.9)
            yksi_m = vakio_mat + np.sum(x_yksi*kerr_mat)
            yksi_k = vakio_kork + np.sum(x_yksi*kerr_kork)
        if 0: # valitaan malli, jossa massojen osuus menee valmiiksi oikein
            # tarkemmin ajateltuna useampi malli oikealta alueelta ja niistä valitaan sopiva
            vmalli.predict(x, palauta=False)
            mr = vmalli.make_mass_relations(y)
            malli_m, sortind_m, ind_m = vmalli.get_model(10)
            malli_k, sortind_k, ind_k = vmalli.get_model(90)
            jarj = np.argsort(vmalli.mass_relations)
            mallit_m = vmalli.estimators[jarj[sortind_m-10:sortind_m+10]]
            mallit_k = vmalli.estimators[jarj[sortind_k-10:sortind_k+10]]
            #valitaan näistä se, joka osuu x:n suurilla arvoilla parhaiten dataan
            osaind = np.argsort(x[:,0])[-int(x.shape[0]/100*10):]
            paras_ms = np.inf
            paras_ks = np.inf
            for i in range(len(mallit_m)):
                suhde = massojen_suhde(mallit_m[i].predict(x[osaind,:]), y[osaind])
                if (suhde-10)**2 < paras_ms:
                    paras_ms = suhde
                    i_m = i
                suhde = massojen_suhde(mallit_k[i].predict(x[osaind,:]), y[osaind])
                if (suhde-90)**2 < paras_ks:
                    paras_ks = suhde
                    i_k = i
            malli_m = mallit_m[i_m]
            malli_k = mallit_k[i_k]
            print('\nparas_(m/k) = %.4f\t%.4f' %(paras_ms**0.5,paras_ks**0.5))
            print('sortind_m = %i\t sortind_k = %i' %(sortind_m,sortind_k))
            print('massojen suhteet: %.5f, %.5f' %(vmalli.mass_relations[ind_m], vmalli.mass_relations[ind_k]))
            yksi_m = malli_m.predict(x_yksi)
            yksi_k = malli_k.predict(x_yksi)
            kerr_mat = malli_m.coef_
            kerr_kork = malli_k.coef_
            vakio_mat = malli_m.intercept_
            vakio_kork = malli_k.intercept_
        summataul.laita(k_ind, w, 1, yksi_m, kauden_pit)
        summataul.laita(k_ind, w, 2, yksi_k, kauden_pit)
        yhdet[w,1] = yksi_m
        yhdet[w,2] = yksi_k
        paramtaul[k_ind, 0*(len(wld.nimet)-1)+w, :] = np.insert(malli.coef_, 0, malli.intercept_)
        paramtaul[k_ind, 1*(len(wld.nimet)-1)+w, :] = np.insert(kerr_mat, 0, vakio_mat)
        paramtaul[k_ind, 2*(len(wld.nimet)-1)+w, :] = np.insert(kerr_kork, 0, vakio_kork)
    if k_ind == 0:
        print('\033[K', end='')
        sys.stdout.flush()
    pd.DataFrame(yhdet, index=nimet, columns=('avg','low','high'), dtype=np.float32).\
        to_csv(uloskansio+"vuo_%s.csv" %(kaudet[k_ind]))
    return

def aja(k_ind):
    global summataul, r2taul, kauden_pituus, paramtaul
    summataul.liity()
    r2taul.liity()
    paramtaul_shm = shm.SharedMemory(name=paramtaul_shm0.name)
    paramtaul = np.ndarray([len(kaudet),(len(wld.nimet)-1)*3,3+onkoprf], np.float32, buffer=paramtaul_shm.buf)
    dt = wld.tee_data(kaudet[k_ind])
    dtx = dt[0]
    dty = dt[1]
    nimet = dt[2][:-1]
    lat = dt[3]
    kauden_pituus = dt[4]
    dropmaski = dt[5]
    #otetaan vain northern high latitudes eli lat >= 50 °N
    maski = lat >= 50
    dtx = dtx[maski,:]
    if onkoprf:
        prf = xr.open_dataset('./prfdata_avg.nc')['osuus'].sel({"lat":slice(29.5,83.5)}).data
        dtx = np.insert(dtx, -1, prf.flatten()[dropmaski][maski], axis=1)
    dty = dty[maski]
    lat = lat[maski]
    kauden_pituus = kauden_pituus[maski]
    alat = pintaalat1x1(lat)
    summataul.set_data(dtx, alat) #dropna osuu eri kohtiin eri kausilla, joten tämä päivitetään
    indeksit = valitse_painottaen(lat, 10)
    dtx = dtx[indeksit,:]
    dty = dty[indeksit]
    maskit = tee_maskit(dtx,nimet)
    sovitukset(dtx, dty, nimet, maskit, k_ind)
    summataul.poistu()
    r2taul.poistu()
    paramtaul_shm.close()
    return

def main():
    global summataul, r2taul, onkoprf, uloskansio, paramtaul_shm0
    onkoprf = ('-prf' in sys.argv)
    uloskansio = "wetlandvuo_tulos/"
    if onkoprf:
        uloskansio += "prf_"
    summataul = Summataul()
    r2taul = R2taul(wld.nimet[:-1])
    paramtaul_shm0 = shm.SharedMemory(create=True, size=len(kaudet)*(len(wld.nimet)-1)*(3+onkoprf)*3*4)
    if '--debug' in sys.argv:
        aja(0)
        r2taul.vapauta()
        return 0
    prosessit = np.empty(len(kaudet), object)
    for k_ind in range(len(kaudet)):
        prosessit[k_ind] = Process(target=aja, args=[k_ind])
        prosessit[k_ind].start()
    for i in range(len(kaudet)):
        prosessit[i].join()
    summataul.liity()
    r2taul.liity()
    print('\n%sSummat (Tg)%s' %(vari1,vari0))
    print(summataul.get_taulukko())
    summataul.to_csv(uloskansio+"summataul.csv")
    summataul.vapauta()
    r2taul.get_taulukko().to_csv(uloskansio+"r2taul.csv")
    r2taul.vapauta()
    paramtaul = np.ndarray([len(kaudet),(len(wld.nimet)-1)*3,3+onkoprf], np.float32, buffer=paramtaul_shm0.buf)
    indeksit = np.empty(paramtaul.shape[1], object)
    pit = paramtaul.shape[1]//3
    for i in range(3):
        paate = ['','_m','_k'][i]
        for j in range(pit):
            indeksit[pit*i+j] = wld.nimet[j] + paate
    if onkoprf:
        sarakkeet = ['vakio','tyyppi','prf','wtl']
    else:
        sarakkeet = ['vakio','tyyppi','wtl']
    for k in range(len(kaudet)):
        df = pd.DataFrame(paramtaul[k,...], index=indeksit, columns=sarakkeet)
        df.to_csv(uloskansio + 'parametrit_%s.csv' %(kaudet[k]))
    paramtaul_shm0.close()
    paramtaul_shm0.unlink()
    return 0

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

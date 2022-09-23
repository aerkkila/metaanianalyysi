#!/usr/bin/python3
from sklearn import linear_model as lm
from multiprocessing import Process
import multiprocessing.shared_memory as shm
from netCDF4 import Dataset
import numpy as np
import pandas as pd
import sys, time
import luokat as Luokat

kaudet = ['whole_year', 'summer', 'freezing', 'winter']
väri1 = "\033[92m"
väri2 = "\033[94m"
väri0 = "\033[0m"

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

def sovitukset(dtx, dty, k_ind):
    global summataul
    malli = lm.LinearRegression()
    #vmalli = Voting(lm.LinearRegression(), 10000)
    yhdet = np.empty([len(nimet),3], np.float32)
    x_yksi = [[1,1,1]] if onkoprf else [[1,1]]
    ijpit = len(nimet)*1
    ijind = 1
    for w in range(len(Luokat.wetl)-1):
        maski = dtx[:,0] >= (0.03 if not '+' in nimet[w] else 0.06)
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
        #ijind += 1
        #vmalli.fit(x,y,{'n':10})
        #summataul.laita(k_ind, w, 1, yksi_m, kauden_pit)
        #summataul.laita(k_ind, w, 2, yksi_k, kauden_pit)
        #yhdet[w,1] = yksi_m
        #yhdet[w,2] = yksi_k
        #paramtaul[k_ind, 0*(len(wld.nimet)-1)+w, :] = np.insert(malli.coef_, 0, malli.intercept_)
        #paramtaul[k_ind, 1*(len(wld.nimet)-1)+w, :] = np.insert(kerr_mat, 0, vakio_mat)
        #paramtaul[k_ind, 2*(len(wld.nimet)-1)+w, :] = np.insert(kerr_kork, 0, vakio_kork)

    if k_ind == 0:
        print('\033[K', end='')
        sys.stdout.flush()
    pd.DataFrame(yhdet, index=nimet, columns=('avg','low','high'), dtype=np.float32).\
        to_csv(uloskansio+"vuo_%s.csv" %(kaudet[k_ind]))
    return

size_param = (len(kaudet)-1)*(len(Luokat.wetl)-1)*2 #*3 # 2 parametria, 0HL

def aja(k_ind):
    global summataul, r2taul, kauden_pituus, paramtaul
    summataul.liity()
    r2taul.liity()
    paramtaul_shm = shm.SharedMemory(name=paramtaul_shm0.name)
    paramtaul = np.ndarray([size_param], np.float32, buffer=paramtaul_shm.buf)

    s = Dataset('flux1x1.nc', 'r')
    vuo = np.ma.getdata(s['flux_bio_posterior'][:])
    vuo = vuo.reshape([vuo.shape[0], np.product(vuo.shape[1:])])
    vuo_t0 = pd.Timestamp(s['time'].units.split('days since ')[1])
    s.close()
    s = Dataset('BAWLD1x1.nc', 'r')
    kost = np.empty(len(Luokat.wetl), object)
    for i,l in enumerate(Luokat.wetl):
        kost[i] = np.ma.getdata(s[l][:]).flatten()
    s.close()
    s = Dataset('kaudet2.nc', 'r')
    kaudet = np.ma.getdata(s['kausi'][:])
    kaudet = kaudet.reshape([kaudet.shape[0], np.product(kaudet.shape[1:])])
    kau_t0 = pd.Timestamp(s['time'].units.split('days since ')[1])
    s.close()

    # yhdennetään ajat
    ero = (vuo_t0 - kau_t0).days
    if ero > 0:
        kaudet = kaudet[ero:, ...]
    elif ero < 0:
        vuo = vuo[-ero:, ...]

    for i in range(1,len(Luokat.wetl)):
        kost[i] /= kost[0]

    #summataul.set_data(aaaaaaa, alat) #dropna osuu eri kohtiin eri kausilla, joten tämä päivitetään
    #sovitukset(dtx, dty, nimet, maskit, k_ind)

    summataul.poistu()
    r2taul.poistu()
    paramtaul_shm.close()
    return

def main():
    global summataul, r2taul, onkoprf, uloskansio, paramtaul_shm0
    #onkoprf = ('-prf' in sys.argv)
    uloskansio = "wetlandvuo_tulos/"
    summataul = Summataul()
    r2taul = R2taul(Luokat.wetl[1:])
    paramtaul_shm0 = shm.SharedMemory(create=True, size=size_param*4)
    if '--debug' in sys.argv:
        aja(1)
        r2taul.vapauta()
        summataul.vapauta()
        paramtaul_shm0.close()
        paramtaul_shm0.unlink()
        return 0
    prosessit = np.empty(len(kaudet), object)
    for k_ind in range(len(kaudet)):
        prosessit[k_ind] = Process(target=aja, args=[k_ind])
        prosessit[k_ind].start()
    for i in range(len(kaudet)):
        prosessit[i].join()
    summataul.liity()
    r2taul.liity()
    print('\n%sSummat (Tg)%s' %(väri1,väri0))
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

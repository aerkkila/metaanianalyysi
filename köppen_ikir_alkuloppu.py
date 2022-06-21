#!/usr/bin/python3
import sys
import numpy as np
import luokat
import xarray as xr
import pandas as pd
from matplotlib.pyplot import *
from multiprocessing import Process

tarkk = 10
prajat_alku = [-115, 55]
prajat_loppu = [-10, 220]
paivarajat = [prajat_alku, prajat_loppu]
resol = 19800
al_muut = ['talven_alku','talven_loppu']
al_nimi = ['start','end']
tallenna = False

def piirra(rajat, maarat, ind_ikir, xnimiot, al_ind, ftnum):
    leveys = 0.8*tarkk/maarat.shape[1]
    for i in range(maarat.shape[1]):
        siirto = (i+0.5)*leveys
        bar(rajat+siirto, maarat[ind_ikir,i,:]/1000, label=luokat.kopp[i], width=leveys)
        title(luokat.ikir[ind_ikir])
        ylabel("Extent (1000 km$^2$)")
        xlabel("winter %s, data %i" %(al_nimi[al_ind], ftnum))
        xticks(rajat, xnimiot, rotation=30)
    legend(loc='upper right')
    tight_layout()
    if tallenna:
        savefig("kuvia/yksittäiset/köppen_w%s_ikir%i_ft%i.png" %(al_nimi[al_ind], ind_ikir, ftnum))
        clf()
    else:
        show()

def aja(kopp, alat, ikir, ftnum):
    for al_ind in range(2):
        minp,maxp = paivarajat[al_ind]
        maarat = np.zeros([len(luokat.ikir),len(luokat.kopp),(maxp-minp)//tarkk])
        paiv = xr.open_dataset("./kausien_pituudet%i.nc" %ftnum).sel({"vuosi":slice(2012,2018)})[al_muut[al_ind]]
        paiv = paiv.data.flatten()
        vuosia = paiv.size//resol

        for ind_ikir in range(len(luokat.ikir)):
            print("\033[%iF%i/%i\033[%iE\033[K" %(ftnum+1, al_ind*len(luokat.ikir)+ind_ikir+1, 2*len(luokat.ikir), ftnum+1), end='')
            sys.stdout.flush()
            for ind_kopp in range(maarat.shape[1]):
                # Tässä lasketaan ensin montako kelvollista vuotta on kussakin pisteessä.
                # Sitten jaetaan pisteen pinta-ala oikeisiin luokkiin
                for i in range(resol):
                    summa = 0
                    for v in range(vuosia):
                        ind = i+v*resol
                        if ikir[ind]==ind_ikir and kopp[ind_kopp,ind] and paiv[ind]>=minp and paiv[ind] < maxp:
                            summa += 1
                    if summa:
                        ala = alat[ind] / summa
                        for v in range(vuosia):
                            ind = i+v*resol
                            if ikir[ind]==ind_ikir and kopp[ind_kopp,ind] and paiv[ind]>=minp and paiv[ind] < maxp:
                                ind_luok = int((paiv[ind]-minp))//tarkk
                                maarat[ind_ikir,ind_kopp,ind_luok] += ala

        rajat = np.arange(minp,maxp,tarkk)
        xnimiot = pd.to_datetime(rajat, unit='D').strftime("%m/%d")
        for ind_ikir in range(maarat.shape[0]):
            piirra(rajat, maarat, ind_ikir, xnimiot, al_ind, ftnum)

def main():
    global tallenna
    rcParams.update({'figure.figsize':(12,10), 'font.size':16})
    if '-s' in sys.argv:
        tallenna = True
    kopp = np.load("./köppenmaski.npy")
    alat = np.load("./pintaalat.npy")
    ikir = np.load("./ikirdata_2009_2018.npy")
    ikir = ikir[(2012-2009)*resol : (2018+1-2009)*resol]
    kopp = np.tile(kopp, 2018-2012+1)
    alat = np.tile(alat, 2018-2012+1)
    pr = np.empty(3,object)
    print('\n'*3, end='')
    sys.stdout.flush()
    for i in range(3):
        pr[i] = Process(target=aja, args=(kopp, alat, ikir, i))
        pr[i].start()
    for p in pr:
        p.join()

if __name__=='__main__':
    main()

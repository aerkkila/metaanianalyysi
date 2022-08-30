#!/usr/bin/python3
import xarray as xr
import numpy as np
from matplotlib.pyplot import *
import pandas as pd
import sys, luokat
from valitse_painottaen import valitse_painottaen
from multiprocessing import Process
from laatikkokuvaaja import laatikkokuvaaja

bawlajit = ['boreal_forest', 'bog', 'fen', 'marsh', 'tundra_wetland', 'permafrost_bog', 'tundra_dry']
alm = ['talven_alku', 'talven_loppu']
aln = ['start', 'end']
kerroin = 8
resol = 19800

def tee_luokat(luokittelu, kausidata, indeksit, lajit, alind, ftnum):
    vuosia = len(kausidata.vuosi)
    lista = np.empty(len(lajit),object)
    tiednimi = '%slaatikkodata/alind%i_ftnum%i.npz' %('köppen' if koppen else 'baw', alind, ftnum)
    for nolla in [0]: # Mahdollistaa break-komennon käytön goto:n tapaan.
        if ei_muistista:
            break
        try:
            tmp = np.load(tiednimi)
        except OSError:
            break
        lista[:] = [tmp[_nimio] for _nimio in tmp]
        tmp.close()
        return lista
    kausimuuttuja = alm[alind]
    if koppen:
        for i,laji in enumerate(lajit):
            data = np.empty(int(np.ceil(resol*vuosia*kerroin)), np.float32)
            dind = 0
            for v in range(vuosia):
                paivat = kausidata[kausimuuttuja].data[v,...].flatten()[indeksit]
                for p in range(resol):
                    if luokittelu[i,p]:
                        data[dind] = paivat[p]
                        dind += 1
            lista[i] = data[0:dind][~np.isnan(data[0:dind])].astype(np.int16)
    else:
        for i,laji in enumerate(lajit):
            painot = (luokittelu[i,:]*100).astype(np.int8)[indeksit]
            keskiosuus = np.mean(painot)
            data = np.empty(int(np.ceil(resol*vuosia*keskiosuus*kerroin)), np.float32)
            dind = 0
            for v in range(vuosia):
                paivat = kausidata[kausimuuttuja].data[v,...].flatten()[indeksit]
                # paivat ja painot on laajennettu indekseillä
                for p in range(resol*kerroin):
                    dind1 = dind + painot[p]
                    data[dind:dind1] = paivat[p] # kyseistä päivää toistetaan baw-luokan prosenttien verran
                    dind = dind1
            lista[i] = data[~np.isnan(data)].astype(np.int16)
    np.savez(tiednimi, *lista)
    return lista

def kuva(luokittelu, alind, ftnum):
    kausidata = xr.open_dataset("kausien_pituudet%i.nc" %ftnum).sel({'vuosi':slice(2012,2018)})
    indeksit  = valitse_painottaen(kausidata.lat.data, kausidata.lon.data, kerroin)
    lajit     = luokat.kopp if koppen else bawlajit
    lista     = tee_luokat(luokittelu, kausidata, indeksit, lajit, alind, ftnum)
    kausidata.close()
    järj = np.array([np.median(lis) for lis in lista]).argsort() # järjestetään laatikot mediaanin mukaan
    if alind:
        järj = järj[::-1]
    lista = lista[järj]
    grid(True, axis='y')
    tulos = laatikkokuvaaja(lista, fliers=' ')
    xnimet = np.array(lajit, object)[järj]
    #joka toinen sarake alemmalle riville
    for i,x in enumerate(xnimet):
        if i%2:
            xnimet[i] = '\n'+x
    xticks(tulos['xsij'], xnimet)
    ylabel('winter %s, data %i' %(aln[alind],ftnum))
    if(alind==0): #talven alku
        ylims = [-110,50]
        ylim(ylims)
    else: # talven loppu
        ylims = [10,175]
        ylim(ylims)
    ytikit = np.arange(*ylims,15)
    ajat = pd.to_datetime(ytikit, unit='D')
    yticks(ytikit, labels=ajat.strftime("%m-%d"))
    tight_layout()
    if(tallenna):
        savefig('kuvia/yksittäiset/%s_laatikko_w%s_ft%i.png' %('köppen' if koppen else 'bawld', aln[alind], ftnum))
        clf()
    else:
        show()

def aja(luokittelu, ftnum):
    try:
        for alind in range(2):
            kuva(luokittelu, alind, ftnum)
    except KeyboardInterrupt:
        return

def main():
    global ei_muistista, tallenna, koppen
    ei_muistista = True if '-e' in sys.argv else False
    tallenna     = True if '-s' in sys.argv else False
    debug        = True if '-d' in sys.argv else False
    koppen       = True if '-k' in sys.argv else False
    rcParams.update({'figure.figsize':(8,11), 'font.size':16})
    if koppen:
        luokittelu = np.load("köppenmaski.npy")
    else:
        baw = xr.open_dataset("BAWLD1x1.nc")
        luokittelu = np.empty([len(bawlajit),resol], np.float32)
        for i,laji in enumerate(bawlajit):
            luokittelu[i,:] = baw[laji].data.flatten()
    if debug:
        aja(luokittelu,0)
        return
    pr = np.empty(3,object)
    for i in range(3):
        pr[i] = Process(target=aja, args=[luokittelu, i])
        pr[i].start()
    for p in pr:
        p.join()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')

#!/usr/bin/python3
import xarray as xr
import numpy as np
from matplotlib.pyplot import *
import sys, warnings
from valitse_painottaen import valitse_painottaen
from multiprocessing import Process
from laatikkokuvaaja import laatikkokuvaaja

bawlajit = ['boreal_forest', 'bog', 'fen', 'marsh', 'tundra_wetland', 'permafrost_bog', 'tundra_dry']
alm = ['talven_alku', 'talven_loppu']
aln = ['start', 'end']
kerroin = 8

def tee_luokat(kausidata, indeksit, alind, ftnum):
    resol = baw.bog.data.flatten().size
    vuosia = len(kausidata.vuosi)
    lista = np.empty(len(bawlajit),object)
    tiednimi = 'bawlaatikkodata/alind%i_ftnum%i.npz' %(alind,ftnum)
    for nolla in [0]: # Mahdollistaa break-komennon käytön goto:n tapaan. Oispa goto.
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
    for i,laji in enumerate(bawlajit):
        painot = (baw[laji].data.flatten()*100).astype(np.int8)[indeksit]
        keskiosuus = np.mean(painot)
        data = np.empty(int(np.ceil(resol*vuosia*keskiosuus*kerroin)), np.float32)
        print("%i/%i" %(i+1,len(bawlajit)))
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

def kuva(alind,ftnum):
    kausidata = xr.open_dataset("kausien_pituudet%i.nc" %ftnum).sel({'vuosi':slice(2012,2018)})
    indeksit = valitse_painottaen(kausidata.lat.data, kausidata.lon.data, kerroin)
    lista = tee_luokat(kausidata, indeksit, alind, ftnum)
    kausidata.close()
    jarj = np.array([np.median(lis) for lis in lista]).argsort() # järjestetään laatikot mediaanin mukaan
    if alind:
        jarj = jarj[::-1]
    lista = lista[jarj]
    grid(True, axis='y')
    laatikkokuvaaja(lista, fliers=' ')
    xnimet = np.array(bawlajit)[jarj]
    #joka toinen sarake alemmalle riville
    for i,x in enumerate(xnimet):
        if i%2:
            xnimet[i] = '\n'+x
    gca().set_xticklabels(xnimet)
    ylabel('winter %s, data %i' %(aln[alind],ftnum))
    if(alind==0): #talven alku
        ylim([-110,50])
    else: # talven loppu
        ylim([25,175])
    tight_layout()
    if('-s' in sys.argv):
        savefig('kuvia/yksittäiset/bawld_laatikko_w%s_ft%i.png' %(aln[alind],ftnum))
        clf()
    else:
        show()

def aja(ftnum):
    for alind in range(2):
        kuva(alind,ftnum)

def main():
    global baw, ei_muistista
    ei_muistista = True if '-e' in sys.argv else False
    rcParams.update({'figure.figsize':(8,11), 'font.size':16})
    baw = xr.open_dataset("BAWLD1x1.nc")
    pros = np.empty(3,object)
    for i in range(3):
        pros[i] = Process(target=aja, args=[i])
        pros[i].start()
    for p in pros:
        p.join()

if __name__=='__main__':
    main()

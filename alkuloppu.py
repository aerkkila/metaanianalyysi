#!/usr/bin/python3
import numpy as np
import xarray as xr
from numpy import sin
from matplotlib.pyplot import *
from multiprocessing import Process

def argumentit():
    global tallenna, tarkk, verbose
    tallenna=False; tarkk=2; verbose=False
    i = 1
    while i < len(sys.argv):
        a = sys.argv[i]
        if a == '-s':
            tallenna = True
        elif a == '-v':
            verbose = True
        elif a == 'start' or a == 'end':
            startend = a
        elif a == '-t' or a == '--tarkkuus':
            i += 1
            tarkk = int(sys.argv[i])
        else:
            print("Varoitus: tuntematon argumentti \"%s\"" %a)
        i += 1
    return

# Diskretisoi darr-DataArrayn tarkk-tarkkuudella ja
# laskee paljonko pinta-alaa on kullakin syntyneellä osuudella.
def pintaalat1x1(kokodata,darr,tarkk):
    aste = 0.0174532925199
    R2 = 40592558970441
    PINTAALA = lambda _lat: aste*R2*(sin((_lat+1)*aste) - sin(_lat*aste))*1.0e-6
    
    dat = darr.data.flatten().astype(int)
    minluku = int(kokodata.min())
    maxluku = int(kokodata.max())
    lukualat = np.zeros( (maxluku - minluku) // tarkk + 1 )
    for j,la in enumerate(darr.lat.data):
        ala = PINTAALA(la)
        lonarr = dat[ j*darr.lon.size : (j+1)*darr.lon.size ]
        lonarr = lonarr[lonarr >= minluku]
        for luku in lonarr.astype(int):
            lukualat[(luku-minluku)//tarkk] += ala
    return np.arange(minluku,maxluku+1,tarkk), lukualat

al_muuttuja = ['talven_alku','talven_loppu']
al_nimi = ['start','end']

def aja(doy,ftnum):
    global xarrlis, yarrlis, paivat, palkit, aln
    for alm, aln in zip(al_muuttuja, al_nimi):
        paivat = doy[alm]
        xarrlis,yarrlis = pintaalat1x1(paivat, paivat, tarkk)

        fig = figure()
        palkit = bar(xarrlis, yarrlis/1000, width=0.8*tarkk)
        xlabel('winter %s, data %i' %(aln,ftnum))
        ylabel('extent (1000 km$^2$)')
        tight_layout()
        if aln[0] == 's':
            xlim([-110,75])
        else:
            xlim([-20,180])
        if not tallenna:
            show()
            continue
        savefig("kuvia/yksittäiset/ikir%i_w%s_ft%i.png" %(ikir_ind,aln,ftnum))

def main():
    rcParams.update({'font.size':19,'figure.figsize':(12,10)})
    argumentit()
    kerroin = 8
    ftluvut = [0,1,2]
    pros = np.empty(len(ftluvut),object)
    for i,l in enumerate(ftluvut):
        doy = xr.open_dataset("kausien_pituudet%i.nc" %l)[al_muuttuja].mean(dim='vuosi')
        pros[i] = Process(target=aja, args=[doy,l])
        pros[i].start()
    for p in pros:
        p.join()

if __name__ == '__main__':
    main()

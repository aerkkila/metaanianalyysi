#!/usr/bin/python3
import numpy as np
import xarray as xr
from numpy import sin
import pandas as pd
from matplotlib.pyplot import *
import sys, luokat, maalajit

# laskee paljonko pinta-alaa on kullakin xjaon osuudella (km²).
# xjaon on oltava tasavälinen
# Jos tyyppi on dataframe, tämä on hirvittävän hidas. Olkoon tyyppi numpy-array.
def pintaalat1x1(paivat,lat,lon,xjako):
    aste = 0.0174532925199
    R2 = 40592558970441
    PINTAALA = lambda _lat: aste*R2*( sin((_lat+1)*aste) - sin(_lat*aste) )*1.0e-6
    
    lukualat = np.zeros(len(xjako))
    tarkk = xjako[1]-xjako[0]
    minluku = xjako[0]
    for j,la in enumerate(lat):
        ala = PINTAALA(la)
        x_rantu = paivat[ j*lon.size : (j+1)*lon.size ]
        maski = x_rantu >= minluku #onko tämä nan-poistaja?
        x_rantu = x_rantu[maski]
        for i,luku in enumerate(x_rantu.astype(int)):
            lukualat[(luku-minluku)//tarkk] += ala
    return lukualat

def luo_xjako(dt,tarkk,luokat2):
    minluku = int(999999999)
    maxluku = int(-999999999)
    for luok in luokat2:
        d = dt[luok]
        print(d)
        try:
            minluku = min(minluku,int(np.nanmin(d)))
            maxluku = max(maxluku,int(np.nanmax(d)))
        except:
            continue # Tällöin taulukon d kaikki jäsenet olivat epälukuja. Kyse ei ole virheestä.
    return np.arange(minluku,maxluku+1,tarkk)

def tee_luokka(xtaul,ytaul,dflista,dfind,luokat2,tarkk,pa_kerr=None):
    xtaul[dfind] = luo_xjako(dflista[dfind], tarkk, luokat2)
    for i,mluok in enumerate(luokat2):
        tmp = dflista[dfind]
        ytaul[dfind,i] = pintaalat1x1(np.array(tmp[mluok]), np.array(tmp.lat), np.array(tmp.lon), xtaul[dfind])

def argumentit(argv):
    global tallenna,verbose
    tallenna = False; verbose = False; maa_vai_koppen = False
    for a in argv:
        if a == '-s':
            tallenna = True
        elif a == '-v':
            verbose = True

def piirra(xtaul,ytaul):
    leveys = 0.8*tarkk/len(luokat2)
    for i,mluok in enumerate(luokat2):
        isiirto = i*leveys+0.5*leveys
        palkit = bar( xtaul[ikir_ind]+isiirto, ytaul[ikir_ind,i]/1000, width=leveys, label=mluok )

def viimeistele(kumpi):
    ylabel('Extent (1000 km$^2$)')
    xlabel('winter %s day' %startend[kumpi])
    ajat = pd.to_datetime(xtaul[kumpi,ikir_ind],unit='D')
    xticks(xtaul[kumpi,ikir_ind],labels=ajat.strftime("%m/%d"),rotation=30)
    title(luokat.ikir[ikir_ind])
    tight_layout()
    legend()

def tee_kuva(df, luokat_w, tarkk):
    xjako = luo_xjako(df,tarkk,luokat_w)
    print(xjako)
    print(len(xjako))

def main():
    luokat_w = ['bog','fen','tundra_wetland','permafrost_bog']
    tarkk = 1e-8
    argumentit(sys.argv[1:])
    rcParams.update({'font.size':13,'figure.figsize':(16,8)})
    ds = xr.open_dataset('./BAWLD1x1.nc')
    df = ds.to_dataframe().reset_index()
    tee_kuva(df, luokat_w, tarkk)

    if tallenna:
        while True:
            if verbose:
                print(luokat.ikir[ikir_ind])
            savefig("kuvia/%s%s%i.png"
                    %(sys.argv[0][:-3], ('_'+startend[0] if len(startend)==1 else ''), ikir_ind))
            if ikir_ind==len(luokat.ikir)-1:
                exit()
            vaihda_luokat(1)
        return
    show()
    return

if __name__ == '__main__':
    main()

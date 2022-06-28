#!/usr/bin/python3
import numpy as np
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

def pintaalat1x1_kerr(paivat,lat,lon,xjako,kerr):
    aste = 0.0174532925199
    R2 = 40592558970441
    PINTAALA = lambda _lat: aste*R2*( sin((_lat+1)*aste) - sin(_lat*aste) )*1.0e-6
    
    lukualat = np.zeros(len(xjako))
    tarkk = xjako[1]-xjako[0]
    minluku = xjako[0]
    for j,la in enumerate(lat):
        ala = PINTAALA(la)
        x_rantu = paivat[j*lon.size : (j+1)*lon.size]
        kertoimet = kerr[j*lon.size : (j+1)*lon.size]
        maski = x_rantu >= minluku
        x_rantu = x_rantu[maski]
        kertoimet = kertoimet[maski]
        for i,luku in enumerate(x_rantu.astype(int)):
            lukualat[(luku-minluku)//tarkk] += ala*kertoimet[i]
    return lukualat

def luo_xjako(dt,tarkk,luokat2):
    minluku = int(999999999)
    maxluku = int(-999999999)
    for luok in luokat2:
        d = dt[luok]
        try:
            minluku = min(minluku,int(np.nanmin(d)))
            maxluku = max(maxluku,int(np.nanmax(d)))
        except:
            continue # Tällöin taulukon d kaikki jäsenet olivat epälukuja. Kyse ei ole virheestä.
    return np.arange(minluku,maxluku+1,tarkk)

def tee_luokka(xtaul,ytaul,dflista,dfind,luokat2,tarkk,pa_kerr=None):
    xtaul[dfind] = luo_xjako(dflista[dfind], tarkk, luokat2)
    if pa_kerr is None:
        for i,mluok in enumerate(luokat2):
            tmp = dflista[dfind]
            ytaul[dfind,i] = pintaalat1x1(np.array(tmp[mluok]), np.array(tmp.lat), np.array(tmp.lon), xtaul[dfind])
        return
    for i,mluok in enumerate(luokat2):
        tmp = dflista[dfind]
        ytaul[dfind,i] = pintaalat1x1_kerr(np.array(tmp[mluok]), np.array(tmp.lat), np.array(tmp.lon), xtaul[dfind], pa_kerr[mluok].to_numpy())

global luokat2
startend = ['start','end']
ikir_ind = 0

def argumentit(argv):
    global tallenna,verbose,maa_vai_koppen
    tallenna = False; verbose = False; maa_vai_koppen = False
    for a in argv:
        if a == '-s':
            tallenna = True
        elif a == '-v':
            verbose = True
        elif a == 'maa' or a == 'köppen':
            maa_vai_koppen = a

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

def vaihda_luokka(hyppy,kumpi):
    global ikir_ind
    ikir_ind = ( ikir_ind + len(luokat.ikir) + hyppy ) % len(luokat.ikir)
    if xtaul[kumpi,ikir_ind] is None:
        tee_luokka(xtaul[kumpi,...], ytaul[kumpi,...], dflista=doydflis[kumpi,...],
                   dfind=ikir_ind, luokat2=luokat2, tarkk=tarkk, pa_kerr=osuuslis[ikir_ind])
    gca().clear()
    piirra(xtaul[kumpi,...],ytaul[kumpi,...])
    viimeistele(kumpi)
    draw()

def vaihda_luokat(hyppy):
    for i in range(len(startend)):
        sca(axs[i])
        vaihda_luokka(hyppy,i)
        hyppy = 0 #toisella kierroksella ikir_ind on jo vaihdettu

def nappainfunk(tapaht):
    if tapaht.key == 'right' or tapaht.key == 'o' or tapaht.key == 'i':
        vaihda_luokat(1)
    elif tapaht.key == 'left' or tapaht.key == 'g' or tapaht.key == 'a':
        vaihda_luokat(-1)
    return

def data_maa():
    global tarkk,doydflis,osuuslis,xtaul,ytaul,luokat2
    luokat2 = ['boreal_forest','tundra_dry','tundra_wetland+\npermafrost_bog','bog+fen']
    tarkk = 15
    lse = len(startend)
    #DOY-data
    doydflis = np.empty([lse,len(luokat.ikir)],object)
    for j in range(lse):
        for i in range(doydflis.shape[1]):
            doydflis[j,i] = maalajit.nimen_jako(pd.read_csv('prf_maa_DOY_%s%i.csv' %(startend[j],i)))
    #osuusdata
    osuuslis = np.empty(doydflis.shape[1],object)
    for i in range(len(luokat.ikir)):
        osuuslis[i] = maalajit.nimen_jako(pd.read_csv('prf_maa_osuus_%i.csv' %(i)))
    xtaul = np.full([lse,len(luokat.ikir)], None, object)
    ytaul = np.full([lse,len(luokat.ikir),len(luokat2)], None, object)

def data_koppen():
    global tarkk,doydflis,osuuslis,xtaul,ytaul,luokat2
    luokat2 = ['D.c','D.d','ET']
    tarkk = 10
    lse = len(startend)
    doydflis = np.empty([lse,len(luokat.ikir)],object)
    osuuslis = np.full([len(luokat.ikir)], None)
    for j in range(lse):
        for i in range(doydflis.shape[1]):
            doydflis[j,i] = pd.read_csv('prf_köppen_%s%i.csv' %(startend[j],i))
    xtaul = np.full([lse,len(luokat.ikir)], None, object)
    ytaul = np.full([lse,len(luokat.ikir),len(luokat2)], None, object)

def main():
    global axs
    argumentit(sys.argv[1:])
    if not maa_vai_koppen:
        print("%s: Virhe: tarvitaan argumentti maa/köppen" %(__name__))
        return
    rcParams.update({'font.size':13,'figure.figsize':(16,8)})

    if maa_vai_koppen == 'maa':
        data_maa()
    elif maa_vai_koppen == 'köppen':
        data_koppen()
    else:
        print(f"{__name__}: Virheellinen muuttuja maa_vai_koppen={maa_vai_koppen}")
        return

    fig,axs = subplots(1,len(startend))
    axs = np.array(axs).flatten()

    vaihda_luokat(0)
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
    fig.canvas.mpl_connect('key_press_event',nappainfunk)
    show()
    return

if __name__ == '__main__':
    main()

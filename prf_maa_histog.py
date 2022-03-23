#!/usr/bin/python3
import numpy as np
import prf_maa_laatikko as pml
import prf
from matplotlib.pyplot import *
from numpy import sin

maaluokat = ['tundra_dry','tundra_wetland+\npermafrost_bog','boreal_forest']
ikir_ind=0

# laskee paljonko pinta-alaa on kullakin xjaon osuudella (km²).
# xjako on oltava tasavälinen
# Jos dt on dataframe, tämä on hirvittävän hidas. Olkoon dt numpy-array.
def pintaalat1x1(dt,lat,lon,xjako):
    aste = 0.0174532925199
    R2 = 40592558970441
    PINTAALA = lambda _lat: aste*R2*( sin((_lat+1)*aste) - sin(_lat*aste) )*1.0e-6
    
    lukualat = np.zeros(len(xjako))
    tarkk = xjako[1]-xjako[0]
    minluku = xjako[0]
    for j,la in enumerate(lat):
        ala = PINTAALA(la)
        x_rantu = dt[ j*lon.size : (j+1)*lon.size ]
        x_rantu = x_rantu[x_rantu >= minluku]
        for luku in x_rantu.astype(int):
            lukualat[(luku-minluku)//tarkk] += ala
    return lukualat

def luo_xjako(dt,tarkk):
    minluku = int(999999999)
    maxluku = int(-999999999)
    for luok in maaluokat:
        d = dt[luok]
        minluku = min(minluku,int(np.nanmin(d)))
        maxluku = max(maxluku,int(np.nanmax(d)))
    if pml.verbose:
        print( 'minluku: %d\n'
               'maxluku: %d' %(minluku,maxluku) )
    return np.arange(minluku,maxluku+1,tarkk)

def tee_luokka(xtaul,ytaul):
    xtaul[ikir_ind] = luo_xjako(pml.dflista[ikir_ind], tarkk)
    for i,mluok in enumerate(maaluokat):
        tmp = pml.dflista[ikir_ind]
        ytaul[ikir_ind,i] = pintaalat1x1( np.array(tmp[mluok]), np.array(tmp.lat), np.array(tmp.lon), xtaul[ikir_ind] )

def piirra():
    leveys = 0.8*tarkk/len(maaluokat)
    for i,mluok in enumerate(maaluokat):
        isiirto = i*leveys
        palkit = bar( xtaul[ikir_ind]+isiirto, ytaul[ikir_ind,i]/1000, width=leveys, label=mluok )

def viimeistele():
    ylabel('Extent (1000 km$^2$)')
    xlabel('winter %s day' %pml.startend)
    title(prf.luokat1[ikir_ind])
    legend()

def vaihda_luokka(hyppy):
    global ikir_ind,xtaul,ytaul
    ikir_ind = ( ikir_ind + len(prf.luokat1) + hyppy ) % len(prf.luokat1)
    if xtaul[ikir_ind] is None:
        tee_luokka(xtaul,ytaul)
    clf()
    piirra()
    viimeistele()
    draw()

def nappainfunk(tapaht):
    if tapaht.key == 'right' or tapaht.key == 'o' or tapaht.key == 'i':
        vaihda_luokka(1)
    elif tapaht.key == 'left' or tapaht.key == 'g' or tapaht.key == 'a':
        vaihda_luokka(-1)

def main():
    global xtaul,ytaul,tarkk
    tarkk = 15
    rcParams.update({'font.size':13,'figure.figsize':(10,8)})
    pml.argumentit()
    pml.valmista_data()
    xtaul = np.full(len(prf.luokat1), None, object)
    ytaul = np.full([len(prf.luokat1),len(maaluokat)], None, object)

    fig = figure()
    vaihda_luokka(0)
    if pml.tallenna:
        while True:
            if pml.verbose:
                print(prf.luokat1[ikir_ind])
            savefig("kuvia/%s_%s%i.png" %(sys.argv[0][:-3],pml.startend,ikir_ind))
            if ikir_ind==len(prf.luokat1)-1:
                exit()
            vaihda_luokka(1)
        return
    else:
        fig.canvas.mpl_connect('key_press_event',nappainfunk)
        show()
        return

if __name__ == '__main__':
    main()

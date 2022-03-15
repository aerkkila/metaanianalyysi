#!/usr/bin/python3
import numpy as np
from numpy import sin
from matplotlib.pyplot import *
import talven_ajankohta as taj
import prf_extent as prf

def argumentit():
    global startend, tallenna, tarkk
    tallenna = False
    startend = 'start'
    tarkk = 1
    for i in range(len(sys.argv)):
        a = sys.argv[i]
        if a == '-s':
            tallenna = True
        elif a == 'start' or a == 'end':
            startend = a
        elif a == '-t' or a == '--tarkkuus':
            i += 1
            tarkk = int(sys.argv[i])
    return

def vaihda_ikirluokka(hyppy:int):
    global ikir_ind
    ikir_ind = ( ikir_ind + len(prf.luokat) + hyppy ) % len(prf.luokat)
    if xarrlis[ikir_ind] is None:
        xarrlis[ikir_ind],yarrlis[ikir_ind] = pintaalat1x1( doy.where(ikirstr==prf.luokat[ikir_ind],np.nan), tarkk )
    for i,suorak in enumerate(palkit):
        suorak.set_height(yarrlis[ikir_ind][i]/1000/tarkk)
    title(prf.luokat[ikir_ind])
    gca().relim()
    gca().autoscale_view()
    draw()
    return

def nappainfunk(tapaht):
    if tapaht.key == 'right' or tapaht.key == 'o' or tapaht.key == 'i':
        vaihda_ikirluokka(1)
    elif tapaht.key == 'left' or tapaht.key == 'g' or tapaht.key == 'a':
        vaihda_ikirluokka(-1)
    return

def pintaalat1x1(darr,tarkk):
    aste = 0.0174532925199
    R2 = 40592558970441
    PINTAALA = lambda _lat: aste*R2*( sin((_lat+1)*aste) - sin(_lat*aste) )*1.0e-6
    
    dat = darr.data.flatten().astype(int)
    minluku = int(darr.min())
    maxluku = int(darr.max())
    lukualat = np.zeros( (maxluku - minluku) // tarkk + 1 )
    for j,la in enumerate(darr.lat.data):
        ala = PINTAALA(la)
        lonarr = dat[ j*darr.lon.size : (j+1)*darr.lon.size ]
        lonarr = lonarr[lonarr >= minluku]
        for luku in lonarr.astype(int):
            lukualat[(luku-minluku)//tarkk] += ala
    return np.arange(minluku,maxluku+1,tarkk), lukualat

if __name__ == '__main__':
    argumentit()
    ikir_ind = 0
    rcParams.update({'font.size':13,'figure.figsize':(12,10)})
    doy = taj.lue_avgdoy(startend)
    ikirouta = prf.Prf('1x1').rajaa( (doy.lat.min(), doy.lat.max()+1) )
    ikirstr = prf.luokittelu_str_xr(ikirouta.data.mean(dim='time'))
    prf.luokat = prf.luokat[1:]

    xarrlis = [None]*len(prf.luokat)
    yarrlis = xarrlis.copy()
    xarrlis[ikir_ind],yarrlis[ikir_ind] = pintaalat1x1( doy.where(ikirstr==prf.luokat[ikir_ind],np.nan), tarkk )

    fig = figure()
    palkit = bar( xarrlis[ikir_ind], yarrlis[ikir_ind]/1000/tarkk, width=0.8*tarkk )
    xlabel('winter %s doy' %startend)
    ylabel('extent (1000 km$^2$ / %s day)' %startend)
    title(prf.luokat[ikir_ind])
    tight_layout()
    if not tallenna:
        fig.canvas.mpl_connect('key_press_event',nappainfunk)
        show()
        exit()

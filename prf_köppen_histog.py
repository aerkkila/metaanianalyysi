#!/usr/bin/python3
import numpy as np
import pandas as pd
from matplotlib.pyplot import *
from config import tyotiedostot
import prf_apu_histog as pah
import prf

luokat2 = ['D.c','D.d','ET']
ikir_ind=0
startend = ['start','end']

def argumentit(argv):
    global tallenna,verbose
    tallenna = False; verbose = False
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
    title(prf.luokat1[ikir_ind])
    tight_layout()
    legend()


def vaihda_luokka(hyppy,kumpi):
    global ikir_ind,xtaul,ytaul
    ikir_ind = ( ikir_ind + len(prf.luokat1) + hyppy ) % len(prf.luokat1)
    if xtaul[kumpi,ikir_ind] is None:
        pah.tee_luokka(xtaul[kumpi,...], ytaul[kumpi,...], dflista=dflista[kumpi,...],
                       dfind=ikir_ind, luokat2=luokat2, tarkk=tarkk)
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

def main():
    global xtaul,ytaul,tarkk,axs,dflista
    argumentit(sys.argv[1:])
    tarkk = 10
    rcParams.update({'font.size':13,'figure.figsize':(16,8)})

    lse = len(startend)
    dflista = np.empty([lse,len(prf.luokat1)],object)
    for j in range(lse):
        for i in range(dflista.shape[1]):
            dflista[j,i] = pd.read_csv('prf_köppen_%s%i.csv' %(startend[j],i))
    xtaul = np.full([lse,len(prf.luokat1)], None, object)
    ytaul = np.full([lse,len(prf.luokat1),len(luokat2)], None, object)

    fig,axs = subplots(1,len(startend))
    axs = np.array(axs).flatten()

    vaihda_luokat(0)
    if tallenna:
        while True:
            if verbose:
                print(prf.luokat1[ikir_ind])
            savefig("kuvia/%s%s%i.png"
                    %(sys.argv[0][:-3], ('_'+startend[0] if len(startend)==1 else ''), ikir_ind))
            if ikir_ind==len(prf.luokat1)-1:
                exit()
            vaihda_luokat(1)
        return
    fig.canvas.mpl_connect('key_press_event',nappainfunk)
    show()
    return

if __name__ == '__main__':
    main()

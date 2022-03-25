#!/usr/bin/python3
import numpy as np
import prf_maa_laatikko as pml
import prf
import pandas as pd
import prf_apu_histog as pah
from matplotlib.pyplot import *

maaluokat = ['boreal_forest','tundra_dry','tundra_wetland+\npermafrost_bog']
ikir_ind=0

def piirra():
    leveys = 0.8*tarkk/len(maaluokat)
    for i,mluok in enumerate(maaluokat):
        isiirto = i*leveys+0.5*leveys
        palkit = bar( xtaul[ikir_ind]+isiirto, ytaul[ikir_ind,i]/1000, width=leveys, label=mluok )

def viimeistele():
    ylabel('Extent (1000 km$^2$)')
    xlabel('winter %s day' %pml.startend)
    ajat = pd.to_datetime(xtaul[ikir_ind],unit='D')
    xticks(xtaul[ikir_ind],labels=ajat.strftime("%m/%d"),rotation=30)
    title(prf.luokat1[ikir_ind])
    legend()

def vaihda_luokka(hyppy):
    global ikir_ind,xtaul,ytaul
    ikir_ind = ( ikir_ind + len(prf.luokat1) + hyppy ) % len(prf.luokat1)
    if xtaul[ikir_ind] is None:
        pah.tee_luokka(xtaul,ytaul, dflista=pml.dflista, dfind=ikir_ind, luokat2=maaluokat, tarkk=tarkk)
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

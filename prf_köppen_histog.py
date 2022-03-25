#!/usr/bin/python3
import numpy as np
import prf
import pandas as pd
import xarray as xr
import talven_ajankohta as taj
from config import tyotiedostot
from matplotlib.pyplot import *
import prf_apu_histog as pah
import köppen

ikir_ind=0
tallenna = False
startend = 'start'

def argumentit(argv):
    global tallenna,startend
    for a in argv:
        if a == '-s':
            tallenna = True
        if a == 'start' or a == 'end':
            startend = a

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
        pah.tee_luokka(xtaul,ytaul, dflista=ikirdflis, dfind=ikir_ind, tarkk=tarkk, luokat2=luokat2)
    clf()
    piirra()
    viimeistele()
    draw()

def nappainfunk(tapaht):
    if tapaht.key == 'right' or tapaht.key == 'o' or tapaht.key == 'i':
        vaihda_luokka(1)
    elif tapaht.key == 'left' or tapaht.key == 'g' or tapaht.key == 'a':
        vaihda_luokka(-1)

def valmista_data():
    #talven ajankohta
    doy = taj.lue_avgdoy(startend)
    #köppen-data
    koppdf = köppen.lue_oletusluokkamaskit_dataset('köppen1x1.nc').to_dataframe()
    #ikiroutadata
    ikirouta = prf.Prf('1x1','xarray').rajaa( (doy.lat.min(), doy.lat.max()+1) ).data.mean(dim='time')
    ikirstr = prf.luokittelu1_str_xr(ikirouta).data.flatten()
    #rajataan tarkemmin määrittelyalueeseen
    doy = doy.data.flatten()
    valinta = doy==doy
    koppdf = koppdf[valinta]
    ikirstr = ikirstr[valinta]
    doy = doy[valinta]
    #yhdistetään talven ajankohta
    for nimi in koppdf:
        koppdf[nimi] = koppdf[nimi].mul(doy)
    #yhdistetään ikirouta
    ikirluokat = prf.luokat1 # np.unique(ikirstr) sekoittaisi järjestyksen
    ikirdflis = np.empty(len(ikirluokat),object)
    for i,ikirluok in enumerate(ikirluokat):
        valinta = ikirstr==ikirluok
        ikirdflis[i] = koppdf.loc[valinta,:]
    return ikirdflis,ikirluokat

def main():
    global xtaul,ytaul,tarkk,luokat2,ikirdflis
    tarkk = 10
    argumentit(sys.argv[1:]) #tallenna,startend
    rcParams.update({'font.size':13,'figure.figsize':(10,8)})
    ikirdflis,ikirluokat = valmista_data()
    luokat2 = list(ikirdflis[0].keys())
    xtaul = np.full(len(ikirluokat), None, object)
    ytaul = np.full([len(ikirluokat),len(luokat2)], None, object)
    for i in range(len(ikirdflis)):
        ikirdflis[i] = ikirdflis[i].reset_index()

    fig = figure()
    vaihda_luokka(0)
    if pkl.tallenna:
        while True:
            savefig("kuvia/%s_%s%i.png" %(sys.argv[0][:-3],pkl.startend,ikir_ind))
            if ikir_ind==len(ikirluokat)-1:
                exit()
            vaihda_luokka(1)
        return
    else:
        fig.canvas.mpl_connect('key_press_event',nappainfunk)
        show()
        return

if __name__ == '__main__':
    main()

#!/usr/bin/python3
import numpy as np
import xarray as xr
from numpy import sin
from matplotlib.pyplot import *
import ikirluokat
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

def vaihda_ikirluokka(hyppy:int):
    global ikir_ind
    ikir_ind = (ikir_ind + len(ikirluokat.dt) + hyppy) % len(ikirluokat.dt)
    if xarrlis[ikir_ind] is None:
        xarrlis[ikir_ind],yarrlis[ikir_ind] = pintaalat1x1(paivat, paivat.where(ikirdat==ikir_ind,np.nan), tarkk)
        return True
    return False

def vaihda_ikirluokka_piirtaen(hyppy:int):
    vaihda_ikirluokka(hyppy)
    for i,suorak in enumerate(palkit):
        suorak.set_height(yarrlis[ikir_ind][i]/1000/tarkk)
    title(ikirluokat.dt[ikir_ind])
    gca().relim()
    gca().autoscale_view()
    if aln[0] == 's':
        xlim([-110,75])
    else:
        xlim([-20,180])
    draw()
    return

def nappainfunk(tapaht):
    if tapaht.key == 'right' or tapaht.key == 'o' or tapaht.key == 'i':
        vaihda_ikirluokka_piirtaen(1)
    elif tapaht.key == 'left' or tapaht.key == 'g' or tapaht.key == 'a':
        vaihda_ikirluokka_piirtaen(-1)
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
    global ikir_ind, xarrlis, yarrlis, paivat, palkit, aln
    ikir_ind=0
    for alm, aln in zip(al_muuttuja, al_nimi):
        paivat = doy[alm]
        xarrlis = [None]*len(ikirluokat.dt)
        yarrlis = xarrlis.copy()
        xarrlis[ikir_ind],yarrlis[ikir_ind] = pintaalat1x1(paivat, paivat.where(ikirdat==ikir_ind,np.nan), tarkk)

        if verbose:
            import locale
            locale.setlocale(locale.LC_ALL,'')
            tulosta = lambda : print(locale.format_string( 'Yhteensä "%s"-aluetta %.2f Mkm²',
                                                           (ikirluokat.dt[ikir_ind], np.sum(yarrlis[ikir_ind])*1e-6) ))
            tulosta()
            while vaihda_ikirluokka(1):
                tulosta()

        fig = figure()
        palkit = bar(xarrlis[ikir_ind], yarrlis[ikir_ind]/1000, width=0.8*tarkk)
        xlabel('winter %s, data %i' %(aln,ftnum))
        ylabel('extent (1000 km$^2$)')
        title(ikirluokat.dt[ikir_ind])
        tight_layout()
        vaihda_ikirluokka_piirtaen(0)
        if not tallenna:
            fig.canvas.mpl_connect('key_press_event',nappainfunk)
            show()
            continue
        while True:
            savefig("kuvia/yksittäiset/ikir%i_w%s_ft%i.png" %(ikir_ind,aln,ftnum))
            if ikir_ind+1 == len(ikirluokat.dt):
                ikir_ind = 0
                break
            vaihda_ikirluokka_piirtaen(1)

def main():
    global ikirdat
    rcParams.update({'font.size':19,'figure.figsize':(12,10)})
    argumentit()
    ikir_ind = 0
    kerroin = 8
    ftluvut = [0]
    pros = np.empty(len(ftluvut),object)
    for i,l in enumerate(ftluvut):
        doy = xr.open_dataset("kausien_pituudet%i.nc" %l)[al_muuttuja].mean(dim='vuosi')
        if(i==0):
            ikirdat = xr.open_dataset("prfdata_avg.nc")['luokka'].sel({'lat':slice(doy.lat.min(),doy.lat.max())})
        pros[i] = Process(target=aja, args=[doy,l])
        pros[i].start()
    for p in pros:
        p.join()

if __name__ == '__main__':
    main()

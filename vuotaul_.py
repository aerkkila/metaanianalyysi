#!/usr/bin/python3
from matplotlib.pyplot import *
from wetlandvuo import kaudet
from multiprocessing import Process
import numpy as np
import sys

ppnum = -1
pparg = ('pri', 'post')
varit = 'rgby'
luokittelu = ''

def lue_data():
    alustettu = False
    for k,kausi in enumerate(kaudet):
        for ftnum in range(3):
            nimi = 'vuotaulukot/%svuo_%s_%s_ft%i.csv' %(luokittelu, pparg[ppnum], kausi, ftnum)
            dt = np.genfromtxt(nimi, delimiter=',', skip_header=2)
            if not alustettu:
                luokat = []
                with open(nimi) as f:
                    f.readline()
                    rivi = f.readline()
                    for r in f:
                        luokat.append(r.partition(',')[0])
                cols      = rivi.rstrip().split(',')[1:]
                taul      = np.empty((len(cols), len(kaudet), 3, len(luokat)))
                alustettu = True
            for c in range(len(cols)):
                taul[c,k,ftnum,:] = dt[:,c+1]
    return taul, luokat, cols

def rikottu_akseli(Xsij, taul, c, yrajat12):
    fig, (ax2,ax1) = subplots(2, 1, sharex=True)
    for ax in (ax1,ax2):
        for k in range(taul.shape[1]):
            for j in range(taul.shape[2]):
                for i in range(taul.shape[3]):
                    ax.plot(Xsij(i,j), taul[c,k,j,i], '.', markersize=12, color=varit[k])
    ax1.set_ylim(yrajat12[0])
    ax2.set_ylim(yrajat12[1])
    ax1.spines['top'].set_visible(False)
    ax2.spines['bottom'].set_visible(False)
    ax2.xaxis.tick_top()
    # katkaisumerkki
    k = 0.5
    kwargs = dict(marker=[(-1,-k),(1,k)], markersize=12, linestyle="none", color='k', mec='k', mew=1, clip_on=False)
    ax1.plot([0,1], [1,1], transform=ax1.transAxes, **kwargs)
    ax2.plot([0,1], [0,0], transform=ax2.transAxes, **kwargs)
    sca(ax2)
    return [ax1, ax2]

def mol_per_m2(Xsij, taul, c):
    rikottu_akseli(Xsij, taul, c, ([0, 0.042], [0.22, 0.42]))

def season_length(Xsij, taul, c):
    yrajat = (np.array([7, 19]), np.array([93, 250]))
    axs = rikottu_akseli(Xsij, taul*365.25, c, yrajat)
    for yr,ax in zip(yrajat,axs):
        ax1 = ax.twinx()
        ylim(yr/365.25)
        ax1.spines['bottom'].set_visible(False)
        ax1.spines['top'].set_visible(False)
        grid(False)
    ylabel('fraction of year')
    sca(axs[1])

def erikseen(eriluok, Xsij, taul, c, luokat, cols):
    ax0 = gca()
    vari = 'c'
    with rc_context({'axes.edgecolor':vari, 'ytick.color':vari}):
        ax1 = ax0.twinx()
        ax1.spines['bottom'].set_visible(False)
        ax1.spines['top'].set_visible(False)
        ax1.spines['left'].set_visible(False)
        ylabel(cols[c])
        ax1.yaxis.label.set_color(vari)
    ax1.grid(False)
    # käännetään eriluok viimeiseksi
    ind_eluok = luokat.index(eriluok)
    lk = luokat.copy()
    for i in range(ind_eluok, len(lk)-1):
        lk[i] = lk[i+1]
    lk[-1] = eriluok
    I = lambda i: i if i<ind_eluok else len(lk)-1 if i==ind_eluok else i-1
    for k in range(taul.shape[1]):
        for j in range(taul.shape[2]):
            for i in range(taul.shape[3]):
                ax = ax1 if i==ind_eluok else ax0
                ax.plot(Xsij(I(i),j), taul[c,k,j,i], '.', markersize=12, color=varit[k] if i else vari)
    sca(ax0)
    for k in range(len(kaudet)):
        plot(0, np.nan, '.', markersize=12, color=varit[k], label=kaudet[k])
    legend(loc='upper center')
    xticks(Xsij(np.arange(taul.shape[-1]),1), lk)
    ylabel(cols[c])

def aja(ppnumarg):
    global ppnum
    ppnum = ppnumarg
    taul,luokat,cols = lue_data()
    rcParams.update({'figure.figsize':(1.5*taul.shape[-1], 8),
                     'font.size':14, 'axes.grid':True, 'axes.grid.axis':'y', 'grid.linestyle':':'})

    #joka toinen nimi alemmalle riville
    for i,x in enumerate(luokat):
        if i%2:
            luokat[i] = '\n'+x

    xlev = 1/len(luokat)
    xlevo = 0.45
    Xsij = lambda wi,fti: (wi+0.5)*xlev - 0.5*xlevo*xlev + fti*xlevo*xlev/3
    for c in range(taul.shape[0]):
        valmis = False
        goto_else = True
        if cols[c] == 'mol/m²':
            mol_per_m2(Xsij, taul, c)
            goto_else = False
        elif cols[c] == 'season_length':
            if not ppnum:
                continue # tämä ei riipu metaanivuosta
            season_length(Xsij, taul, c)
            goto_else = False
        elif cols[c] == 'Tg' or cols[c] == 'mol/s':
            eriluok = 'D.c' if luokittelu == 'köppen' else 'wetland' if luokittelu == 'wetland' else None
            if eriluok is None:
                goto_else = True
            else:
                lk = erikseen(eriluok, Xsij, taul, c, luokat, cols)
                valmis = True
                goto_else = False
        if goto_else:
            for k in range(taul.shape[1]):
                for j in range(taul.shape[2]):
                    for i in range(taul.shape[3]):
                        plot(Xsij(i,j), taul[c,k,j,i], '.', markersize=12, color=varit[k])

        if not valmis:
            for k in range(len(kaudet)):
                plot(0, np.nan, '.', markersize=12, color=varit[k], label=kaudet[k])
            legend()
            xticks(Xsij(np.arange(taul.shape[-1]),1), luokat)
            ylabel(cols[c])

        tight_layout()
        if '-s' in sys.argv:
            savefig('kuvia/yksittäiset/%s_%s_%s.png' %(luokittelu, pparg[ppnum], cols[c].replace('/',',')))
            clf()
            continue
        show()

def main():
    global luokittelu
    luokittelu = sys.argv[1]
    pr = np.empty(2, object)
    for i in range(len(pr)):
        pr[i] = Process(target=aja, args=[i])
        pr[i].start()
    for p in pr:
        p.join()
    return

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

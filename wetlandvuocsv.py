#!/usr/bin/python3
from matplotlib.pyplot import *
from wetlandvuo import kaudet
import numpy as np
import sys

def lue_data():
    alustettu = False
    for k,kausi in enumerate(kaudet):
        for ftnum in range(3):
            nimi = 'wetlandvuotaulukot/wetlandvuo_%s_ft%i.csv' %(kausi, ftnum)
            dt = np.genfromtxt(nimi, delimiter=',', skip_header=2)
            if not alustettu:
                wluokat = []
                with open(nimi) as f:
                    f.readline()
                    rivi = f.readline()
                    for r in f:
                        wluokat.append(r.partition(',')[0])
                cols      = rivi.rstrip().split(',')[1:]
                taul      = np.empty((len(cols), len(kaudet), 3, len(wluokat)))
                alustettu = True
            for c in range(len(cols)):
                taul[c,k,ftnum,:] = dt[:,c+1]
    return taul, wluokat, cols

varit = 'rgby'

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

def main():
    global axs
    rcParams.update({'figure.figsize':(10,8), 'font.size':14, 'axes.grid':True, 'axes.grid.axis':'y', 'grid.linestyle':':'})
    taul,wluokat,cols = lue_data()

    #joka toinen nimi alemmalle riville
    for i,x in enumerate(wluokat):
        if i%2:
            wluokat[i] = '\n'+x

    xlev = 1/len(wluokat)
    xlevo = 0.3
    Xsij = lambda wi,fti: (wi+0.5)*xlev - 0.5*xlevo*xlev + fti*xlevo*xlev/3
    for c in range(taul.shape[0]):
        if cols[c] == 'mol/m²':
            mol_per_m2(Xsij, taul, c)
        elif cols[c] == 'season_length':
            season_length(Xsij, taul, c)
        else:
            for k in range(taul.shape[1]):
                for j in range(taul.shape[2]):
                    for i in range(taul.shape[3]):
                        plot(Xsij(i,j), taul[c,k,j,i], '.', markersize=12, color=varit[k])

        for k in range(len(kaudet)):
            plot(0, np.nan, '.', markersize=12, color=varit[k], label=kaudet[k])
        legend()

        xticks(Xsij(np.arange(6),1), wluokat)
        ylabel(cols[c])
        tight_layout()
        if '-s' in sys.argv:
            savefig('kuvia/yksittäiset/wetland_%s.png' %(cols[c].replace('/',',')))
            clf()
            continue
        show()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

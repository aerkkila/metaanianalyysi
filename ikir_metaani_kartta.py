#!/usr/bin/python3
import xarray as xr
import numpy as np
import cartopy.crs as ccrs
import matplotlib.colors as mcolors
import matplotlib, sys, luokat
from matplotlib.pyplot import *
from matplotlib.colors import ListedColormap as lcmap
from multiprocessing import Process

varoitusväri = '\033[1;33m'
väri0        = '\033[0m'
ikir_ind     = 0

def argumentit(argv):
    global tallenna,verbose
    tallenna=False; verbose=False
    i=0
    while i < len(argv):
        a = argv[i]
        if a == '-s':
            tallenna = True
        elif a == '-v':
            verbose = True
        else:
            print("%sVaroitus:%s tuntematon argumentti \"%s\"" %(varoitusväri,väri0,a))
        i+=1

def luo_varikartta(ch4data):
    global pienin,suurin
    pienin = np.nanpercentile(ch4data.data, 1)
    suurin = np.nanpercentile(ch4data.data,99)
    if verbose:
        print('pienin, prosenttipiste: ', ch4data.min().data, pienin)
        print('suurin, prosenttipiste: ', ch4data.max().data, suurin)
    N = 1024
    cmap = matplotlib.cm.get_cmap('coolwarm',N)
    värit = np.empty(N,object)
    kanta = 10

    #negatiiviset vuot lineaarisesti
    for i in range(0,N//2):
        värit[i] = cmap(i)

    #positiiviset vuot logaritmisesti
    cmaplis=np.logspace(np.log(0.5)/np.log(kanta),0,N//2)
    for i in range(N//2,N):
        värit[i] = cmap(cmaplis[i-N//2])
    return lcmap(värit)

ulkoväri = '#d0e0c0'
harmaaväri = '#c0c0c0'

def piirrä():
    ax = gca()
    ax.set_extent(kattavuus,platecarree)
    ax.coastlines()
    #Tämä asettaa maskin ulkopuolisen alueen eri väriseksi
    harmaa = lcmap(ulkoväri)
    muu = xr.DataArray(data=np.zeros([kattavuus[3]-kattavuus[2],kattavuus[1]-kattavuus[0]]),
                       coords={ 'lat':np.arange(kattavuus[2]+0.5,kattavuus[3],1),
                                'lon':np.arange(kattavuus[0]+0.5,kattavuus[1],1), },
                       dims=['lat','lon'])
    muu.plot.pcolormesh(transform=platecarree, ax=gca(), cmap=harmaa, add_colorbar=False)
    #Varsinainen data
    ch4data.where(ikirouta==ikir_ind,np.nan).plot.\
        pcolormesh(transform=platecarree, cmap=vkartta, norm=mcolors.TwoSlopeNorm(0,max(pienin*6,-suurin),suurin),
                   add_colorbar=False)
    #Tämä asettaa muut ikiroutaluokka-alueet harmaaksi.
    harmaa = lcmap(harmaaväri)
    ch4data.where(~(ikirouta==ikir_ind),np.nan).plot.\
        pcolormesh( transform=platecarree, ax=gca(), add_colorbar=False, cmap=harmaa )

def varipalkki():
    cbar_nimio = r'$\frac{\mathrm{mol}}{\mathrm{m}^2\mathrm{s}}$'
    norm = mcolors.TwoSlopeNorm(0,max(pienin*6,-suurin),suurin)
    ax = axes((0.87,0.031,0.03,0.92))
    cbar = gcf().colorbar(matplotlib.cm.ScalarMappable(cmap=vkartta,norm=norm), cax=ax)
    ax.get_yaxis().labelpad = 15
    #cbar.set_label(cbar_nimio, rotation=0, fontsize=25) # Tämä aiheuttaa nyt yhtäkkiä virheen, vaikka ennen ei
    #väripalkki ulkoalueista
    harmaa = lcmap([ulkoväri,harmaaväri])
    norm = matplotlib.colors.Normalize(vmin=-2, vmax=2)
    ax = axes((0.78,0.031,0.03,0.92), frameon=False)
    cbar = gcf().colorbar(matplotlib.cm.ScalarMappable(cmap=harmaa,norm=norm), cax=ax, drawedges=False)
    cbar.ax.yaxis.set_ticks([])
    for i,s in enumerate(['undefined', 'other\ncategories']):
        cbar.ax.text(-1.8, -1+2*i, s)
    cbar.outline.set_visible(False)

def tee_alikuva(subplmuoto, subpl, **axes_kwargs):
    subpl_y = subplmuoto[0]-1 - subpl // subplmuoto[1]
    subpl_x = subpl % subplmuoto[1]
    xkoko = 0.77/subplmuoto[1]
    ykoko = 0.97/subplmuoto[0]
    ax = axes([0.02 + subpl_x*xkoko,
               0.03 + subpl_y*ykoko,
               xkoko-0.03, ykoko-0.05],
              **axes_kwargs)
    return ax

pripost_sis = ['flux_bio_prior', 'flux_bio_posterior'][::-1]
pripost_ulos = ['pri', 'post'][::-1]

def aja(ppind, ftnum):
    global ch4data, ikir_ind, vkartta
    ch4data1 = ch4data0[pripost_sis[ppind]]
    kaudet   = xr.open_dataarray("./kaudet%i.nc" %(ftnum))
    for k,kausi in enumerate(luokat.kaudet):
        if k == 0:
            ch4data = ch4data1.where(kaudet).mean(dim='time')
        else:
            ch4data  = ch4data1.where(kaudet==k).mean(dim='time')

        vkartta = luo_varikartta(ch4data)

        for ikir_ind in range(len(luokat.ikir)):
            sca(tee_alikuva([1,1], 0, projection=projektio))
            piirrä()
            title("%s, %s, data %i" %(luokat.ikir[ikir_ind],
                                      luokat.kaudet[k].replace('_', ' '), ftnum))
            varipalkki()
            if not tallenna:
                show()
                continue
            tunniste = "%s_%s_%s_ft%i" %(pripost_ulos[ppind], luokat.ikir[ikir_ind].replace(' ', '_'),
                                         luokat.kaudet[k], ftnum)
            savefig("./kuvia/yksittäiset/%s_%s.png" %(sys.argv[0][:-3], tunniste))
            clf()

def aja_(*args):
    try:
        aja(*args)
    except KeyboardInterrupt:
        sys.exit()

def main():
    global projektio,platecarree,kattavuus,ikirouta,ch4data0
    rcParams.update({'font.size':18,'figure.figsize':(10,7.8)})
    argumentit(sys.argv[1:])

    ch4data0 = xr.open_dataset('./flux1x1.nc')

    ikirouta = xr.open_dataset('./prfdata.nc')['luokka']
    ikirouta = ikirouta.sel({'time':range(2011,2019)}).mean(dim='time').round().astype(np.int8)
    ikirouta = ikirouta.sel({'lat':slice(29.5, 84)})

    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    kattavuus   = [-180,180,30,90]

    pr = np.empty(6, object)
    i=0
    for ppind in range(2):
        for ftnum in range(3):
            pr[i] = Process(target=aja_, args=(ppind,ftnum))
            pr[i].start()
            i+=1
    for p in pr:
        p.join()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

#!/usr/bin/python3
from matplotlib.pyplot import *
import cartopy.crs as ccrs
import xarray as xr
import sys, matplotlib
from flux1x1 import kaudet

def tee_alikuva(subplmuoto, subpl, projektio):
    subpl_y = subplmuoto[0]-1 - subpl // subplmuoto[1]
    subpl_x = subpl % subplmuoto[1]
    xkoko = 0.97/subplmuoto[1]
    ykoko = 0.97/subplmuoto[0]
    ax = axes([0.04 + subpl_x*xkoko,
               0.04 + subpl_y*ykoko,
               xkoko-0.03, ykoko-0.05],
              projection=projektio)
    return ax

def argumentit(argv):
    global tallenna
    tallenna = False
    for i in range(len(argv)):
        if argv[i] == '-s':
            tallenna = True

def aja(jako,kausi):
    argumentit(sys.argv[1:])
    rcParams.update({'font.size':13,'figure.figsize':(12,10)})
    tallenna = False
    if '-s' in sys.argv:
        tallenna = True
    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    kattavuus   = [-180,180,39,90]
    dt = xr.open_dataset('vuo_%s_%s.nc' %(jako,kausi)).mean(dim='time')

    pienin = np.inf
    suurin = -np.inf
    for nimi in dt.keys():
        yrite = np.nanpercentile(dt[nimi].data.flatten(), 99)
        if yrite > suurin:
            suurin = yrite
            continue
        yrite = np.nanpercentile(dt[nimi].data.flatten(), 1)
        if yrite < pienin:
            pienin = yrite

    for i,nimi in enumerate(dt.keys()):
        ax = tee_alikuva((2,2), i, projektio)
        ax.coastlines()
        ax.set_extent(kattavuus,platecarree)
        dt[nimi].plot.pcolormesh(transform=platecarree,cmap=get_cmap('seismic'),
                                 norm=matplotlib.colors.DivergingNorm(0,pienin*10,suurin))
        harmaa_kartta = matplotlib.colors.ListedColormap(['#e0e0e0'])
        xr.where(dt[nimi]!=dt[nimi],1,np.nan).plot.pcolormesh(transform=platecarree,
                                                              cmap=harmaa_kartta,
                                                              add_colorbar=False)
    if tallenna:
        savefig('kuvia/%s_%s_%s.png' %(sys.argv[0][:-3],jako,kausi))
        clf()
    else:
        show()
    return 0

if __name__=='__main__':
    arg0 = sys.argv[0]
    for jako in ['köppen','bawld']:
        for kausi in kaudet.keys():
            aja(jako,kausi)

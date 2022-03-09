#!/usr/bin/python3
import cartopy.crs as ccrs
import maalajit as ml
import sys
from matplotlib.pyplot import *
from maalajit_plot import args, maalajit

if __name__ == '__main__':
    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    kattavuus   = [-180,180,55,90]

    alkup, muunnos = ml.lue_maalajit(maalajit)
    alkup   = ml.maalajien_yhdistamiset( alkup, pudota=True )
    muunnos = ml.maalajien_yhdistamiset( muunnos, pudota=True )

    rcParams.update({'font.size': 17,
                     'figure.figsize': (14,8)})

    for i,laji in enumerate(alkup.keys()):
        sys.stdout.write('\r%i/%i\t%s\033[0K' %(i+1,len(alkup.keys()),laji))
        ax = axes( (0.01,0.02,0.41,0.92), projection=projektio )
        ax.coastlines()
        ax.set_extent(kattavuus, platecarree) 
        pcolormesh( muunnos[laji].lon, muunnos[laji].lat, muunnos[laji], transform=platecarree, cmap='gnuplot2_r', vmax=alkup[laji].max() )
        ax = axes( (0.43,0.02,0.03,0.92) )
        colorbar(cax=ax)

        ax = axes( (0.51,0.02,0.41,0.92), projection=projektio )
        ax.coastlines()
        ax.set_extent(kattavuus, platecarree)
        pcolormesh( alkup[laji].lon, alkup[laji].lat, alkup[laji], transform=platecarree, cmap='gnuplot2_r', vmax=alkup[laji].max() )
        ax = axes( (0.93,0.02,0.03,0.92) )
        colorbar(cax=ax)

        suptitle(laji)
        if(args.tallenna):
            savefig(f'BAWLD_kartta_{laji}.png')
            clf()
        else:
            show()
    sys.stdout.write('\r\033[0K')

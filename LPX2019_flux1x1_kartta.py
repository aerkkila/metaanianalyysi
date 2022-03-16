#!/usr/bin/python3
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import cartopy.crs as ccrs
import cartopy.feature as feature
from argparse import ArgumentParser
from configure import tyotiedostot

pars = ArgumentParser()
pars.add_argument('-k', '--kausi', default='whole_year',
                  help='summer, winter, \033[31mwhole_year\033[0m')
pars.add_argument('-m', '--muuttuja', default='posterior_bio',
                  help='Löytyvät nc-tiedostosta. Oletus on \033[31mposterior_bio\033[0m')
pars.add_argument('-s', '--tallenna', nargs='?', type=int, const=1, default=0)
args = pars.parse_args()

kaudet = { 'summer':(6,9), 'winter':(3,12), 'whole_year':(1,13) }
data0 = xr.open_dataset(tyotiedostot + 'FT_implementointi/Results_LPX2019/flux1x1_LPX2019_FTimpl_S3_bio_antro_tot.nc')[args.muuttuja]
ajat = pd.to_datetime(data0.time.data)
kohdat = (kaudet[args.kausi][0] <= ajat.month) & (ajat.month < kaudet[args.kausi][1])
if(args.kausi == 'winter'):
    kohdat = ~kohdat
data = data0[kohdat]
data = data.mean(dim='time')

platecarree=ccrs.PlateCarree()
kattavuus=[-180,180,49,90]
projection=ccrs.LambertAzimuthalEqualArea(central_latitude=90)
figsize=(12,10)

#minimi ja maksimi
maski_lat = ( (data.lat>=kattavuus[2]) & (data.lat<=kattavuus[3]) )
datamin = data.data[maski_lat].min()
datamax = data.data[maski_lat].max()

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111,projection=projection)
ax.set_extent(kattavuus,platecarree)
ax.coastlines()
ax.add_feature(feature.BORDERS)
data.plot.pcolormesh(x='lon', y='lat', ax=ax, transform=ccrs.PlateCarree(),
                     cmap='seismic', norm=mcolors.DivergingNorm(0,max(datamin*6,-datamax),datamax))#, vmin=datamin, vmax=datamax)
ax.set_title('Mean flux, %s' %args.kausi)
if(args.tallenna):
    plt.savefig('kuvia/' + '%s_%s_%s.png' %(sys.argv[0][:-3],args.muuttuja,args.kausi), dpi=150, bbox_inches='tight')
else:
    plt.show()

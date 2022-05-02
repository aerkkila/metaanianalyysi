#!/usr/bin/python3
import xarray as xr
import cartopy.crs as ccrs
from matplotlib.pyplot import *
import numpy
import config

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

wad2m = xr.open_dataarray(config.WAD2M+'wad2m.nc').mean(dim='time')
wetl = xr.open_dataset('./BAWLD1x1.nc').wetland
rcParams.update({'figure.figsize':(12,12)})

projektio = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
kattavuus = [-180,180,35,90]
ax = tee_alikuva([2,2], 0, projektio)
ax.coastlines()
ax.set_extent(kattavuus,ccrs.PlateCarree())
wad2m.plot.pcolormesh(transform=ccrs.PlateCarree(), cmap=get_cmap('coolwarm'))
title('WAD2M')

ax = tee_alikuva([2,2], 1, projektio)
ax.coastlines()
ax.set_extent(kattavuus,ccrs.PlateCarree())
wetl.plot.pcolormesh(transform=ccrs.PlateCarree(), cmap=get_cmap('coolwarm'))
title('Wetland')

ax = tee_alikuva([2,2], 2, projektio)
ax.coastlines()
ax.set_extent(kattavuus,ccrs.PlateCarree())
(wad2m-wetl).plot.pcolormesh(transform=ccrs.PlateCarree(), cmap=get_cmap('coolwarm'))
title('Erotus')

ax = tee_alikuva([2,2], 3, projektio)
ax.coastlines()
ax.set_extent(kattavuus,ccrs.PlateCarree())
dt = ((wad2m-wetl)/wetl*100).where(wetl**2>0.01, np.nan)
dt.plot.pcolormesh(transform=ccrs.PlateCarree(), cmap=get_cmap('coolwarm'))
title('Ero wetlandiin (%)')
print(np.nanmean(dt))
show()

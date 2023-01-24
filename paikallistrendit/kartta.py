#!/bin/env python
import cartopy.crs as ccrs
from netCDF4 import Dataset
import numpy as np
from matplotlib.pyplot import *
import matplotlib.colors as mcolors
import sys, os

kaudet = ['summer', 'freezing', 'winter']
tapahtumat = ['start', 'end', 'length']
raja = 5

def kartta(ds, kausi, tap):
    kt = (kausi, tap)

    def kuvaksi(dt, i):
        ax = subplot(1,2,i, projection=proj)
        ax.coastlines()
        ax.set_extent(katt, pc)
        normi = mcolors.TwoSlopeNorm(0, np.nanpercentile(dt, 2), np.nanpercentile(dt, 98))
        pcolormesh(mx, my, dt, transform=pc, norm=normi, cmap=get_cmap('coolwarm'))
        c = colorbar()
        if i == 2:
            title('p < %.2f' %(raja/100))
        c.set_label('$\Delta$(%s %s) / 10 years' %kt)

    pc   = ccrs.PlateCarree()
    proj = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    katt = [-180,180,35,90]

    lat = np.ma.getdata(ds['lat'])
    lon = np.ma.getdata(ds['lon'])
    mx,my = np.meshgrid(lon,lat, sparse=True)
    dt = np.ma.getdata(ds['trendit/%s_%s' %kt])
    dt1 = np.ma.getdata(ds['p/%s_%s' %kt])

    #ax = axes(projection=proj).coastlines()
    kuvaksi(dt,1)

    #ax = axes(projection=proj).coastlines()
    dt[dt1>=raja] = np.nan
    kuvaksi(dt,2)

    tight_layout()
    if '-s' in sys.argv:
        savefig('kuvat/%s_%s.png' %kt)
        clf()
    else:
        show()

def main():
    rcParams.update({'font.size': 15,
                     'figure.figsize': (16,8)})
    if '-s' in sys.argv:
        os.system('mkdir -p kuvat')

    ds = Dataset('trendit.nc', 'r')
    for kausi in kaudet:
        for tapaht in tapahtumat:
            kartta(ds, kausi, tapaht)

    ds.close()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

#!/usr/bin/python3
from ease_lonlat import EASE2GRID, SUPPORTED_GRIDS
import numpy as np
import xarray as xr
import sys

indeksi = lambda x,y: y*720+x

lat = np.arange(29.5, 84, 1)
lon = np.arange(-179.5,180,1)
#Jostain syystä pituuspiirit pitää kääntää takaperin
#Jos ease2-datan keskipituuspiiri ≠ 0, muutettakoon kpp:n arvoa
kpp = 180
lon1 = lon.copy()
if kpp:
    lon1[kpp:] = lon[:-kpp]
    lon1[0:kpp]= lon[-kpp:]
    lon1 = lon1[::-1]

koord = np.empty([len(lat)*len(lon)],int)
grid = EASE2GRID(name='EASE2_N25km', **SUPPORTED_GRIDS['EASE2_N25km'])
ind=0
for i,la in enumerate(lat):
    for j,lo in enumerate(lon1):
        koord[ind] = indeksi(*grid.lonlat2rc(lo,la)); ind+=1

xr.DataArray(dims=('lat','lon'),coords=({'lat':lat,'lon':lon}),data=koord.reshape([len(lat),len(lon)])).to_netcdf('testi.nc')

for nimi in sys.argv[1:]:
    ds0 = xr.open_dataset(nimi)
    ds = xr.Dataset()
    for i,avain in enumerate(ds0.keys()):
        da0 = ds0[avain]
        dt0 = da0.data.flatten()
        p0 = 720**2
        p1 = dt0.size//p0
        q0 = len(lat)*len(lon)
        dt = np.empty(q0*p1, dtype=dt0.dtype)
        for j in range(p1):
            dt[j*q0:(j+1)*q0] = dt0[j*p0:(j+1)*p0][koord]
        muoto = list(da0.data.shape)
        muoto[-2:] = [len(lat),len(lon)]
        dims = list(da0.dims)
        dims[-2:] = ['lat','lon']
        coords = {}
        pit = len(da0.coords)
        for k,crd in enumerate(da0.coords):
            if k<pit-2:
                coords.update({crd:da0[crd].data})
                continue
            coords.update({'lat':lat})
            coords.update({'lon':lon})
            break
        try:
            ds.update({avain:xr.DataArray(dims=dims, coords=coords, data=dt.reshape(muoto))})
        except:
            pass
    ind=0
    tulos=0
    while(1):
        tulos = nimi.find('/',ind)
        if(tulos<0):
            break
        ind=tulos+1
    ds.to_netcdf(nimi[ind:-3] + '1x1.nc')

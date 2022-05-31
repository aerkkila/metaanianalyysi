#!/usr/bin/python3
import xarray as xr
import cartopy.crs as ccrs
from matplotlib.pyplot import *
import config, locale
from sklearn import linear_model

def selittavyys(x,y,yvar):
    malli = linear_model.LinearRegression().fit(x,y)
    return 1 - np.mean((malli.predict(x)-y)**2) / yvar

def poista_epaluvut(lista):
    maski = lista[0]==lista[0]
    for i in range(1,len(lista)):
        maski &= lista[i]==lista[i]
    for i in range(len(lista)):
        lista[i] = lista[i][maski]
    return lista

#Tässä ei ole vähimmäismäärää wetlandille, minkä vuoksi selittävyys voi erota wetlandvuo-tiedostoista
wad2m = xr.open_dataarray(config.WAD2M+'wad2m.nc').mean(dim='time').data.flatten()
wetl = xr.open_dataset('./BAWLD1x1.nc').wetland.data.flatten()
vuo = xr.open_dataset('./flux1x1_winter.nc')['flux_bio_posterior'].mean(dim='time').data.flatten()*1e9
wad2m, wetl, vuo = poista_epaluvut([wad2m, wetl, vuo])

wad2m_h = np.array([wad2m,]).transpose()
wetl_h = np.array([wetl,]).transpose()
wad2m_wetl_h = np.array([wad2m,wetl,]).transpose()

vuovar = np.var(vuo)
locale.setlocale(locale.LC_ALL, '')
print(locale.format_string('wad2m:\t\t%.4f\n'
                           'wetl:\t\t%.4f\n'
                           'wad2m+wetl\t%.4f\n',
                           (selittavyys(wad2m_h, vuo, vuovar),
                            selittavyys(wetl_h, vuo, vuovar),
                            selittavyys(wad2m_wetl_h, vuo, vuovar))),
      end='')

arvio = lambda x: linear_model.LinearRegression().fit(x,vuo).predict(x)
rcParams.update({'figure.figsize':(10,12)})
fig, ax = subplots(3,1)
x = np.arange(len(vuo))

sca(ax[0])
plot(wad2m, vuo, '.')
arv = arvio(wad2m_h)
plot(wad2m, arvio(wad2m_h), '.')
xlabel('WAD2M')

sca(ax[1])
plot(wetl, vuo, '.')
arv = arvio(wetl_h)
plot(wetl, arv, '.')
xlabel('wetland')

sca(ax[2])
plot(wad2m, vuo, '.')
arv = arvio(wad2m_wetl_h)
plot(wad2m, arv, '.')

show()

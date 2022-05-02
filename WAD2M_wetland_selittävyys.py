#!/usr/bin/python3
import xarray as xr
import cartopy.crs as ccrs
from matplotlib.pyplot import *
import config, locale
from sklearn import linear_model

def selittavyys(x,y,ymean,yvar):
    malli = linear_model.LinearRegression().fit(x,y)
    return np.mean((malli.predict(x)-ymean)**2) / yvar

def poista_epaluvut(lista):
    maski = lista[0]==lista[0]
    for i in range(1,len(lista)):
        maski &= lista[i]==lista[i]
    for i in range(len(lista)):
        lista[i] = lista[i][maski]
    return lista

def jarjesta_nollannen_mukaan(lista):
    jarj = np.argsort(lista[0])
    for i in range(len(lista)):
        lista[i] = lista[i][jarj]
    return lista

wad2m = xr.open_dataarray(config.WAD2M+'wad2m.nc').mean(dim='time').data.flatten()
wetl = xr.open_dataset('./BAWLD1x1.nc').wetland.data.flatten()
vuo = xr.open_dataarray('./flux1x1_whole_year.nc').mean(dim='time').data.flatten()*1e9
wad2m, wetl, vuo = poista_epaluvut([wad2m, wetl, vuo])
vuo, wetl, wad2m = jarjesta_nollannen_mukaan([vuo, wetl, wad2m])

wad2m_h = np.array([wad2m,]).transpose()
wetl_h = np.array([wetl,]).transpose()
wad2m_wetl_h = np.array([wad2m,wetl,]).transpose()

vuovar = np.var(vuo)
vuomean = np.mean(vuo)
locale.setlocale(locale.LC_ALL, '')
print(locale.format_string('wad2m:\t\t%.4f\n'
                           'wetl:\t\t%.4f\n'
                           'wad2m+wetl\t%.4f\n',
                           (selittavyys(wad2m_h, vuo, vuomean, vuovar),
                            selittavyys(wetl_h, vuo, vuomean, vuovar),
                            selittavyys(wad2m_wetl_h, vuo, vuomean, vuovar))),
      end='')

arvio = lambda x: linear_model.LinearRegression().fit(x,vuo).predict(x)
rcParams.update({'figure.figsize':(12,12)})
fig, ax = subplots(3,2)
x = np.arange(len(vuo))

sca(ax[0,0])
plot(wad2m, vuo, '.')
arv = arvio(wad2m_h)
plot(wad2m, arvio(wad2m_h), '.')

sca(ax[0,1])
plot(x, vuo)
plot(x, np.sort(arv))

sca(ax[1,0])
plot(wetl, vuo, '.')
arv = arvio(wetl_h)
plot(wetl, arv, '.')

sca(ax[1,1])
plot(x, vuo)
plot(x, np.sort(arv))

sca(ax[2,0])
plot(wad2m, vuo, '.')
arv = arvio(wad2m_wetl_h)
plot(wad2m, arv, '.')

sca(ax[2,1])
plot(x, vuo)
plot(x, np.sort(arv))

show()

#!/usr/bin/python3
import xarray as xr
import numpy as np
import pandas as pd
import sys
from flux1x1 import kaudet

tyhja_taulukko = lambda index: pd.DataFrame(0, columns=['Keskiarvo', 'Keskiarvo 90 %', '5 %', '95 %'], index=index)

def tee_data_maarista(dt,maarat):
    dtf = dt.data.flatten()
    uusi = np.empty(sum(maarat)*dt.lon.size)
    ind_uusi = 0
    ind_data = 0
    for maara in maarat:
        for j_lon in range(len(dt.lon)):
            uusi[ind_uusi: ind_uusi+maara] = dtf[ind_data]
            ind_data += 1
            ind_uusi += maara
    return uusi

#Tätä ei käytetä. Tällä jätetään huomiotta hilaruutujen pinta-alan riippuvuus leveyspiiristä.
def tee_data_suoraan(dt):
    return dt.data.flatten()

def taulukon_teko(dt, lat_tasoitus_funk, *lat_funk_args):
    taul = tyhja_taulukko(dt.keys())
    for nimi in dt.keys():
        da = lat_tasoitus_funk(dt[nimi], *lat_funk_args)
        rajat = [np.nanpercentile(da, 5), np.nanpercentile(da, 95)]
        taul.loc[nimi,:] = [np.nanmean(da),
                            np.nanmean(da[(rajat[0]<=da) & (da<=rajat[1])]),
                            rajat[0],
                            rajat[1]]
    return taul*1e9


aste = 0.0174532925199
R2 = 40592558970441
PINTAALA = lambda _lat: aste*R2*( np.sin((_lat+1)*aste) - np.sin(_lat*aste) )*1.0e-6

def taul_pintaaloista(dt):
    alat = np.empty_like(dt.lat.data)
    for i,la in enumerate(dt.lat.data):
        alat[i] = PINTAALA(la)
    pisteita = 0
    for pa in alat:
        pisteita += int(np.round(pa/100))
    maarat = np.round(alat/alat[0]*32).astype(int)
    dt = dt.mean(dim='time')
    return taulukon_teko(dt, tee_data_maarista, maarat)

def aja(jako):
    if '-s' in sys.argv:
        f = open('%s_%s.txt' %(sys.argv[0][:-3],jako), 'w')
    else:
        f = sys.stdout
    for kausi in kaudet.keys():
        dt = xr.open_dataset('./vuo_%s_%s.nc' %(jako,kausi))
        f.write('%s\n%s\n\n' %(kausi,taul_pintaaloista(dt).to_string()))
        dt.close()
    if f != sys.stdout:
        f.close()

if __name__ == '__main__':
    aja('köppen')
    aja('bawld')

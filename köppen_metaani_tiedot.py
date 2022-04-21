#!/usr/bin/python3
import xarray as xr
import numpy as np
import pandas as pd
import time

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

def main():
    dt = xr.open_dataset('./köppen_metaani.nc')
    print('tasoittamaton')
    print(taulukon_teko(dt, tee_data_suoraan))
    print('tasoitettu')
    print(taul_pintaaloista(dt))
    dt.close()

if __name__ == '__main__':
    main()

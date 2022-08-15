#!/usr/bin/python3
import xarray as xr
import numpy as np
import pandas as pd
import sys, config, traceback

#Vuosiin lisätään yksi, koska tiedostojen nimissä vuosi n tarkoittaa talvea n–(n+1) eikä (n-1)–n
#Tämän voi tarkistaa laskentakoodista calculate_DOY_of_start_of_freezing.py tai tiedostojen attribuuteista
def nimesta_vuosi(ds):
    for var in ds.keys():
        ds[var] = ds[var].assign_coords({'vuosi':int(ds.encoding['source'][-7:-3])+1})
    return ds

def avaa(nimi):
    a = xr.open_mfdataset(nimi, engine='h5netcdf', combine='nested', concat_dim=['vuosi'], preprocess=nimesta_vuosi)
    return a.transpose('lat','lon','vuosi').load()

def vuoden_paivat(vuosi):
    return 366 if (vuosi % 4 and not (vuosi % 100)) or (vuosi % 400) else 365

def main():
    kesaluku = 1
    kausiluvut = [2,3] #kesä=1, jäätyminen=2, talvi=3. Nolla on varattu määrittelemättömälle kaudelle.
    kausinimet = ['freezing','winter']
    if sys.argv[1] == '0':
        kansio = config.tyotiedostot+'FT_implementointi/FT_percents_pixel_ease_flag/DOY/'
    elif sys.argv[1] == '1':
        kansio = config.tyotiedostot+'../smos_uusi/data1/'
    elif sys.argv[1] == '2':
        kansio = config.tyotiedostot+'../smos_uusi/data2/'

    a     = avaa(kansio+'freezing_start_doy_*.nc').freezing_start
    lat   = a.lat.data
    lon   = a.lon.data
    vuosi = a.vuosi.data
    rajat = np.empty([2,3,len(lat),len(lon),len(vuosi)], np.float32)

    ind = kausinimet.index('freezing')
    rajat[0,ind,...] = a.data
    a = avaa(kansio+'freezing_end_doy_*.nc').freezing_end
    rajat[1,ind,...] = a.data

    ind = kausinimet.index('winter')
    a = avaa(kansio+'winter_start_doy_*.nc').autumn_end
    rajat[0,ind,...] = a.data
    a = avaa(kansio+'winter_end_doy_*.nc').spring_start
    rajat[1,ind,...] = a.data
    
    maski = xr.open_dataarray('aluemaski.nc').data

    alkuaika  = pd.Period('%4i-08-01' %(int(vuosi[0])-1), freq='D')
    loppuaika = pd.Period('%4i-08-01' %(int(vuosi[-1])), freq='D')

    paivamaarat = pd.period_range(alkuaika, loppuaika-1)

    #tehdään dataarray vuodenajoista ja niitten pituuksista
    dt = np.zeros([lat.size, lon.size, (loppuaika-alkuaika).n], np.int8)
    dtpit = np.empty(len(kausinimet), object)
    for k in range(len(kausinimet)):
        dtpit[k] = np.empty([lat.size, lon.size, vuosi.size], np.float32) + np.nan
    print('')
    for j in range(lat.size):
        print('\033[F%i/%i\033[K' %(j+1,lat.size))
        for i in range(lon.size):
            if not maski[j,i]:
                continue
            dt[j,i,:] = kesaluku
            for v,vuosi1 in enumerate(vuosi):
                nollakohta = pd.Period('%4i-01-01' %vuosi1)
                for k,kausinum,kausi in zip(np.arange(len(kausiluvut)), kausiluvut, kausinimet):
                    paiva0 = rajat[0,k,j,i,v]
                    paiva1 = rajat[1,k,j,i,v]
                    if paiva0 != paiva0 and paiva1 != paiva1:
                        dtpit[k][j,i,v] = 0
                        continue
                    elif paiva0 == paiva0 and paiva1 != paiva1:
                        paiva1 = vuoden_paivat(vuosi1)
                    elif paiva0 != paiva0 and paiva1 == paiva1:
                        paiva0 = 0
                    pit = int(paiva1 - paiva0)
                    t0 = (nollakohta - (alkuaika + int(paiva0))).n
                    dt[j,i,t0:t0+pit] = kausinum
                    dtpit[k][j,i,v] = pit
    darr = xr.DataArray(dt, name='kausi',
                        dims=('lat','lon','time'),
                        coords=({'lat':lat,
                                 'lon':lon,
                                 'time':np.arange(0,len(paivamaarat))}))
    darr.attrs.update({'luvut':'1:kesä; 2:jäätyminen; 3:talvi'})
    darr.time.attrs.update({'units':'days since {}'.format((alkuaika))})
    darr.transpose('time','lat','lon').to_netcdf('%s%s.nc' %(sys.argv[0][:-3], sys.argv[1]))
    darr.close()
    return
    darrpitT = xr.Dataset()
    for i in range(len(kausinimet)):
        tmp = xr.DataArray(dtpit[i].transpose(2,0,1),
                           dims=('vuosi','lat','lon'),
                           coords=({'vuosi':vuosi.astype(np.int16),
                                    'lat':lat,
                                    'lon':lon,}))
        darrpitT = darrpitT.assign({kausinimet[i]: tmp.copy()})
    for t in tapahtumat:
        tmp = xr.DataArray(ajat[t].transpose('vuosi','lat','lon').data.astype(np.float32),
                           dims=('vuosi','lat','lon'),
                           coords=({'vuosi':vuosi.astype(np.int16),
                                    'lat':lat,
                                    'lon':lon,}))
        darrpitT = darrpitT.assign({t: tmp.copy()})
    darrpitT.to_netcdf('kausien_pituudet%s.nc' %sys.argv[1])
    darrpitT.close()
    return

if __name__=='__main__':
    try:
        main()
        print('\033[92mOhjelman ajo onnistui, vaikka tähän tulleekin virheilmoitus:\033[0m')
    except KeyboardInterrupt:
        print('')
        sys.exit()

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

avaa = lambda nimi: xr.open_mfdataset(nimi, engine='h5netcdf', combine='nested', concat_dim=['vuosi'], preprocess=nimesta_vuosi)
muokkaa_array = lambda darr: darr[1:-1,...].transpose('lat','lon','vuosi') #ensimmäinen ja viimeinen vuosi ovat huonoja

def main():
    kausiluvut = [1,2,3] #kesä, jäätyminen, talvi. Nolla on varattu määrittelemättömälle kaudelle.
    kausinimet = ['summer','freezing','winter']
    kansio = config.tyotiedostot+'FT_implementointi/FT_percents_pixel_ease_flag/DOY/'
    jaatym_alku = avaa(kansio+'freezing_start_doy_*.nc').freezing_start
    talven_alku = avaa(kansio+'winter_start_doy_*.nc').autumn_end
    talven_loppu = avaa(kansio+'winter_end_doy_*.nc').spring_start
    jaatym_alku = muokkaa_array(jaatym_alku)
    talven_alku = muokkaa_array(talven_alku)
    talven_loppu = muokkaa_array(talven_loppu)
    ajat = xr.Dataset({'jaatym_alku':jaatym_alku, 'talven_alku':talven_alku, 'talven_loppu':talven_loppu}).load()
    tapahtumat = ['jaatym_alku', 'talven_alku', 'talven_loppu']
    jaatym_alku.close()
    talven_alku.close()
    talven_loppu.close()

    alkuaika = pd.Period('%4i-08-01' %(int(ajat.vuosi[0])-1), freq='D')
    loppuaika = pd.Period('%4i-08-01' %(int(ajat.vuosi[-1])), freq='D')

    paivamaarat = pd.period_range(alkuaika, loppuaika-1)

    #tehdään dataarray vuodenajoista ja niitten pituuksista
    dt = np.zeros([ajat.lat.size, ajat.lon.size, (loppuaika-alkuaika).n], np.int8)
    dtpit = np.empty(len(kausinimet), object)
    for k in range(len(kausinimet)):
        dtpit[k] = np.zeros([ajat.lat.size, ajat.lon.size, ajat.vuosi.size], np.int16)
    print('')
    for j in range(ajat.lat.size):
        print('\033[F%i/%i\033[K' %(j+1,ajat.lat.size))
        for i in range(ajat.lon.size):
            ind = 0
            for v,vuosi in enumerate(ajat.vuosi):
                vuoden_paivat = 366 if (vuosi % 4 and not (vuosi % 100)) or (vuosi % 400) else 365
                nollakohta = pd.Period('%4i-01-01' %vuosi)
                joko0tai1 = 1 #Tällä laitetaan puuttuva data nollaksi. Esim. winter_end puuttuu --> talvi ja kesä pois.
                for kausi,tapahtuma in zip(kausiluvut, tapahtumat):
                    paiva = ajat[tapahtuma].data[j,i,v]
                    if paiva != paiva:
                        joko0tai1 = 0
                        continue
                    pit = (nollakohta+int(paiva) - paivamaarat[ind]).n
                    dt[j,i,ind:ind+pit] = kausi*joko0tai1
                    dtpit[kausi-1][j,i,v] = pit*joko0tai1 if pit*joko0tai1 <= vuoden_paivat else vuoden_paivat
                    joko0tai1 = 1
                    ind += pit
            dt[j,i,ind:] = kausiluvut[0]*joko0tai1 #loppu on kesää
    darr = xr.DataArray(dt, name='kausi',
                        dims=('lat','lon','time'),
                        coords=({'lat':ajat.lat,
                                 'lon':ajat.lon,
                                 'time':np.arange(0,len(paivamaarat))}))
    darr.attrs.update({'luvut':'1:kesä; 2:jäätyminen; 3:talvi'})
    darr.time.attrs.update({'units':'days since {}'.format((alkuaika))})
    darrpitT = xr.Dataset()
    for i in range(len(kausinimet)):
        tmp = xr.DataArray(dtpit[i], dims=('lat','lon','vuosi'),
                           coords=({'lat':ajat.lat,
                                    'lon':ajat.lon,
                                    'vuosi':ajat.vuosi.astype(np.int16)}))
        darrpitT = darrpitT.assign({kausinimet[i]: tmp.transpose('vuosi','lat','lon').copy()})
    ajat.close()
    darr.transpose('time','lat','lon').to_netcdf('%s.nc' %(sys.argv[0][:-3]))
    darr.close()
    darrpitT.to_netcdf('kausien_pituudet.nc')
    darrpitT.close()
    print('\033[92mOhjelman ajo onnistui, vaikka tähän tulleekin virheilmoitus:\033[0m')
    return

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

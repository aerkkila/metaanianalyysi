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

    #rajataan ch4data
    #sieltä luettaneen vain ajat eli sitä ilmankin pärjättäneisiin
    #ch4data = xr.open_dataset('../edgartno_lpx/flux1x1_1d.nc').sel({'lat':slice(ajat.lat.min(),ajat.lat.max())})
    #ch4alku = pd.Period(ch4data.time.data[0], freq='D')
    #ch4loppu = pd.Period(ch4data.time.data[-1], freq='D')
    alkuaika = pd.Period('%4i-08-01' %(int(ajat.vuosi[0])-1), freq='D')
    loppuaika = pd.Period('%4i-08-01' %(int(ajat.vuosi[-1])), freq='D')
    #ch4data = ch4data[(alkuaika-ch4alku).n:(loppuaika-ch4alku).n,...]

    #muunnetaan pd.Timestamp -> pd.Period
    #pit_aika = ch4data.time.size
    #paivamaarat = np.empty(pit_aika, object)
    paivamaarat = pd.period_range(alkuaika, loppuaika-1)
    #for i in range(pit_aika):
    #    paivamaarat[i] = pd.Period(ch4data.time.data[i], freq='D')

    #tehdään dataarray vuodenajoista ja niitten pituuksista
    dt = np.zeros([ajat.lat.size, ajat.lon.size, pit_aika], np.int8)
    dtpit = np.empty(len(kausinimet), object)
    for k in range(len(kausinimet)):
        dtpit[k] = np.zeros([ajat.lat.size, ajat.lon.size, ajat.vuosi.size], np.int16)
    #ind0 = (pd.Period('%4i-01-01' %ajat.vuosi.data[0], freq='D') - alkuaika).n #ensimmäisen nollakohdan indeksi
    print('')
    for j in range(ajat.lat.size):
        print('\033[F%i/%i\033[K' %(j+1,ajat.lat.size))
        for i in range(ajat.lon.size):
            ind = 0
            for v,vuosi in enumerate(ajat.vuosi):
                nollakohta = pd.Period('%4i-01-01' %vuosi)
                joko0tai1 = 1 #Tällä laitetaan puuttuva data nollaksi. Esim. winter_end puuttuu --> talvi ja kesä pois.
                for kausi,tapahtuma in zip(kausiluvut, tapahtumat):
                    paiva = ajat[tapahtuma].data[j,i,v]
                    if paiva != paiva:
                        joko0tai1 = 0
                        continue
                    pit = (nollakohta+int(paiva) - paivamaarat[ind]).n
                    dt[j,i,ind:ind+pit] = kausi*joko0tai1
                    dtpit[kausi-1][j,i,v] = pit
                    joko0tai1 = 1
                    ind += pit
            dt[j,i,ind:] = kausiluvut[0]*joko0tai1 #loppu on kesää
    darr = xr.DataArray(dt, name='kausi',
                        dims=('lat','lon','time'),
                        coords=({'lat':ajat.lat,
                                 'lon':ajat.lon,
                                 'time':paivamaarat})) #.data saa days since -attribuutin muuttumaan
    darr.kausi.attrs.update({'luvut':'1:kesä; 2:jäätyminen; 3:talvi'})
    darrpit = xr.Dataset()
    darrpitT = xr.Dataset()
    for i in range(len(kausinimet)):
        tmp = xr.DataArray(dtpit[i], dims=('lat','lon','vuosi'),
                           coords=({'lat':ajat.lat,
                                    'lon':ajat.lon,
                                    'vuosi':ajat.vuosi.astype(np.int16)}))
        darrpit = darrpit.assign({kausinimet[i]: tmp.copy()})
        darrpitT = darrpitT.assign({kausinimet[i]: tmp.transpose('vuosi','lat','lon').copy()})
    ajat.close()
    darr.to_netcdf('%s_latlontime.nc' %(sys.argv[0][:-3]))
    darr.transpose('time','lat','lon').to_netcdf('%s.nc' %(sys.argv[0][:-3]))
    darr.close()
    darrpit.to_netcdf('kausien_pituudet_latlontime.nc')
    darrpitT.to_netcdf('kausien_pituudet.nc')
    darrpit.close()
    darrpitT.close()
    print('\033[92mOhjelman ajo onnistui, vaikka tähän tulleekin virheilmoitus:\033[0m')
    return

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

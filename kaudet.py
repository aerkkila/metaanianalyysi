#!/usr/bin/python3
import xarray as xr
import numpy as np
import pandas as pd
import sys, config, traceback

def argumentit(argv):
    global tallenna,verbose,ikir_ind
    tallenna=False; verbose=False; ikir_ind=0
    i=1
    while i < len(argv):
        a = argv[i]
        if a == '-s':
            tallenna = True
        elif a == '-v':
            verbose = True
        else:
            print("%sVaroitus:%s tuntematon argumentti \"%s\"" %(varoitusvari,vari0,a))
        i+=1
    return

#Vuosiin lisätään yksi, koska tiedostojen nimissä vuosi n tarkoittaa talvea n–(n+1) eikä (n-1)–n
#Tämän voi tarkistaa laskentakoodista calculate_DOY_of_start_of_freezing.py tai tiedostojen attribuuteista
def nimesta_vuosi(ds):
    for var in ds.keys():
        ds[var] = ds[var].assign_coords({'vuosi':int(ds.encoding['source'][-7:-3])+1})
    return ds

avaa = lambda nimi: xr.open_mfdataset(nimi, engine='h5netcdf', combine='nested', concat_dim=['vuosi'], preprocess=nimesta_vuosi)
aikamaski_lambda = lambda dt: ~((dt<=-300) | (300<=dt)).any(axis=[1,2]).data.compute() # 0. vuosi jää pois
muokkaa_array = lambda darr,aikamaski: darr.sel({'vuosi':aikamaski}).transpose('lat','lon','vuosi')

def aja():
    argumentit(sys.argv[1:])
    kansio = config.tyotiedostot+'FT_implementointi/FT_percents_pixel_ease_flag/DOY/'
    jaatym_alku = avaa(kansio+'freezing_start_doy_*.nc').freezing_start
    aikamaski = aikamaski_lambda(jaatym_alku)
    talven_alku = avaa(kansio+'winter_start_doy_*.nc').autumn_end
    aikamaski |= aikamaski_lambda(talven_alku)
    talven_loppu = avaa(kansio+'winter_end_doy_*.nc').spring_start
    aikamaski |= aikamaski_lambda(talven_loppu)
    jaatym_alku = muokkaa_array(jaatym_alku,aikamaski)
    talven_alku = muokkaa_array(talven_alku,aikamaski)
    talven_loppu = muokkaa_array(talven_loppu,aikamaski)
    ajat = xr.Dataset({'jaatym_alku':jaatym_alku, 'talven_alku':talven_alku, 'talven_loppu':talven_loppu}).load()
    tapahtumat = ['jaatym_alku', 'talven_alku', 'talven_loppu']
    jaatym_alku.close()
    talven_alku.close()
    talven_loppu.close()

    #rajataan ch4data
    ch4data = xr.open_dataarray('../edgartno_lpx/flux1x1_1d.nc').sel({'lat':slice(ajat.lat.min(),ajat.lat.max())})
    ch4alku = pd.Period(ch4data.time.data[0], freq='D')
    ch4loppu = pd.Period(ch4data.time.data[-1], freq='D')
    alkuaika = pd.Period('%4i-08-01' %(int(ajat.vuosi[0])-1), freq='D')
    loppuaika = pd.Period('%4i-08-01' %(int(ajat.vuosi[-1])), freq='D')
    ch4data = ch4data[(alkuaika-ch4alku).n:(loppuaika-ch4alku).n,...]

    #muunnetaan pd.Timestamp -> pd.Period
    pit_aika = ch4data.time.size
    ch4ajat = np.empty(pit_aika,pd.Period)
    for i in range(pit_aika):
        ch4ajat[i] = pd.Period(ch4data.time.data[i], freq='D')

    #tehdään dataarray vuodenajoista
    dt = np.zeros([ajat.lat.size, ajat.lon.size, pit_aika], np.int8)
    ind0 = (pd.Period('%4i-01-01' %ajat.vuosi.data[0], freq='D') - alkuaika).n #ensimmäisen nollakohdan indeksi
    print('')
    for j in range(ajat.lat.size):
        print('\033[F%i/%i\033[K' %(j+1,ajat.lat.size))
        for i in range(ajat.lon.size):
            ind = ind0
            for v,vuosi in enumerate(ajat.vuosi):
                nollakohta = pd.Period('%4i-01-01' %vuosi)
                for kausi,tapahtuma in zip([3,1,2], tapahtumat):
                    paiva = ajat[tapahtuma].data[j,i,v]
                    if paiva != paiva:
                        break #oispa goto
                    pit = (nollakohta+int(paiva) - ch4ajat[ind]).n
                    dt[j,i,ind:ind+pit] = kausi
                    ind += pit
                else:
                    continue
                break
    ajat.close()
    darr = xr.DataArray(dt, name='kausi',
                        dims=('lat','lon','time'),
                        coords=({'lat':ajat.lat,
                                 'lon':ajat.lon,
                                 'time':ch4data.time.data})) #.data saa time:units-attribuutin muuttumaan
    ch4data.close()
    darr.to_netcdf('%s_latlontime.nc' %(sys.argv[0][:-3]))
    darr.transpose('time','lat','lon').to_netcdf('%s.nc' %(sys.argv[0][:-3]))
    darr.close()
    print('\033[92mOhjelman ajo onnistui, vaikka tähän tulleekin virheilmoitus:\033[0m')
    return 0

def main():
    try:
        r = aja()
    except:
        print('\033[91mOhjelman ajo epäonnistui.\033[0m %s' %traceback.format_exc())
        sys.exit(1)
    sys.exit(r)

if __name__=='__main__':
    main()

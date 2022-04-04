#!/usr/bin/python3
import xarray as xr
import numpy as np
import pandas as pd
import sys
import config

varoitusvari = '\033[1;33m'
vari0 = '\033[0m'

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

def main():
    argumentit(sys.argv[1:])
    vuodet = range(2010,2019)
    kansio = config.tyotiedostot+'FT_implementointi/FT_percents_pixel_ease_flag/DOY/'
    alkuajat = np.empty(len(vuodet),object)
    loppuajat = alkuajat.copy()
    for i,vuosi in enumerate(vuodet):
        alkuajat[i] = xr.open_dataarray(kansio+'freezing_start_doy_%4d.nc' %vuosi)
        loppuajat[i] = xr.open_dataarray(kansio+'winter_start_doy_%4d.nc' %vuosi)
    alku = xr.concat(alkuajat,dim='time')
    loppu = xr.concat(loppuajat,dim='time')
    for i in range(len(vuodet)):
        alkuajat[i].close()
        loppuajat[i].close()

    #Joka vuodelta pd.Timestamp-dataarray alku- ja loppuajoista
    alkuajat=np.empty(len(vuodet),object)
    loppuajat=np.empty(len(vuodet),object)
    for i,vuosi in enumerate(vuodet):
        nollakohta = pd.Period('%4i-01-01' %(vuosi+1))
        #epälukujen kohdalla alku == loppu
        alkuajat[i] = nollakohta + alku[i,...].\
            where( (alku[i,...]==alku[i,...]) & (loppu[i,...]==loppu[i,...]), 0 ).astype(int)
        loppuajat[i] = nollakohta + loppu[i,...].\
            where( (alku[i,...]==alku[i,...]) & (loppu[i,...]==loppu[i,...]), 0 ).astype(int)

    #rajataan ch4data
    ch4data = xr.open_dataarray('../edgartno_lpx/flux1x1_1d.nc').loc[:,loppu.lat.min():loppu.lat.max(),:]
    ch4alku = pd.Period(ch4data.time.data[0], freq='D')
    ch4loppu = pd.Period(ch4data.time.data[-1], freq='D')
    ft_alku = pd.Period('%4i-01-01' %(vuodet[0]), freq='D')
    ft_loppu = pd.Period('%4i-01-01' %(vuodet[-1]+1), freq='D')
    ch4data = ch4data[(ft_alku-ch4alku).n:(ft_loppu-ch4alku).n,...]

    ch4data = ch4data.transpose('lat','lon','time')

    #muunnetaan pd.Timestamp -> pd.Period
    pit_aika = ch4data.sizes['time']
    ch4ajat = np.empty(pit_aika,pd.Period)
    for i in range(pit_aika):
        ch4ajat[i] = pd.Period(ch4data.time.data[i], freq='D')

    pit_latlon = ch4data.sizes['lat']*ch4data.sizes['lon']
    k = 0
    dt = ch4data.data
    for i in range(ch4data.shape[0]): #lat
        for j in range(ch4data.shape[1]): #lon
            k += 1
            print("\r%i/%i" %(k,pit_latlon), end='')
            ind = 0
            for v,vuosi in enumerate(vuodet[1:]): #ensimmäinen vuosi on huono
                pit = alkuajat[v].data[i,j] - ch4ajat[ind]
                dt[i,j,ind:ind+pit.n] = np.nan
                #indeksi seuraavan ulkopuolisen kohdan alkuun
                erotus = loppuajat[v].data[i,j] - ch4ajat[ind]
                ind += erotus.n
            dt[i,j,ind:] = np.nan

    ch4data.data = dt
    ch4data = ch4data.transpose('time','lat','lon')
    ch4data[:570,...] = np.nan #ensimmäinen vuosi pois
    print("")
    #kopioidaan, jotta aika-attribuutti päivittyy
    tallennus = xr.DataArray(data = ch4data.data[365:,...],
                             coords = {'time':ch4data.time.data[365:], 'lat':ch4data.lat.data, 'lon':ch4data.lon.data},
                             dims = ['time','lat','lon'],
                             name = ch4data.name)
    tallennus.to_netcdf('flux1x1_jäätymiskausi.nc')

if __name__ == '__main__':
    main()

#!/usr/bin/python3
import xarray as xr
import pandas as pd
from scipy.interpolate import interp2d
import os
from config import tyotiedostot

tunnisteet_kaikki = {
    'glacier'        : 'GLA',
    'rockland'       : 'ROC',
    'tundra_dry'     : 'TUN',
    'boreal_forest'  : 'BOR',
    'wetland'        : 'WET',
    'permafrost_bog' : 'PEB',
    'tundra_wetland' : 'WTU',
    'marsh'          : 'MAR',
    'bog'            : 'BOG',
    'fen'            : 'FEN',
    'lake'           : 'LAK',
    'river'          : 'RIV',
}
tunnisteet = {
    # 'glacier'        : 'GLA',
    # 'rockland'       : 'ROC',
    'tundra_dry'     : 'TUN',
    'boreal_forest'  : 'BOR',
    # 'wetland'        : 'WET',
    'permafrost_bog' : 'PEB',
    'tundra_wetland' : 'WTU',
    # 'marsh'          : 'MAR',
    'bog'            : 'BOG',
    'fen'            : 'FEN',
    'lake'           : 'LAK',
    # 'river'          : 'RIV',
}

def maalajien_yhdistamiset(setti, pudota=False):
    lista = []
    for lajit in [ ['bog','fen'], ['tundra_wetland','permafrost_bog'] ]:
        ohita = False
        for laji in lajit:
            if not laji in setti.keys():
                ohita = True
                break
        if ohita:
            continue
        taul = setti[lajit[0]].copy()
        nimi=lajit[0]
        lista.append(lajit[0])
        for laji in lajit[1:]:
            taul += setti[laji]
            nimi += '+%s' %laji
            lista.append(laji)
        setti.update( taul.to_dataset(name=nimi) )
    return setti.drop_vars(lista) if pudota else setti

def nimen_jako(df:pd.DataFrame) -> pd.DataFrame: #jaetaan pitkät yhdistelmänimet kahdelle riville
    nimenvaihto = {}
    for sarake in df.columns:
        if( '+' in sarake and len(sarake) > 10 ):
            ind = sarake.index('+')+1
            nimenvaihto.update({ sarake: sarake[:ind] + '\n' + sarake[ind:] })
    df.rename( nimenvaihto, inplace=True, axis='columns' )
    return df

def hae_tiednimi(maalaji):
    for tied in os.listdir(tyotiedostot+'MethEOWP730/BAWLD'):
        if f'_{tunnisteet_kaikki[maalaji]}.nc' in tied:
            return tied

class Muuntaja1x1:
    def __init__(self):
        data = xr.open_dataset(tyotiedostot+'FT_implementointi/FT_percents_pixel_ease_flag/DOY/winter_start_doy_2010.nc')
        self.uusi = xr.DataArray( dims=('lat', 'lon'), coords=({'lat':data.lat, 'lon':data.lon}) )
        data.close()
    def __enter__(self):
        return self
    def __call__(self,maadata):
        uusi = self.uusi.copy()
        interp = interp2d(maadata.lon, maadata.lat, maadata.data, copy=False)
        uusi.data = interp(uusi.lon, uusi.lat)
        return uusi
    def __exit__(self,a,b,c):
        self.uusi.close()

def lue_maalajit(maalajit, alkup=True, muunnos=True): -> xr.Dataset:
    alkup_data = None
    muunn_data = None
    with Muuntaja1x1() as muuntaja:
        for maalaji in maalajit:
            maadata = xr.open_dataset( tyotiedostot + 'MethEOWP730/BAWLD/' + hae_tiednimi(maalaji) ).Band1.fillna(0)
            if(alkup):
                if alkup_data is None:
                    alkup_data = maadata.to_dataset(name=maalaji)
                else:
                    alkup_data.update( maadata.to_dataset(name=maalaji) )
            if(muunnos):
                if muunn_data is None:
                    muunn_data = muuntaja(maadata).to_dataset(name=maalaji)
                else:
                    muunn_data.update( muuntaja(maadata).to_dataset(name=maalaji) )
    return alkup_data, muunn_data

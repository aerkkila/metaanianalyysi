#!/usr/bin/python3
import config, sys, os
import numpy as np
from netCDF4 import Dataset
from scipy.interpolate import interp2d

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

def hae_tiednimi(luokka, hakemisto):
    for tied in os.listdir(hakemisto):
        if f'_{tunnisteet_kaikki[luokka]}.nc' in tied:
            return hakemisto+tied
    print("Ei löytynyt %s" %luokka)
    sys.exit()

def luo_data(luokat, alkup=True, muunnos=True):
    alkup_data = None
    muunn_data = None
    if alkup:
        ds0 = Dataset('BAWLD05x05.nc', 'w')
        lat0 = np.arange(29.25, 83.9, 0.5)
        lon0 = np.arange(-179.75, 179.9, 0.5)
        ds0.createDimension('lat', lat0.size)
        ds0.createDimension('lon', lon0.size)
        ds0.createVariable('lat', 'f8', ('lat'))
        ds0.createVariable('lon', 'f8', ('lon'))
        ds0['lat'][:] = lat0
        ds0['lon'][:] = lon0
    if muunnos:
        ds1 = Dataset('BAWLD1x1.nc', 'w')
        lat1 = np.arange(29.5, 84, 1)
        lon1 = np.arange(-179.5, 180, 1)
        ds1.createDimension('lat', lat1.size)
        ds1.createDimension('lon', lon1.size)
        ds1.createVariable('lat', 'f8', ('lat'))
        ds1.createVariable('lon', 'f8', ('lon'))
        ds1['lat'][:] = lat1
        ds1['lon'][:] = lon1
    for luokka in luokat:
        ds = Dataset(hae_tiednimi(luokka, config.tyotiedostot+'MethEOWP730/BAWLD/'), 'r')
        lat = ds['lat'][:]
        liite = np.zeros([np.searchsorted(lat0,lat[0]), lon0.size])
        data0 = ds['Band1'][:].filled(0)
        data0 = np.concatenate([liite,data0*0.01], axis=0)
        if(alkup):
            ds0.createVariable(luokka, 'f8', ('lat','lon'))
            ds0[luokka][:] = data0
        if(muunnos):
            interp = interp2d(lon0, lat0, data0, copy=False)
            data1 = interp(lon1, lat1)
            ds1.createVariable(luokka, 'f8', ('lat','lon'))
            ds1[luokka][:] = data1
        ds.close()
    return ds0, ds1

def main():
    ds0, ds1 = luo_data(tunnisteet_kaikki.keys())
    ds0.close()
    ds1.close()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

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
lisäluokat = {
    'wetland_nonprf' : ['bog','fen','marsh'],
    'wetland_prf'    : ['permafrost_bog','tundra_wetland']
}

def hae_tiednimi(luokka, hakemisto, jatke):
    for tied in os.listdir(hakemisto):
        if '_%s%s.nc' %(tunnisteet_kaikki[luokka],jatke) in tied:
            return hakemisto+tied
    print("Ei löytynyt %s" %luokka)
    sys.exit()

def luo_data(jatke):
    alkup,muunnos = (1,1)
    luokat = tunnisteet_kaikki.keys()
    if alkup:
        ds0 = Dataset('BAWLD05x05%s.nc' %jatke, 'w')
        lat0 = np.arange(29.25, 83.9, 0.5)
        lon0 = np.arange(-179.75, 179.9, 0.5)
        ds0.createDimension('lat', lat0.size)
        ds0.createDimension('lon', lon0.size)
        ds0.createVariable('lat', 'f8', ('lat'))
        ds0.createVariable('lon', 'f8', ('lon'))
        ds0['lat'][:] = lat0
        ds0['lon'][:] = lon0
    if muunnos:
        ds1 = Dataset('BAWLD1x1%s.nc' %jatke, 'w')
        lat1 = np.arange(29.5, 84, 1)
        lon1 = np.arange(-179.5, 180, 1)
        ds1.createDimension('lat', lat1.size)
        ds1.createDimension('lon', lon1.size)
        ds1.createVariable('lat', 'f8', ('lat'))
        ds1.createVariable('lon', 'f8', ('lon'))
        ds1['lat'][:] = lat1
        ds1['lon'][:] = lon1

    def luo_muuttuja(data0, liite, luokka):
        data0 = np.concatenate([liite,data0*0.01], axis=0)
        if(alkup):
            ds0.createVariable(luokka, 'f8', ('lat','lon'))
            ds0[luokka][:] = data0
        if(muunnos):
            interp = interp2d(lon0, lat0, data0, copy=False)
            data1 = interp(lon1, lat1)
            ds1.createVariable(luokka, 'f8', ('lat','lon'))
            ds1[luokka][:] = data1

    for luokka in luokat:
        ds = Dataset(hae_tiednimi(luokka, config.tyotiedostot+'MethEOWP730/BAWLD/', jatke), 'r')
        lat = ds['lat'][:]
        liite = np.zeros([np.searchsorted(lat0,lat[0]), lon0.size])
        data0 = ds['Band1'][:].filled(0)
        luo_muuttuja(data0, liite, luokka)
        ds.close()
    for luokka in lisäluokat:
        lista = lisäluokat[luokka]
        ds = Dataset(hae_tiednimi(lista[0], config.tyotiedostot+'MethEOWP730/BAWLD/', jatke), 'r')
        dt = ds['Band1'][:].filled(0)
        ds.close()
        for a in lista[1:]:
            ds = Dataset(hae_tiednimi(a, config.tyotiedostot+'MethEOWP730/BAWLD/', jatke), 'r')
            dt += ds['Band1'][:].filled(0)
            ds.close()
        luo_muuttuja(dt, liite, luokka)
        
    return ds0, ds1

def main():
    for jatke in ['','_H','_L']:
        ds0, ds1 = luo_data(jatke)        
        ds0.close()
        ds1.close()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

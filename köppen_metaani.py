#!/usr/bin/python3
import xarray as xr
import numpy as np
import config, köppen, sys

def main(tiednimi):
    #rajataan winter_start_datan sijainteihin
    kansio = config.tyotiedostot+'FT_implementointi/FT_percents_pixel_ease_flag/DOY/'
    ajat = xr.open_dataarray(kansio+'winter_start_doy_2014.nc')

    dt_kop = köppen.lue_oletusluokkamaskit_dataset()
    dt_ch4 = xr.open_dataarray(tiednimi).sel({'lat':slice(dt_kop.lat.min(),dt_kop.lat.max())})
    for t in range(len(dt_ch4.time)):
        dt_ch4[t,...] = dt_ch4[t,...].where(ajat==ajat, np.nan)
    ajat.close()
    uusidata = {}
    for i,nimi in enumerate(dt_kop.keys()):
        dt_ = np.empty(dt_ch4.data.shape)
        for t in range(len(dt_ch4.time)):
            dt_[t,...] = xr.where(dt_kop[nimi], dt_ch4[t,...], np.nan).data
        uusidata.update({nimi: xr.DataArray(dt_,
                                            coords=({'time':dt_ch4.time, 'lat':dt_ch4.lat, 'lon':dt_ch4.lon}),
                                            dims=('time','lat','lon'))})
    dt = xr.Dataset(uusidata,
                    coords=({'time':dt_ch4.time, 'lat':dt_ch4.lat, 'lon':dt_ch4.lon}))
    dt.to_netcdf('%s.nc' %(sys.argv[0][:-3]))
    return 0

if __name__ == '__main__':
    sys.exit(main(config.edgartno_dir + 'posterior.nc'))

#!/usr/bin/python3
import xarray as xr
import numpy as np
import config, sys

kaudet = {'freezing':2, 'winter':3, 'summer':1, 'whole_year':4}

def main():
    kausidata = xr.open_dataarray('./kaudet.nc')
    vuotied = config.edgartno_dir + 'flux1x1_1d.nc'
    vuo = xr.open_dataset(vuotied).sel({'lat':slice(kausidata.lat.min(),kausidata.lat.max()),})

    # tallennetaan leikattu, mutta muuten käsittelemätön versio
    uusi = vuo.sel(time=slice(kausidata.time.min(),vuo.time.max()+1))
    uusi.coords.update({'time':uusi.time.data})
    uusi.to_netcdf("%s.nc" %(sys.argv[0][:-3]))
    return
    
    vuo = vuo.sel({'time':slice(kausidata.time.min(),kausidata.time.max())})
    print('')
    for i,kausi in enumerate(kaudet.keys()):
        print('\033[F%i/%i\033[K' %(i+1,len(kaudet.keys())))
        if kausi=='whole_year':
            uusi = xr.where(kausidata!=0, vuo, np.nan)
        else:
            uusi = xr.where(kausidata==kaudet[kausi], vuo, np.nan)
        uusi.to_netcdf('flux1x1_%s.nc' %([:-3],kausi))
        uusi.close()
    vuo.close()
    kausidata.close()
    return 0

if __name__ == '__main__':
    main()

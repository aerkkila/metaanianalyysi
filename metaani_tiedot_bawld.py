#!/usr/bin/python3
import xarray as xr
import numpy as np
import pandas as pd
import config, sys
from metaani_tiedot_ import taul_pintaaloista

suot = ['bog','fen','tundra_wetland','permafrost_bog']

def main():
    baw = xr.open_dataset('./BAWLD1x1.nc')
    vuo = xr.open_dataarray(config.edgartno_dir + 'posterior.nc').sel({'lat':slice(baw.lat.min(),baw.lat.max())})
    ajat = xr.open_dataarray(config.tyotiedostot + 'FT_implementointi/FT_percents_pixel_ease_flag/DOY/winter_end_doy_2014.nc')
    baw = xr.where(ajat==ajat, baw, np.nan)
    ajat.close()
    wetl = baw['wetland']
    baw = xr.where(wetl>0.2, baw, np.nan)
    baw = baw[suot]
    for nimi in baw.keys():
        baw[nimi] = xr.where(baw[nimi]/wetl>=0.5, vuo, np.nan)
    vuo.close()
    if '-s' in sys.argv[1:]:
        with open('%s.txt' %(sys.argv[0][:-3]), 'w') as f:
            f.write(taul_pintaaloista(baw).to_string())
            f.write('\n')
    else:
        print(taul_pintaaloista(baw))
    baw.close()

if __name__ == '__main__':
    main()

#!/usr/bin/python3
import xarray as xr
import numpy as np
import locale, config

locale.setlocale(locale.LC_ALL,'')

def luokka_vuot(luokka):
    osuusraja = 0.7
    wetlandraja = 0.03
    vuot = xr.open_dataarray(config.edgartno_dir+'posterior.nc').mean(dim='time')
    baw = xr.open_dataset('BAWLD1x1.nc').\
        drop_vars(['bog','fen','tundra_wetland','permafrost_bog','bog+fen','tundra_wetland+permafrost_bog'])
    vuot = vuot.sel({'lat':slice(baw.lat.min(), baw.lat.max())})
    wlmaski = (baw['wetland'] >= wetlandraja).data.flatten()
    luokmaski = (baw[luokka] >= osuusraja).data.flatten()
    if not any(luokmaski):
        return
    met_luok = vuot.data.flatten()[(~wlmaski) & (luokmaski)]
    baw.close()
    v0 = '\033[0m'
    v1 = '\033[1;33m'
    v2 = '\033[1;36m'
    print(locale.format_string(
        '\n%s%s%s (%i pistettä)\n'
        '%sμ%s\t%.3e\n'
        '%sσ%s\t%.3e\n'
        '%s(5,95)%%%s\t(%.3e; %.3e)',
        (v2,luokka,v0,met_luok.size,
         v1,v0,np.mean(met_luok),
         v1,v0,np.std(met_luok),
         v1,v0,np.percentile(met_luok,5),np.percentile(met_luok,95))
    ))

if __name__ == '__main__':
    luokat = ['tundra_dry', 'boreal_forest', 'rockland', 'lake']
    for luokka in luokat:
        luokka_vuot(luokka)

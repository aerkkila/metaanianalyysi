#!/bin/env python

from matplotlib.pyplot import *
from netCDF4 import Dataset
import os, sys

smosdir = 'create_kausien_päivät'
kaudet = ['freezing', 'winter', 'thaw']
tapaht = ['start', 'end']

def main():
    vuosi = 2015
    ds_päivät = Dataset('kausien_päivät_int16.nc')
    vuodet = np.ma.getdata(ds_päivät['vuosi'][:].flatten())
    indvuosi = np.searchsorted(vuodet, vuosi)
    päivät = np.empty([len(kaudet), len(tapaht)], object)
    for ikausi, kausi in enumerate(kaudet):
        for itapahtuma, tapahtuma in enumerate(tapaht):
            dt = np.ma.getdata(ds_päivät['%s_%s' %(kausi, tapahtuma)][indvuosi,...].flatten()).astype(np.float32)
            täyttö = dt[0]
            dt[dt==täyttö] = np.nan
            päivät[ikausi,itapahtuma] = dt
    ds_päivät.close()

    ds = Dataset('%s/ftpercent/partly_frozen_percent_%i.nc' %(smosdir, vuosi-1))
    partly = np.ma.getdata(ds['data'][:])
    lat = np.ma.getdata(ds['lat'][:])
    lon = np.ma.getdata(ds['lon'][:])
    ds.close()
    ds = Dataset('%s/ftpercent/partly_frozen_percent_%i.nc' %(smosdir, vuosi))
    partly = np.concatenate([partly, np.ma.getdata(ds['data'][:])])
    ds.close()
    partly = np.reshape(partly, (partly.shape[0], np.product(partly.shape[1:])))

    var = Dataset('%s/ftpercent/frozen_percent_%i.nc' %(smosdir, vuosi-1))['data']
    frozen = np.ma.getdata(var[:])
    var = Dataset('%s/ftpercent/frozen_percent_%i.nc' %(smosdir, vuosi))['data']
    frozen = np.concatenate([frozen, np.ma.getdata(var[:])])
    frozen = np.reshape(frozen, (frozen.shape[0], np.product(frozen.shape[1:])))

    pisteitä = partly.shape[1]
    viivat = np.empty(3)

    tallenna = '-s' in sys.argv
    rcParams.update({'font.size':15, 'figure.figsize':(10,8)})
    for p in range(0, pisteitä, 20):
        if not (any(frozen[:,p]) and any(partly[:,p])):
            continue
        continueflag = 0
        for päivädata in päivät.flatten():
            if np.isnan(päivädata[p]):
                continueflag = 1 # oispa goto
                break
        if continueflag:
            continue

        print("%i° N, %i° E" %(lat[p//len(lon)], lon[p%len(lon)]))
        alku = int(päivät[0,0][p]) - 30
        loppu = int(päivät[2,0][p]) + 30
        aikaväli = np.arange(alku, loppu)
        plot(aikaväli, frozen[365+alku:365+loppu,p], color='k', label='frozen')
        plot(aikaväli, partly[365+alku:365+loppu,p], color='r', label='partly frozen')
        viivat[:] = [päivät[ind,0][p] for ind in range(len(kaudet))]
        yrange = gca().get_ylim()
        vlines(viivat, yrange[0], yrange[1], color='y', linewidth=3)
        text(np.mean([alku, viivat[0]]), yrange[1]+0.02, 'thaw %i' %(vuosi-1), ha='center')
        text(np.mean(viivat[[0,1]]), yrange[1]+0.02, 'freezing %i' %vuosi, ha='center')
        text(np.mean(viivat[[1,2]]), yrange[1]+0.02, 'winter %i' %vuosi, ha='center')
        text(np.mean([viivat[2], loppu]), yrange[1]+0.02, 'thaw %i' %vuosi, ha='center')
        gca().set_ylim(yrange)
        gca().set_xlim([alku,loppu])
        xlabel('day of year')
        legend()
        tight_layout()
        if tallenna:
            savefig('kuvia/kausien_määrittely.png')
            clf()
        else:
            show()
        break

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

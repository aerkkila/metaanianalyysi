#!/usr/bin/python3
import xarray as xr
import numpy as np
from wetlandvuo_voting import PINTAALA1x1
import sys

wnimet = ['bog', 'fen', 'marsh', 'tundra_wetland', 'permafrost_bog']

if __name__=='__main__':
    ds = xr.open_dataset('./prf_maa.nc').sel({'lat':slice(49.4,90)})
    lat = ds.lat.data
    alat = PINTAALA1x1(ds.lat.data)
    #taulukko = np.empty([len(wnimet),len(prf)], np.float32)
    tied = open('%s_1000km2.csv' %(sys.argv[0][:-3]), 'w')
    tied1 = open('%s_prosentti.csv' %(sys.argv[0][:-3]), 'w')
    tied.write(',non-permafrost,sporadic,discontinuous,continuous\n')
    tied1.write(',non-permafrost,sporadic,discontinuous,continuous\n')
    for w,wnimi in enumerate(wnimet):
        tied.write("%s" %(wnimi))
        tied1.write("%s" %(wnimi))
        for p in range(4):
            pintaala = 0
            pintaala1 = 0
            dt = ds[wnimi].mean(dim='time').data[p,...]
            for j in range(dt.shape[0]): #j on lat- eli myös alat-indeksi
                for i in range(dt.shape[1]):
                    pintaala += alat[j]*dt[j,i]
                    pintaala1 += alat[j]
            tied.write(",%i" %(int(np.round(pintaala*1e-3))))
            tied1.write(",%.3f" %(pintaala/pintaala1*100))
        tied.write('\n')
        tied1.write('\n')
    tied.close()
    tied1.close()

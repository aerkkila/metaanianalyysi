#!/bin/env python
from netCDF4 import Dataset
import numpy as np
import pymannkendall as fit1
import sys
# Piti muistaa vielä sklearn theil-sen

dir = '../'
kaudet = ['summer', 'freezing', 'winter']

# data annetaan r,t-muodossa
def sovita(data):
    trendit = np.empty(data.shape[0], np.float32)
    merkits = np.empty(data.shape[0], np.uint8)
    for r in range(data.shape[0]):
        print("%i \r" %r, end='')
        sys.stdout.flush()
        if np.sum(~np.isnan(data[r,:])) < 3:
            trendit[r], merkits[r] = (np.nan, 101)
            continue
        a = fit1.original_test(data[r,:])
        trendit[r] = a.slope
        merkits[r] = a.p*100
    print("\033[K", end='')
    return trendit, merkits

# data olkoon jo tallennusmuodossa
def tallenna(trendilista, merkitlista, muuttujanimet, lat, lon):
    da = Dataset('trendit.nc', 'w')
    tr = da.createGroup("/trendit")
    pr = da.createGroup("/p")
    lad = da.createDimension('lat',len(lat))
    lod = da.createDimension('lon',len(lon))
    v = da.createVariable('lat', 'f8', ('lat'))
    v[:] = lat[:]
    v = da.createVariable('lon', 'f8', ('lon'))
    v[:] = lon[:]
    for tre,mer,nimi in zip(trendilista,merkitlista,muuttujanimet):
        v = tr.createVariable(nimi, 'f4', ('lat','lon'))
        v[:] = tre
        v = pr.createVariable(nimi, 'u1', ('lat','lon'))
        v[:] = mer
    da.close()

def main():
    da = Dataset(dir+'kausien_päivät.nc', 'r')
    la = da['lat']
    lo = da['lon']
    trendit = np.empty(len(kaudet)*3, object)
    merkits = np.empty_like(trendit)
    muuttujat = np.empty(len(kaudet)*3, object)
    alkuloppu = np.empty(2, object)
    for i,kausi in enumerate(kaudet):
        for j,tapahtuma in enumerate(['_start','_end','_length']):
            ind = i*3+j
            muuttujat[ind] = kausi + tapahtuma
            print(muuttujat[ind])
            if j < 2:
                dt = np.ma.getdata(da[muuttujat[ind]][:])
                dt = dt.reshape([dt.shape[0], np.product(dt.shape[1:])])
                alkuloppu[j] = dt
            else:
                dt = alkuloppu[1] - alkuloppu[0]
            tre,mer = sovita(dt.transpose())
            trendit[ind] = tre.reshape([len(la),len(lo)])
            merkits[ind] = mer.reshape([len(la),len(lo)])
    tallenna(trendit, merkits, muuttujat, la, lo)

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        exit()

#!/usr/bin/env python
from netCDF4 import Dataset
import numpy as np
import luokat, re

def lue_data():
    ds = Dataset('ikirdata.nc')
    ikir = np.round(np.mean(np.ma.getdata(ds['luokka']), axis=0)).astype(np.int8).flatten()
    ds.close()

    ds = Dataset('köppen1x1maski.nc')
    köpp = np.zeros([len(luokat.köpp), 19800], bool)
    for u in ds.variables:
        for i,k in enumerate(luokat.köpp):
            if re.match(k,u):
                köpp[i,:] = köpp[i,:] | np.ma.getdata(ds[u]).flatten()
    ds.close()

    ds = Dataset('BAWLD1x1.nc')
    wetl = np.ma.getdata(ds['wetland']).flatten()
    ds.close()

    ds = Dataset('aluemaski.nc')
    maski = np.ma.getdata(ds['maski']).flatten().astype(bool)
    alat = np.load('pintaalat.npy')
    ds.close()

    return ikir[maski], köpp[:,maski], wetl[maski], alat[maski]

def main():
    ikir, köpp, wetl, alat = lue_data()
    taul = np.empty([len(luokat.ikir)+1, len(luokat.köpp)+1], int) # +1 wetland-luokasta

    for ki in range(len(luokat.köpp)):
        for ii in range(len(luokat.ikir)):
            taul[ii,ki] = np.sum(alat[(köpp[ki]) & (ikir==ii)]) * 1e-3
        # kosteikko tälle ilmastoluokalle
        tmpmaski = (köpp[ki]) & (wetl>=0.05)
        taul[ii+1,ki] = np.sum(alat[tmpmaski] * wetl[tmpmaski]) * 1e-3
    # kosteikot kaikille ikiroutaluokille
    for ii in range(len(luokat.ikir)):
        tmpmaski = (ikir==ii) & (wetl>=0.05)
        taul[ii,ki+1] = np.sum(alat[tmpmaski] * wetl[tmpmaski]) * 1e-3

    f = open('köppikir.tex', 'w')
    f.write('\\begin{tabular}{l|%s}\nArea (1000 km²)' %('r'*(len(luokat.köpp)+1)))
    for k in luokat.köpp:
        f.write(' & ' + k)
    f.write(' & wetland')
    f.write(' \\\\\n\\midrule\n')
    luokat.ikir.append('wetland')
    for ii,i in enumerate(luokat.ikir):
        f.write(i.replace('_',' '))
        for ki in range(len(luokat.köpp)+(ii<len(luokat.ikir)-1)):
            f.write(' & %i' %taul[ii,ki])
        f.write(' \\\\\n')
    f.write('\\end{tabular}\n')
    f.close()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

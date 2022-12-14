#!/bin/env python
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
    taul = np.empty([len(luokat.ikir)+2, len(luokat.köpp)+2], int) # +2 wetland-luokasta, alue ja osuus

    for ki in range(len(luokat.köpp)):
        for ii in range(len(luokat.ikir)):
            taul[ii,ki] = np.sum(alat[(köpp[ki]) & (ikir==ii)]) * 1e-3
        # kosteikko tälle ilmastoluokalle
        tmpmaski = (köpp[ki]) & (wetl>=0.05)
        taul[ii+1,ki] = np.sum(alat[tmpmaski] * wetl[tmpmaski]) * 1e-3
        taul[ii+2,ki] = taul[ii+1,ki] / np.sum(alat[köpp[ki]]) * 1e6
    # kosteikot kaikille ikiroutaluokille
    for ii in range(len(luokat.ikir)):
        tmpmaski = (ikir==ii) & (wetl>=0.05)
        taul[ii,ki+1] = np.sum(alat[tmpmaski] * wetl[tmpmaski]) * 1e-3
        taul[ii,ki+2] = taul[ii,ki+1] / np.sum(alat[ikir==ii]) * 1e6

    f = open('köppikir.tex', 'w')
    f.write('\\begin{tabular}{l|%s' %('r'*(len(luokat.köpp)+1)))
    f.write('|r}\nArea (1000 km²)')
    for k in luokat.köpp:
        f.write(' & ' + k)
    f.write(' & wetland & wetland ‰')
    f.write(' \\\\\n\\midrule\n')

    for ii,i in enumerate(luokat.ikir):
        f.write(i.replace('_',' '))
        for ki in range(len(luokat.köpp)+2):
            f.write(' & %i' %(taul[ii,ki]))
        f.write(' \\\\\n')

    f.write('wetland')
    for ki in range(len(luokat.köpp)):
        f.write(' & %i' %(taul[len(luokat.ikir),ki]))
    f.write(' & & \\\\\n')
    f.write(' \\midrule\n')

    f.write('wetland ‰')
    for ki in range(len(luokat.köpp)):
        f.write(' & %i' %(taul[len(luokat.ikir)+1,ki]))
    f.write(' & & \\\\\n')

    f.write('\\end{tabular}\n')
    f.close()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

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
    ds = Dataset('aluemaski.nc')
    maski = np.ma.getdata(ds['maski']).flatten().astype(bool)
    alat = np.load('pintaalat.npy')
    ds.close()
    return ikir[maski],köpp[:,maski],alat[maski]

def main():
    ikir,köpp, alat = lue_data()
    taul = np.empty([len(luokat.ikir), len(luokat.köpp)], int)
    for ki,k in enumerate(luokat.köpp):
        for ii,i in enumerate(luokat.ikir):
            taul[ii,ki] = np.sum(alat[(köpp[ki]) & (ikir==ii)]) * 1e-3
    f = open('köppikir.tex', 'w')
    f.write('\\begin{tabular}{l|%s}\nArea (1000 km²)' %('r'*len(luokat.köpp)))
    for k in luokat.köpp:
        f.write(' & ' + k)
    f.write(' \\\\\n\\midrule\n')
    for ii,i in enumerate(luokat.ikir):
        f.write(i.replace('_',' '))
        for ki,k in enumerate(luokat.köpp):
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

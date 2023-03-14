#!/bin/env python
from netCDF4 import Dataset
import numpy as np
import luokat, re
from pintaalat import pintaalat

lonpit = 360

def lue_data():
    ds = Dataset('ikirdata.nc')
    vuodet = np.ma.getdata(ds['vuosi']) >= 2011
    ikir = np.round(np.mean(np.ma.getdata(ds['luokka'])[vuodet, ...], axis=0)).astype(np.int8).flatten()
    ds.close()

    ds = Dataset('köppen1x1maski.nc')
    köpp = np.zeros([len(luokat.köpp), 19800], bool)
    for u in ds.variables:
        for i,k in enumerate(luokat.köppre):
            if re.match(k,u):
                köpp[i,:] = köpp[i,:] | np.ma.getdata(ds[u]).flatten()
    ds.close()

    ds = Dataset('BAWLD1x1.nc')
    wetl = np.ma.getdata(ds['wetland']).flatten()
    wetlmaski = np.ma.getdata(ds['pct']).flatten() # mikä osuus hilaruudusta on mukana bawld-luokituksessa
    ds.close()
    wetlmaski = wetlmaski > 0

    ds = Dataset('aluemaski.nc')
    maski = np.ma.getdata(ds['maski']).flatten().astype(bool)
    ds.close()

    alat = np.repeat(pintaalat, lonpit)

    return ikir[maski], köpp[:,maski], wetl[maski], alat[maski], wetlmaski[maski]

def main():
    ikir, köpp, wetl, alat, wetlmaski = lue_data()
    taul = np.empty([len(luokat.ikir)+3, len(luokat.köpp)+3], int) # +3 wetland-luokasta, alue ja osuus yhteensä ja bawld-alueella

    for ki in range(len(luokat.köpp)):
        for ii in range(len(luokat.ikir)):
            taul[ii,ki] = np.sum(alat[(köpp[ki]) & (ikir==ii)]) * 1e-3
        # kosteikko tälle ilmastoluokalle
        tmpmaski = köpp[ki] & (wetl>=0.05)
        wetmaski = köpp[ki] & wetlmaski
        taul[ii+1,ki] = np.sum(alat[tmpmaski] * wetl[tmpmaski]) * 1e-3 # wetland-pintaala
        taul[ii+2,ki] = np.sum(alat[wetmaski] * wetl[wetmaski]) / np.sum(alat[wetmaski]) * 1e3 # luokan varsinainen wetland-osuus ilman 0.05 rajaakaan
        taul[ii+3,ki] = taul[ii+1,ki] / np.sum(alat[köpp[ki]]) * 1e6 # käytetyn wetland alan ja luokan alan suhde
    # kosteikot kaikille ikiroutaluokille
    for ii in range(len(luokat.ikir)):
        ikirnyt = (ikir==ii)
        tmpmaski = ikirnyt & (wetl>=0.05)
        wetmaski = ikirnyt & wetlmaski
        taul[ii,ki+1] = np.sum(alat[tmpmaski] * wetl[tmpmaski]) * 1e-3
        taul[ii,ki+2] = np.sum(alat[wetmaski] * wetl[wetmaski]) / np.sum(alat[wetmaski]) * 1e3
        taul[ii,ki+3] = taul[ii,ki+1] / np.sum(alat[ikir==ii]) * 1e6

    f = open('yhdistelmäalueet.tex', 'w')
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
        f.write(' / %i' %(taul[ii,ki+1]))
        f.write(' \\\\\n')

    # pohjalle tulee ilmaston kosteikkoluokat
    f.write('wetland')
    for ki in range(len(luokat.köpp)):
        f.write(' & %i' %(taul[len(luokat.ikir),ki]))
    f.write(' & & \\\\\n')
    f.write(' \\midrule\n')

    f.write('wetland ‰')
    for ki in range(len(luokat.köpp)):
        f.write(' & %i' %(taul[len(luokat.ikir)+1,ki]))
        f.write(' / %i' %(taul[len(luokat.ikir)+2,ki]))
    f.write(' & & \\\\\n')

    f.write('\\end{tabular}\n')
    f.close()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

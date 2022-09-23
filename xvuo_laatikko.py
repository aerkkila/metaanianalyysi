#!/usr/bin/python3
from matplotlib.pyplot import *
import matplotlib as mpl
import numpy as np
from netCDF4 import Dataset
import sys, config
from laatikkokuvaaja import laatikkokuvaaja

def lpx(laji):
    da = Dataset(config.lpx_dir + 'LPX_area_%s.nc' %laji, 'r')
    d = np.mean(da['data'][:], axis=0)
    da.close()
    return d.flatten()

def main():
    #hyppy = 0.1
    rcParams.update({'figure.figsize':(6,6), 'font.size':15})
    argv1 = sys.argv[1] if len(sys.argv)>1 and sys.argv[1]!='-s' else 'wetland'
    s = Dataset('BAWLD1x1.nc','r')
    x = s['wetland'][:].flatten()
    lon,lat = (np.ma.getdata(s['lon'][:]), np.ma.getdata(s['lat'][:]))
    s.close()
    s = Dataset('aluemaski.nc', 'r')
    maski = np.ma.getdata(s['maski'][:]).flatten().astype(bool)
    s.close()
    lon,lat = np.meshgrid(lon,lat)
    lon,lat = (lon.flatten(), lat.flatten())
    painot = np.load('./pintaalat.npy', 'r')
    s = Dataset('flux1x1.nc', 'r')
    if '--priori' in sys.argv:
        y = np.mean(np.ma.getdata(s['flux_bio_prior'][:]), axis=0).flatten()*1e9
        nimipaate = '_prior'
    else:
        y = np.mean(np.ma.getdata(s['flux_bio_posterior'][:]), axis=0).flatten()*1e9
        nimipaate = ''
    s.close()
    laji = argv1
    if laji=='peat' or laji=='wetsoil' or laji=='inund':
        x1 = x
    for j in range(1):
        subplot(1,1,j+1)
        #alue = (lon<0) if j==0 else (lon>=0 if j==1 else lon<np.inf) # erikseen itäinen ja läntinen alue
        alue = maski# & alue
        x1 = x[alue][:]
        y1 = y[alue][:]
        painot1 = painot[alue][:]
        #aluenimi = ['west','east','all'][j]
        rajat = np.empty(11)
        rajat[0] = 0
        rajat[1] = 0.05
        for i in range(1,10):
            rajat[i+1] = i*0.1
        luokat = np.empty(len(rajat)-1, object)
        painostot = np.empty_like(luokat)
        for i in range(len(luokat)):
            alue = (rajat[i]<=x1) & (x1<rajat[i+1])
            luokat[i] = y1[alue]
            painostot[i] = painot1[alue]
        tulos = laatikkokuvaaja(luokat, xsij=rajat, avgmarker='o', fliers='.', painostot=painostot, sijainti='+')

        # suoran sovitus, joka on jäänyt turhaksi
        '''
        if j:
            a = np.vstack([np.ones(len(rajat)-1), rajat[:-1]+hyppy/2]).T
            kerr = np.linalg.lstsq(a, tulos['avg'], rcond=None)[0]
        else:
            a = np.vstack([np.ones(len(rajat)-3), rajat[:-3]+hyppy/2]).T
            kerr = np.linalg.lstsq(a, tulos['avg'][:-2], rcond=None)[0]
        plot(rajat[[0,-1]], rajat[[0,-1]]*kerr[1]+kerr[0], color='y')
        '''

        xticks(rotation=90)
        xlabel('fraction of %s' %(argv1))#, aluenimi))
        ylabel('flux (nmol m$^{-2}$ s$^{-1}$)')
        ax = gca()
        xsij = tulos['xsij1']
        _y0 = ax.transAxes.transform((0,1.01))[1]
        for i in range(len(xsij)):
            _x = ax.transData.transform((xsij[i],0))[0]
            _x,_y = ax.transData.inverted().transform((_x,_y0))
            text(_x, _y, "%.0f" %(np.sum(painostot[i])*1e-3), rotation=90, horizontalalignment='center')

        ax.twinx()
        m = 12.01 + 4*1.0079
        kerr = 1e-9 * 1e6 * 86000 * 365 # nmol, km²
        emissio = [np.sum(painostot[i]*luokat[i]*kerr*m*1e-12) for i in range(len(tulos['xsij1']))]
        emissio = np.cumsum(emissio)
        plot(tulos['xsij1'], emissio)
        ylim(bottom=0)
        ylabel('Cumulative emission (Tg)')

    tight_layout()
    if '-s' in sys.argv:
        savefig('kuvia/%s_%s%s.png' %(sys.argv[0][:-3], laji, nimipaate))
    else:
        show()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

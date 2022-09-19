#!/usr/bin/python3
#from wetlandtyypin_pisteet import valitse_painottaen
from matplotlib.pyplot import *
import matplotlib as mpl
import sys
from netCDF4 import Dataset
from sklearn.linear_model import LinearRegression
from copy import copy
import config

def aja(x0, y0, hyppy, xnimio=''):
    rajat = np.arange(0, max(x0)+hyppy, hyppy)
    luokat = np.empty(len(rajat)-1, object)
    for i in range(len(luokat)):
        luokat[i] = y0[(rajat[i]<=x0) & (x0<rajat[i+1])]

    suor = np.empty(len(luokat), object)
    laatikot = np.empty([len(luokat), 4], np.float32)
    avgs = np.empty([len(luokat)], np.float32)
    yerr_a = np.zeros([2,len(luokat)], np.float32)
    yerr_y = np.zeros([2,len(luokat)], np.float32)
    for i in range(len(luokat)):
        if len(luokat[i]):
            laatikot[i,:] = np.percentile(luokat[i], [5,25,75,95])
            avgs[i] = np.mean(luokat[i])
        else:
            laatikot[i,:] = np.nan
            avgs[i] = np.nan
        xalue = rajat[i+1]-rajat[i]
        lev = xalue/2
        x = xalue*i-lev/2
        y = laatikot[i,1]
        w = lev
        h = laatikot[i,2]-laatikot[i,1]
        suor[i] = mpl.patches.Rectangle((x,y),w,h)
        yerr_a[0,i] = laatikot[i,1]-laatikot[i,0]
        yerr_y[1,i] = laatikot[i,3]-laatikot[i,2]
    ax = gca()
    errorbar(rajat[:-1], laatikot[:,1], yerr=yerr_a, fmt='none', color='b')
    errorbar(rajat[:-1], laatikot[:,2], yerr=yerr_y, fmt='none', color='b')
    errorbar(rajat[:-1], avgs, xerr=lev/2, fmt='none', color='b')
    for i in range(len(luokat)):
        y = luokat[i][ (luokat[i]>laatikot[i,-1]) | (luokat[i]<laatikot[i,0]) ]
        plot(np.repeat(rajat[[i]], len(y)), y, '.', color='r')
    pc = mpl.collections.PatchCollection(suor, facecolor="#00000000", edgecolor='b')
    ax.add_collection(pc)
    xticks(rajat)
    ax.set_xlim(rajat[0]-lev/2-0.02, rajat[-2]+lev/2+0.02)
    ylabel('nmol m$^{-2}$ s$^{-1}$')
    return {'rajat':rajat, 'laatikot':laatikot, 'luokat':luokat, 'avgs':avgs}

def lpx(laji):
    da = Dataset(config.lpx_dir + 'LPX_area_%s.nc' %laji, 'r')
    d = np.mean(da['data'][:], axis=0)
    da.close()
    return d.flatten()

def main():
    rcParams.update({'figure.figsize':(13,6), 'font.size':15})
    kausi = 'whole_year'
    s = Dataset('BAWLD1x1.nc','r')
    dt = {'x':s['wetland'][:].flatten(), 'lon':s['lon'][:].flatten(), 'lat':s['lat'][:].flatten()}
    dt['lon'],dt['lat'] = np.meshgrid(dt['lon'],dt['lat'])
    dt['lon'] = dt['lon'].flatten()
    dt['lat'] = dt['lat'].flatten()
    s.close()
    s = Dataset('flux1x1.nc', 'r')
    if '--priori' in sys.argv:
        dt.update({'y':np.mean(s['flux_bio_prior'][:], axis=0).flatten()*1e9})
        nimipaate = '_prior'
    else:
        dt.update({'y':np.mean(s['flux_bio_posterior'][:], axis=0).flatten()*1e9})
        nimipaate = ''
    s.close()
    laji = sys.argv[1]
    if laji=='wetland':
        x0 = dt['x']
    elif laji=='peat' or laji=='wetsoil' or laji=='inund':
        x0 = lpx(laji)
    else:
        print('tuntematon: %s' %laji)
        sys.exit()
    for j in range(2):
        alue = (dt['lon']<0) if j==0 else (dt['lon']>=0 if j==1 else dt['lon']<np.inf) #erikseen itäinen ja läntinen alue
        x = copy(x0[alue])
        y = copy(dt['y'][alue])
        lat = copy(dt['lat'][alue])
        aluenimi = ['west','east'][j]
        for i,hyppy in enumerate([0.1]):
            subplot(1,2,j+i*2+1)
            data = aja(x, y, hyppy=hyppy, xnimio=aluenimi)
            y1 = np.max(y)+1
            rajat = data['rajat']
            laatikot = data['laatikot']
            luokat = data['luokat']
            for i in range(laatikot.shape[0]):
                text(rajat[i], y1, "%.0f" %(len(luokat[i])), rotation=90)
            xlabel(laji + ' (%s)' %(aluenimi))
            if hyppy<0.1:
                xticks(rotation=45)
            continue
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

        

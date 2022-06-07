#!/usr/bin/python3
from wetlandtyypin_pisteet import valitse_painottaen
from matplotlib.pyplot import *
import matplotlib as mpl
import sys

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
    ylabel('CH$_4$ flux')
    return {'rajat':rajat, 'laatikot':laatikot, 'luokat':luokat, 'avgs':avgs}

def hilan_korjaus(x, y, lat, monistus):
    indeksit = valitse_painottaen(lat, monistus)
    return x[indeksit], y[indeksit]

def lpx(laji):
    da = xr.open_dataarray(config.lpx_dir + 'LPX_area_%s.nc' %laji).mean(dim='time')
    return da.data.flatten() #tämä ja vuo pitäisi yhdistää ennen keskiarvoa

def main():
    rcParams.update({'figure.figsize':(12,10), 'font.size':15})
    kausi = 'whole_year'
    if '--priori' in sys.argv:
        dt = wld.tee_data2(kausi, priori=True)
        nimipaate = '_prior'
    else:
        dt = wld.tee_data2(kausi)
        nimipaate = ''
    laji = sys.argv[1]
    monistus = 8
    if laji=='wetland':
        x0 = dt['x'][:,dt['wlnimet'].index(laji)]
    elif laji=='peat' or laji=='wetsoil' or laji=='inund':
        x0 = lpx(laji)
        x0 = x0[dt['maski']]
    else:
        exit()
    for j in range(3):
        alue = (dt['lon']<0) if j==0 else (dt['lon']>=0 if j==1 else dt['lon']<np.inf) #erikseen itäinen ja läntinen alue
        x = copy(x0[alue])
        y = copy(dt['y'][alue])
        lat = copy(dt['lat'][alue])
        x,y = hilan_korjaus(x,y,lat,monistus)
        aluenimi = ['west','east','all'][j]
        for i,hyppy in enumerate([0.1]):
            subplot(2,2,j+i*2+1)
            data = aja(x, y, hyppy=hyppy, xnimio=aluenimi)
            y1 = np.max(y)+1
            rajat = data['rajat']
            laatikot = data['laatikot']
            luokat = data['luokat']
            for i in range(laatikot.shape[0]):
                text(rajat[i], y1, "%.0f" %(np.ceil(len(luokat[i])/monistus)), rotation=90)
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
    import wetlandvuo_data as wld
    import xarray as xr
    from sklearn.linear_model import LinearRegression
    from copy import copy
    import config
    main()

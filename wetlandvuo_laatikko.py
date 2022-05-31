#!/usr/bin/python3
from wetlandtyypin_pisteet import valitse_painottaen
from matplotlib.pyplot import *
import matplotlib as mpl
import sys

def aja(dt, laji='wetland', hyppy=0.1, alue=None, xnimio=''):
    monistus = 8
    wnimet = dt[2]
    wl = dt[0][:,wnimet.index(laji)]
    vuo = dt[1]
    if not alue is None:
        wl = wl[alue]
        vuo = vuo[alue]
        lat = dt[3][alue]
    if monistus != 1:
        indeksit = valitse_painottaen(lat, monistus)
    else:
        indeksit = np.arange(len(vuo))
    wl = wl[indeksit]
    vuo = vuo[indeksit]
    rajat = np.arange(0, 1+hyppy, hyppy)
    luokat = np.empty(len(rajat)-1, object)
    for i in range(len(luokat)):
        luokat[i] = vuo[(rajat[i]<=wl) & (wl<rajat[i+1])]

    suor = np.empty(len(luokat), object)
    listat = np.empty([len(luokat), 4], np.float32)
    avgs = np.empty([len(luokat)], np.float32)
    yerr_a = np.zeros([2,len(luokat)], np.float32)
    yerr_y = np.zeros([2,len(luokat)], np.float32)
    for i in range(len(luokat)):
        if len(luokat[i]):
            listat[i,:] = np.percentile(luokat[i], [5,25,75,95])
            avgs[i] = np.mean(luokat[i])
        else:
            listat[i,:] = np.nan
            avgs[i] = np.nan
        xalue = rajat[i+1]-rajat[i]
        lev = xalue/2
        x = xalue*i-lev/2
        y = listat[i,1]
        w = lev
        h = listat[i,2]-listat[i,1]
        suor[i] = mpl.patches.Rectangle((x,y),w,h)
        yerr_a[0,i] = listat[i,1]-listat[i,0]
        yerr_y[1,i] = listat[i,3]-listat[i,2]
    ax = gca()
    errorbar(rajat[:-1], listat[:,1], yerr=yerr_a, fmt='none', color='b')
    errorbar(rajat[:-1], listat[:,2], yerr=yerr_y, fmt='none', color='b')
    errorbar(rajat[:-1], avgs, xerr=lev/2, fmt='none', color='b')
    for i in range(len(luokat)):
        y = luokat[i][ (luokat[i]>listat[i,-1]) | (luokat[i]<listat[i,0]) ]
        plot(np.repeat(rajat[[i]], len(y)), y, '.', color='r')
    pc = mpl.collections.PatchCollection(suor, facecolor="#00000000", edgecolor='b')
    ax.add_collection(pc)
    y = np.max(vuo)+1
    for i in range(len(luokat)):
        text(rajat[i], y, "%i" %(int(len(luokat[i])/monistus)))
    ax.set_xlim(rajat[0]-lev/2-0.02, rajat[-2]+lev/2+0.02)
    ylabel('CH$_4$ flux')
    xlabel(laji + (' (%s)' %(xnimio)) if len(xnimio) else '')
    xticks(rajat)
    return {'rajat':rajat, 'listat':listat, 'avgs':avgs}

if __name__=='__main__':
    import wetlandvuo_data as wld
    import xarray as xr
    from sklearn.linear_model import LinearRegression
    rcParams.update({'figure.figsize':(12,12)})
    dt = wld.tee_data('whole_year')
    for j in range(2):
        alue = (dt[6] >= 0) if j else (dt[6] < 0) #erikseen itäinen ja läntinen alue
        aluenimi = ['west','east'][j]
        for i,hyppy in enumerate([0.1, 0.2]):
            subplot(2,2,j*2+i+1)
            data = aja(dt, 'wetland', hyppy=hyppy, alue=alue, xnimio=aluenimi)
            if hyppy<0.1:
                xticks(rotation=45)
            continue

            #sovittaa käyrät laatikkodiagrammeihin
            funktio = lambda x: x**2
            xplot = np.linspace(0,1,101).reshape([101,1])
            xplot = np.concatenate([xplot,funktio(xplot)], axis=1)
            yt = data['listat'].transpose()[[1,2],:]
            yt = np.insert(yt, 1, data['avgs'], axis=0)
            malli = LinearRegression()
            for y in yt:
                x = np.array(data['rajat']).reshape([len(data['rajat']),1])[:-1]
                x = np.concatenate([x,funktio(x)],axis=1)
                maski = y==y
                y = y[maski]
                x = x[maski,:]
                malli.fit(x,y)
                plot(xplot[:,0], malli.predict(xplot), color='y')
                print("%.4f\t" %(malli.predict(xplot[[-1],:])), end='')

            #käyrä alkuperäisen datan keskiarvosta
            wetl = dt[0][:,[-1]]
            vuo = dt[1]
            malli.fit(np.concatenate([wetl,funktio(wetl)],axis=1),vuo)
            plot(xplot[:,0], malli.predict(xplot), color='g')
            print("%.4f" %(malli.predict(xplot[[-1],:])[0]), end='')

            print("\b\n", end='')
    if '-s' in sys.argv:
        savefig('kuvia/%s.png' %(sys.argv[0][:-3]))
    else:
        show()

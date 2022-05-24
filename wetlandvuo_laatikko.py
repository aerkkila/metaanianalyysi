#!/usr/bin/python3
from wetlandtyypin_pisteet import valitse_painottaen
from matplotlib.pyplot import *
import matplotlib as mpl
import sys

def aja(dt, laji='wetland', hyppy=0.1, alue=None):
    monistus = 8
    wnimet = dt[2]
    wl = dt[0][:,wnimet.index(laji)]
    vuo = dt[1]
    if not alue is None:
        wl = wl[alue]
        vuo = vuo[alue]
        lat = dt[3][alue]
    indeksit = valitse_painottaen(lat, monistus)
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
    ylabel('vuo')
    xlabel(laji)
    xticks(rajat)
    return {'rajat':rajat, 'listat':listat, 'avgs':avgs}

if __name__=='__main__':
    import wetlandvuo_data as wld
    import xarray as xr
    from sklearn.linear_model import LinearRegression
    rcParams.update({'figure.figsize':(12,12)})
    if '-prf' in sys.argv:
        from copy import deepcopy
        dt = wld.tee_data('whole_year')
        prf = xr.open_dataset('prfdata_avg.nc')['luokka'].sel({'lat':slice(29.5, 83.5)})
        prf = prf.data.flatten()[dt[5]]
        for prflaji in range(2):
            dt1 = deepcopy(dt)
            if not prflaji:
                maski = prf==0
            else:
                maski = prf!=0
            for j in [0,1,3,4]:
                dt1[j] = dt[j][maski]
            ax = subplot(1,2,prflaji+1)
            data = aja(dt1, 'wetland')
            title(['non permafrost', 'some permafrost'][prflaji])
        show()
        exit()
    dt = wld.tee_data('freezing')
    for j in range(2):
        alue = (dt[6] >= 0) if j else (dt[6] < 0) #erikseen itäinen ja läntinen alue
        aluenimi = ['west','east'][j]
        for i,hyppy in enumerate([0.1, 0.2]):
            subplot(2,2,j*2+i+1)
            data = aja(dt, 'wetland', hyppy=hyppy, alue=alue)
            malli = LinearRegression()
            funktio = lambda x: x**2
            xplot = np.linspace(0,1,101).reshape([101,1])
            xplot = np.concatenate([xplot,funktio(xplot)], axis=1)
            wetl = dt[0][:,[-1]]
            vuo = dt[1]
            yt = data['listat'].transpose()[[1,2],:]
            yt = np.insert(yt, 1, data['avgs'], axis=0)
            if hyppy<0.1:
                xticks(rotation=45)
            continue

            #sovittaa käyrät laatikkodiagrammeihin
            for y in yt:
                break
                x = np.array(data['rajat']).reshape([len(data['rajat']),1])[:-1]
                x = np.concatenate([x,funktio(x)],axis=1)
                maski = y==y
                y = y[maski]
                x = x[maski,:]
                malli.fit(x,y)
                plot(xplot[:,0], malli.predict(xplot), color='y')
                print("%.4f\t" %(malli.predict(xplot[[-1],:])), end='')
            #malli.fit(np.concatenate([wetl,funktio(wetl)],axis=1),vuo)
            #plot(xplot[:,0], malli.predict(xplot), color='g')
            #print(malli.predict(xplot[[-1],:]))
            print("\b\n", end='')
    show()

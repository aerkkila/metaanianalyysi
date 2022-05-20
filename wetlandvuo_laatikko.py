#!/usr/bin/python3
from wetlandtyypin_pisteet import valitse_painottaen
from matplotlib.pyplot import *
import matplotlib as mpl
import sys

def aja(dt, laji='wetland'):
    monistus = 8
    wnimet = dt[2]
    wl = dt[0][:,wnimet.index(laji)]
    vuo = dt[1]
    indeksit = valitse_painottaen(dt[3], monistus)
    wl = wl[indeksit]
    vuo = vuo[indeksit]
    hyppy = 0.15
    rajat = np.arange(0, 1+hyppy, hyppy)
    luokat = np.empty(len(rajat)-1, object)
    for i in range(len(luokat)):
        luokat[i] = vuo[(rajat[i]<=wl) & (wl<rajat[i+1])]

    suor = np.empty(len(luokat), object)
    listat = np.empty([len(luokat), 4], np.float32)
    avgs = np.empty([len(luokat)], np.float32)
    xlis = np.empty(len(luokat), np.float32)
    yerr_a = np.zeros([2,len(luokat)], np.float32)
    yerr_y = np.zeros([2,len(luokat)], np.float32)
    xalue = 1/len(luokat)
    lev = 0.5 * xalue
    for i in range(len(luokat)):
        if len(luokat[i]):
            listat[i,:] = np.percentile(luokat[i], [5,25,75,95])
            avgs[i] = np.mean(luokat[i])
        else:
            listat[i,:] = np.nan
            avgs[i] = np.nan
        x = xalue*i-lev/2
        y = listat[i,1]
        w = lev
        h = listat[i,2]-listat[i,1]
        suor[i] = mpl.patches.Rectangle((x,y),w,h)
        yerr_a[0,i] = listat[i,1]-listat[i,0]
        yerr_y[1,i] = listat[i,3]-listat[i,2]
        xlis[i] = xalue*i
    ax = gca()
    errorbar(xlis, listat[:,1], yerr=yerr_a, fmt='none', color='b')
    errorbar(xlis, listat[:,2], yerr=yerr_y, fmt='none', color='b')
    errorbar(xlis, avgs, xerr=lev/2, fmt='none', color='b')
    for i in range(len(luokat)):
        y = luokat[i][ (luokat[i]>listat[i,-1]) | (luokat[i]<listat[i,0]) ]
        plot(np.repeat(xlis[[i]], len(y)), y, '.', color='r')
    pc = mpl.collections.PatchCollection(suor, facecolor="#00000000", edgecolor='b')
    ax.add_collection(pc)
    y = np.max(vuo)+1
    for i in range(len(xlis)):
        text(xlis[i], y, "%i" %(int(len(luokat[i])/monistus)))
    ax.set_xlim(rajat[0]-lev/2-0.02, rajat[-2]+lev/2+0.02)
    ylabel('vuo')
    xlabel(laji)

if __name__=='__main__':
    import wetlandvuo_data as wld
    import xarray as xr
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
            aja(dt1, 'wetland')
            title(['non permafrost', 'some permafrost'][prflaji])
    else:
        aja(wld.tee_data('whole_year'), 'wetland')
    show()

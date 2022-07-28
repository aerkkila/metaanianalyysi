import matplotlib as mpl
from matplotlib.pyplot import *
import numpy as np

#tämä korvattiin np.searchsorted-funktiolla
def search_ind(num, limits):
    length = len(limits)
    lower = 0
    upper = length-1
    while True:
        if upper-lower <= 1:
            return lower if num<limits[lower] else upper if num<limits[upper] else upper+1
        mid = (lower+upper)//2
        if num<limits[mid]:
            upper = mid-1
        elif num>limits[mid]:
            lower = mid+1
        else:
            return mid

def wpercentile(arr, painot, lista, on_valmis=False):
    ret = np.empty(len(lista))
    if on_valmis:
        rajat = painot
        sarr = arr
    else:
        jarj = np.argsort(arr)
        sarr = np.array(arr)[jarj]
        rajat = np.array(painot, np.float64)[jarj].cumsum()
        jakaja = rajat[-1] + (rajat[-1]-rajat[-2])
        for i in range(len(rajat)):
            rajat[i] /= jakaja
    for i,p0 in enumerate(lista):
        p           = p0/100
        ind         = np.searchsorted(rajat, p, side='right')
        alaraja     = rajat[0 if ind==0 else ind-1] # rajat-taulukko sisältää ylärajat
        ylaraja     = rajat[ind-1 if ind>=len(rajat) else ind]
        valin_osuus = (p-alaraja)/(ylaraja-alaraja)
        ylaraja_arr = sarr[ind-1] if ind>=len(sarr) else sarr[ind]
        alaraja_arr = sarr[ind] if ind==0 else sarr[ind-1]
        ret[i] = alaraja_arr + (ylaraja_arr-alaraja_arr)*valin_osuus
    return ret

def laatikkokuvaaja(lista, xsij=None, fliers='.', painostot=None, valmis=False, vari='b'):
    laatikoita = len(lista)
    if xsij is None:
        xsij = np.linspace(0,1,laatikoita+1)
    suor = np.empty(laatikoita, object)
    laatikot = np.empty([laatikoita, 4], np.float32)
    mediaanit = np.empty([laatikoita], np.float32)
    yerr_a = np.zeros([2,laatikoita], np.float32)
    yerr_y = np.zeros([2,laatikoita], np.float32)
    for i in range(laatikoita):
        if len(lista[i]):
            if(painostot is None):
                a = np.percentile(lista[i], [50,5,25,75,95])
                laatikot[i,:] = a[1:]
                mediaanit[i] = a[0]
            else:
                a = wpercentile(lista[i], painostot[i], [50,5,25,75,95], on_valmis=valmis)
                laatikot[i,:] = a[1:]
                mediaanit[i] = a[0]
        else:
            laatikot[i,:] = np.nan
            mediaanit[i] = np.nan
        xalue = xsij[i+1]-xsij[i]
        lev = xalue/2
        x = xalue*i-lev/2
        y = laatikot[i,1]
        w = lev
        h = laatikot[i,2]-laatikot[i,1]
        suor[i] = mpl.patches.Rectangle((x,y),w,h)
        yerr_a[0,i] = laatikot[i,1]-laatikot[i,0]
        yerr_y[1,i] = laatikot[i,3]-laatikot[i,2]
    ax = gca()
    errorbar(xsij[:-1], laatikot[:,1], yerr=yerr_a, fmt='none', color=vari)
    errorbar(xsij[:-1], laatikot[:,2], yerr=yerr_y, fmt='none', color=vari)
    errorbar(xsij[:-1], mediaanit, xerr=lev/2, fmt='none', color=vari, linewidth=2)
    #scatter(xsij[:-1], [np.mean(l) for l in lista], marker='x', color=vari)
    if fliers:
        for i in range(laatikoita):
            y = lista[i][ (lista[i]>laatikot[i,-1]) | (lista[i]<laatikot[i,0]) ]
            plot(np.tile(xsij[[i]], len(y)), y, fliers, color='r')
    pc = mpl.collections.PatchCollection(suor, facecolor="#00000000", edgecolor=vari)
    ax.add_collection(pc)
    xticks(xsij)
    ax.set_xlim(xsij[0]-lev/2-0.02, xsij[-2]+lev/2+0.02)
    return {'xsij':xsij, 'laatikot':laatikot, 'mediaanit':mediaanit}

def testi():
    painot = [1,1,2,2]
    taul   = [1,2,3,4]
    pros   = [30,50,70]
    print(wpercentile(taul,painot,pros))

if __name__=='__main__':
    testi()

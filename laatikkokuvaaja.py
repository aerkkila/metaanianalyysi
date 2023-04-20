import matplotlib as mpl
from matplotlib.pyplot import *
import numpy as np

# argumentti on_valmis=True tarkoittaa, että painot-taulukko ei sisällä painoja,
# vaan sisältää jo oikeat prosenttipisteet arr on järjestyksessä
def wpercentile(arr, painot, lista, on_valmis=False):
    ret = np.empty(len(lista))
    if on_valmis:
        rajat = painot
        sarr = arr
    else:
        # muodostetaan rajat ja sarr
        jarj = np.argsort(arr)
        sarr = np.array(arr)[jarj]
        nanind = np.searchsorted(sarr, np.nan)
        sarr = sarr[:nanind]
        rajat = np.array(painot, np.float64)[jarj][:nanind].cumsum()
        jakaja = rajat[-1] + (rajat[-1]-rajat[-2])
        for i in range(len(rajat)):
            rajat[i] /= jakaja
    for i,p0 in enumerate(lista):
        p           = p0/100
        ind         = np.searchsorted(rajat, p, side='right')
        # interpoloidaan lineaarisesti tarkemmin
        alaraja     = rajat[0 if ind==0 else ind-1] # rajat-taulukko sisältää ylärajat
        ylaraja     = rajat[ind-1 if ind>=len(rajat) else ind]
        välin_osuus = (p-alaraja)/(ylaraja-alaraja)
        yläraja_arr = sarr[ind-1] if ind>=len(sarr) else sarr[ind]
        alaraja_arr = sarr[ind] if ind==0 else sarr[ind-1]
        ret[i] = alaraja_arr + (yläraja_arr-alaraja_arr)*välin_osuus
    return ret

def mustavalko(rgb):
    avg = np.average(rgb, weights=[0.8,1,0.3])
    if avg > 0.2:
        return 'k'
    h = '#707080' # return harmaa aiheuttaisi varoituksen myöhemmin
    harmaa = mpl.colors.to_rgb(h)
    neliö = (rgb[0]-harmaa[0])**2 + (rgb[1]-harmaa[1])**2 + (rgb[2]-harmaa[2])**2
    return 'k' if neliö/3 < 0.3**2 else h

def laatikkokuvaaja(lista, xsij=None, fliers='.', painostot=None, valmis=False, vari='b', avgmarker=False, sijainti='0', fill=False):
    if fill:
        mustavalk = [mustavalko(mpl.colors.to_rgb(v)) for v in vari]
    laatikoita = len(lista)
    if xsij is None:
        xsij = np.linspace(0,1,laatikoita+1)

    xsij0 = xsij[:]
    xsij = xsij.copy()
    if sijainti=='-':
        for i in range(1,len(xsij)):
            xsij[i] = (xsij0[i-1]+xsij0[i]) / 2
        xsij[0] = xsij[1] - (xsij[2]-xsij[1])
    elif sijainti=='+':
        for i in range(len(xsij)-1):
            xsij[i] = (xsij0[i+1]+xsij0[i]) / 2
        xsij[-1] = xsij[-2] + (xsij[-2]-xsij[-3])

    suor = np.empty(laatikoita, object)
    laatikot = np.empty([laatikoita, 4], np.float32)
    mediaanit = np.empty([laatikoita], np.float32)
    levtaul = np.empty([laatikoita], np.float32)
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
        xalue = xsij0[i+1]-xsij0[i]
        lev = xalue/2
        levtaul[i] = lev
        x = xsij[i] - lev/2
        y = laatikot[i,1]
        w = lev
        h = laatikot[i,2]-laatikot[i,1]
        suor[i] = mpl.patches.Rectangle((x,y),w,h)
        yerr_a[0,i] = laatikot[i,1]-laatikot[i,0]
        yerr_y[1,i] = laatikot[i,3]-laatikot[i,2]
    ax = gca()
    errorbar(xsij[:-1], laatikot[:,1], yerr=yerr_a, fmt='none', ecolor=vari)
    errorbar(xsij[:-1], laatikot[:,2], yerr=yerr_y, fmt='none', ecolor=vari)
    errorbar(xsij[:-1], mediaanit, xerr=levtaul/2, fmt='none', ecolor=mustavalk if fill else vari, linewidth=2)
    if fliers:
        for i in range(laatikoita):
            y = lista[i][ (lista[i]>laatikot[i,-1]) | (lista[i]<laatikot[i,0]) ]
            plot(np.tile(xsij[[i]], len(y)), y, fliers, color='r')
    pc = mpl.collections.PatchCollection(suor, facecolor=vari if fill else "#00000000", edgecolor=vari)
    ax.add_collection(pc)
    if(avgmarker):
        avg = [np.mean(l) for l in lista]
        scatter(xsij[:-1], avg, marker=avgmarker, c=mustavalk if fill else vari, zorder=10)
    xticks(xsij0)
    ax.set_xlim(xsij[0]-lev/2-0.02, xsij[-2]+lev/2+0.02)
    ret = {'xsij':xsij0[:-1], 'xsij1':xsij[:-1], 'laatikot':laatikot, 'mediaanit':mediaanit}
    if avgmarker:
        ret.update({'avg':avg})
    return ret

def testi():
    painot = [1,1,2,2]
    taul   = [1,2,3,4]
    pros   = [30,50,70]
    print(wpercentile(taul,painot,pros))

if __name__=='__main__':
    testi()

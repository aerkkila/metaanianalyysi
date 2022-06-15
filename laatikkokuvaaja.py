import matplotlib as mpl
from matplotlib.pyplot import *
import numpy as np

def laatikkokuvaaja(lista, xsij=None, fliers='.'):
    laatikoita = len(lista)
    if xsij is None:
        xsij = np.linspace(0,1,laatikoita+1)
    suor = np.empty(laatikoita, object)
    laatikot = np.empty([laatikoita, 4], np.float32)
    avgs = np.empty([laatikoita], np.float32)
    yerr_a = np.zeros([2,laatikoita], np.float32)
    yerr_y = np.zeros([2,laatikoita], np.float32)
    for i in range(laatikoita):
        if len(lista[i]):
            laatikot[i,:] = np.nanpercentile(lista[i], [5,25,75,95])
            avgs[i] = np.nanmean(lista[i])
        else:
            laatikot[i,:] = np.nan
            avgs[i] = np.nan
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
    errorbar(xsij[:-1], laatikot[:,1], yerr=yerr_a, fmt='none', color='b')
    errorbar(xsij[:-1], laatikot[:,2], yerr=yerr_y, fmt='none', color='b')
    errorbar(xsij[:-1], avgs, xerr=lev/2, fmt='none', color='b')
    for i in range(laatikoita):
        y = lista[i][ (lista[i]>laatikot[i,-1]) | (lista[i]<laatikot[i,0]) ]
        plot(np.tile(xsij[[i]], len(y)), y, fliers, color='r')
    pc = mpl.collections.PatchCollection(suor, facecolor="#00000000", edgecolor='b')
    ax.add_collection(pc)
    xticks(xsij)
    ax.set_xlim(xsij[0]-lev/2-0.02, xsij[-2]+lev/2+0.02)
    return {'xsij':xsij, 'laatikot':laatikot, 'avgs':avgs}

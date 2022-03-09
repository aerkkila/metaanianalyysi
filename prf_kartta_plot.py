#!/usr/bin/python3
import numpy as np
from matplotlib.pyplot import *
import matplotlib
import prf_extent as prf

if __name__ == '__main__':
    rcParams.update({'font.size':13,'figure.figsize':(12,10)})
    ikirouta = prf.Prf('1x1').rajaa( (40,90) )
    ikirdata = np.mean(ikirouta.data,axis=0)
    ikirnum = prf.luokittelu_num(ikirdata) #ikirdatan käyttäminen päättyy
    luokkia=4
    cmap = matplotlib.cm.get_cmap('plasma_r',lut=luokkia)
    cmap = matplotlib.colors.ListedColormap([ cmap(i) for i in range(luokkia) ])
    imshow(ikirnum, cmap=cmap, interpolation='none')
    cbar=colorbar()
    vali = (luokkia-1)/luokkia
    cbar.set_ticks( np.linspace(vali/2,luokkia-1-vali/2,luokkia) )
    cbar.ax.set_yticklabels(prf.luokat)
    tight_layout()
    show()

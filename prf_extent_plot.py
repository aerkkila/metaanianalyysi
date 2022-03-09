#!/usr/bin/python3
import numpy as np
from matplotlib.pyplot import *
from prf_extent import lue_prf

def vaihda_vuosi(maara:int):
    global vuosi_ind
    if vuosi_ind + maara < tif['data'].shape[0] and vuosi_ind + maara >= 0:
        vuosi_ind += maara
    olio.set_data(tif['data'][vuosi_ind].reshape(tif['muoto']))
    title(str(tif['vuodet'][vuosi_ind]))
    draw()

def nappainfunk(tapaht):
    if tapaht.key == 'right':
        vaihda_vuosi(1)
    elif tapaht.key == 'left':
        vaihda_vuosi(-1)

if __name__ == '__main__':
    tif = lue_prf()
    vuosi_ind = 0
    fig = figure(figsize=(12,10))
    olio = imshow( np.reshape( tif['data'][vuosi_ind], tif['muoto'] ), cmap=get_cmap('rainbow') )
    title(str(tif['vuodet'][vuosi_ind]))
    colorbar()
    tight_layout()
    fig.canvas.mpl_connect('key_press_event',nappainfunk)
    show()

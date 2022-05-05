#!/usr/bin/python3
import numpy as np
from matplotlib.pyplot import *
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.widgets import CheckButtons, RadioButtons
import sys

#a/b, missä a on summa jakajaa pienempien dt:n pisteitten etäisyydestä jakajaan
#     ja b on summa kaikkien pisteitten absoluuttisista etäisyyksistä jakajaan
#     jakajan ollessa keskiarvo tämä siis palauttaa 0,5 jne.
def massojen_suhde(jakaja, dt):
    maski = dt<jakaja
    a = np.sum(jakaja[maski] - dt[maski])
    maski = ~maski
    b = a + np.sum(dt[maski] - jakaja[maski])
    return a/b

nimet = ['bog', 'fen', 'marsh', 'tundra_wetland', 'permafrost_bog', 'wetland']

def vntafunktio(nimio):
    actives = vntanapit.get_status()
    for i in range(len(actives)):
        piirros[i].set_visible(actives[i])
    draw()
    return

def tyyppifunktio(nimio):
    global t_ind
    t_ind = nimet.index(nimio)
    piirra()
    return

def piirra():
    global piirretty, datax, datay, yhat, yhat_vot, yhat_raj
    wetl = datax[:,-1]
    dtx = datax[:,t_ind]
    dtyh = yhat[t_ind,...]
    dtyh_vot = yhat_vot[t_ind,...]
    dtyh_raj = yhat_raj[t_ind,...]
    dty = [datay, dtyh, dtyh_vot, dtyh_raj[r_ind0,:], dtyh_raj[r_ind1,:]]
    if not piirretty:
        piirros[0], = plot(dtx,wetl,datay,'.', color='b', label='arvot', markersize=7)
        piirros[1], = plot(dtx,wetl,dtyh,'.', color='g', label='arvio')
        piirros[2], = plot(dtx,wetl,dtyh_vot,'.', color='c', label='joukkion avg')
        piirros[3], = plot(dtx,wetl,dtyh_raj[r_ind0,:],'.', color='r', label='%i %%' %(rajat[r_ind0]))
        piirros[4], = plot(dtx,wetl,dtyh_raj[r_ind1,:],'.', color='y', label='%i %%' %(rajat[r_ind1]))
        xlabel(nimet[t_ind])
        ylabel('wetland')
        ax.set_zlabel('vuo')
        legend(loc='upper left')
        piirretty = True
        vntafunktio('')
        show()
        return
    for i in range(len(piirros)):
        piirros[i].set_data(dtx,wetl)
    piirros[0].set_3d_properties(datay)
    piirros[1].set_3d_properties(dtyh)
    piirros[2].set_3d_properties(dtyh_vot)
    piirros[3].set_3d_properties(dtyh_raj[r_ind0,:])
    piirros[4].set_3d_properties(dtyh_raj[r_ind1,:])
    ax.set_xlabel(nimet[t_ind])
    ax.auto_scale_xyz(dtx, wetl, dty)
    draw()
    return

def main():
    global r_ind0, r_ind1, ax, piirretty, piirros
    global datax, datay, yhat, yhat_vot, yhat_raj, rajat, t_ind
    global vntanapit, tyyppinapit    
    rcParams.update({'figure.figsize':(12,7), 'font.size':10})
    piirretty = False
    r_ind0 = 9
    r_ind1 = -10
    tmp = False
    if '-tmp' in sys.argv:
        dt = np.load('./wetlandvuo_voting_data_tmp.npz')
        tmp = True
    else:
        dt = np.load('./wetlandvuo_voting_data.npz')
    datax = dt['x']
    datay = dt['y']
    yhat = dt['yhat']
    yhat_vot = dt['yhat_voting']
    yhat_raj = dt['yhat_raja']
    rajat = dt['rajat']
    dt.close()

    for i,nimi in enumerate(nimet[:-1]):
        print('\033[32m%s\033[0m' %(nimi))
        print('selitetty varianssi(yksi,joukkio) = %.4f\t%.4f' %(1-np.mean((yhat[i,...]-datay)**2)/np.var(datay),
                                                                 1-np.mean((yhat_vot[i,...]-datay)**2/np.var(datay))))
        print(rajat[r_ind0], massojen_suhde(yhat_raj[i,r_ind0,:],datay))
        print(rajat[r_ind1], massojen_suhde(yhat_raj[i,r_ind1,:],datay))

    vntanapit = CheckButtons(
        ax = axes([0.0, 0.1, 0.1, 0.6]),
        labels = ('data','yksi','joukkio','matala','korkea'),
        actives = (1,1,0,1,1)
    )
    tyyppinapit = RadioButtons(
        ax = axes([0.1, 0.1, 0.14, 0.6]),
        labels = nimet[:-1]
    )
    ax = axes([0.25,0.02,0.72,0.93], projection='3d')
    piirros = np.empty(len(vntanapit.get_status()), object)
    vntanapit.on_clicked(vntafunktio)
    tyyppinapit.on_clicked(tyyppifunktio)
    t_ind = 0
    piirra()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit()

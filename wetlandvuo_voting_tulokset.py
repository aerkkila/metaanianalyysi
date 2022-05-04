#!/usr/bin/python3
import numpy as np
from wetlandvuo_data import tee_data
from matplotlib.pyplot import *
from mpl_toolkits.mplot3d import Axes3D
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

def yksi_tyyppi(datax,datay,yhat,yraja,nimi,rajat):
    ehi0 = 5
    ehi1 = -6
    wetl = datax[:,-1]
    datax = datax[:,0]
    ax = subplot(121, projection='3d')
    plot(datax,wetl,datay,'.', color='b', label='arvot', markersize=7)
    plot(datax,wetl,yhat,'.', color='g', label='avg arvio')
    plot(datax,wetl,yraja[ehi0,:],'.', color='r', label='%i %%' %(rajat[ehi0]))
    plot(datax,wetl,yraja[ehi1,:],'.', color='y', label='%i %%' %(rajat[ehi1]))
    xlabel(nimi)
    legend(loc='upper left')
    ax = subplot(122)
    plot(wetl,datay,'.', color='b', label='arvot', markersize=7)
    plot(wetl,yhat,'.', color='g', label='avg arvio')
    plot(wetl,yraja[ehi0,:],'.', color='r', label='%i %%' %(rajat[ehi0]))
    plot(wetl,yraja[ehi1,:],'.', color='y', label='%i %%' %(rajat[ehi1]))
    xlabel('wetland')
    legend(loc='upper left')
    
    tight_layout()
    #savefig("kuvia/%s_%s.png" %(sys.argv[0][:-3],nimi))
    show()
    clf()

    print('\033[32m%s\033[0m' %(nimi))
    print('selitetty varianssi = %.4f' %(1-np.mean((yhat-datay)**2)/np.var(datay)))
    print(rajat[ehi0], massojen_suhde(yraja[ehi0,:],datay))
    print(rajat[ehi1], massojen_suhde(yraja[ehi1,:],datay))
    return

def main():
    nimet = ['bog', 'fen', 'marsh', 'tundra_wetland', 'permafrost_bog', 'wetland']
    rcParams.update({'figure.figsize':(14,10), 'font.size':12})
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
        yksi_tyyppi(datax, datay, yhat_vot[i,...], yhat_raj[i,...], nimi, rajat)

if __name__=='__main__':
    main()

#!/usr/bin/python3
import numpy as np
from matplotlib.pyplot import *
from wetlandvuo_data import tee_data
from matplotlib.pyplot import *
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

def yksi_tyyppi(yh,eh,nimi,er,datax,wetl,datay):
    #alussa: eh: pisteet, raja
    eh = eh.transpose()
    print('\033[32m%s\033[0m' %(nimi))
    fig,ax = subplots(1,2)
    sca(ax.flatten()[0])
    plot(datax,datay,'.', color='b', label='arvot')
    plot(datax,yh,'.', color='g', label='avg arvio')
    plot(datax,eh[5,:],'.', color='r', label='%i %%' %(er[5]))
    plot(datax,eh[-6,:],'.', color='y', label='%i %%' %(er[-6]))
    xlabel(nimi)
    legend(loc='upper left')
    sca(ax.flatten()[1])
    plot(wetl,datay,'.', color='b', label='arvot')
    plot(wetl,yh,'.', color='g', label='avg arvio')
    plot(wetl,eh[5,:],'.', color='r', label='%i %%' %(er[5]))
    plot(wetl,eh[-6,:],'.', color='y', label='%i %%' %(er[-6]))
    xlabel('wetland')
    legend(loc='upper left')
    
    tight_layout()
    show()
    return

def main():
    rcParams.update({'figure.figsize':(14,10)})
    if '-p' in sys.argv:
        dt = np.load('./wetvotdat_painottamaton.npz', allow_pickle=True)
    else:
        dt = np.load('./wetlandvuo_voting_data.npz', allow_pickle=True)
    yhl = dt['yhatut_list']
    ehl = dt['ehatut_list']
    er = dt['ennusrajat']
    dt.close()
    dt = tee_data('numpy')
    datax = dt[0] #(pisteet, wetltyypit)
    datay = dt[1]
    nimet = dt[2]
    wetl = np.array(np.sum(datax, axis=1))

    for i in range(len(yhl)):
        yksi_tyyppi(yhl[i],ehl[i],nimet[i],er,datax[:,i],wetl,datay)

if __name__=='__main__':
    main()

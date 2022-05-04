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
    ehi0 = 5
    ehi1 = -6
    fig,ax = subplots(1,2)
    sca(ax.flatten()[0])
    plot(datax,datay,'.', color='b', label='arvot', markersize=7)
    plot(datax,yh,'.', color='g', label='avg arvio')
    plot(datax,eh[ehi0,:],'.', color='r', label='%i %%' %(er[ehi0]))
    plot(datax,eh[ehi1,:],'.', color='y', label='%i %%' %(er[ehi1]))
    xlabel(nimi)
    legend(loc='upper left')
    sca(ax.flatten()[1])
    plot(wetl,datay,'.', color='b', label='arvot', markersize=7)
    plot(wetl,yh,'.', color='g', label='avg arvio')
    plot(wetl,eh[ehi0,:],'.', color='r', label='%i %%' %(er[ehi0]))
    plot(wetl,eh[ehi1,:],'.', color='y', label='%i %%' %(er[ehi1]))
    xlabel('wetland')
    legend(loc='upper left')
    
    tight_layout()
    savefig("kuvia/%s_%s.png" %(sys.argv[0][:-3],nimi))
    clf()

    print('\033[32m%s\033[0m' %(nimi))
    print('selitetty varianssi: %.4f' %(1-np.mean((yh-datay)**2)/np.var(datay)))
    print(er[ehi0], massojen_suhde(eh[ehi0,:],datay))
    print(er[ehi1], massojen_suhde(eh[ehi1,:],datay))
    return

def main():
    rcParams.update({'figure.figsize':(14,10), 'font.size':12})
    tmp = False
    if '-p' in sys.argv:
        dt = np.load('./wetvotdat_painottamaton.npz', allow_pickle=True)
    elif '-tmp' in sys.argv:
        dt = np.load('./wetlandvuo_voting_data_tmp.npz', allow_pickle=True)
        tmp = True
    else:
        dt = np.load('./wetlandvuo_voting_data.npz', allow_pickle=True)
    yhl = dt['yhatut_list']
    ehl = dt['ehatut_list']
    er = dt['ennusrajat']
    dt.close()
    dt = tee_data('numpy', tmp)
    datax = dt[0] #(pisteet, wetltyypit)
    datay = dt[1]
    nimet = dt[2]
    wetl = np.array(np.sum(datax, axis=1))

    for i in range(len(yhl)):
        yksi_tyyppi(yhl[i],ehl[i],nimet[i],er,datax[:,i],wetl,datay)

if __name__=='__main__':
    main()

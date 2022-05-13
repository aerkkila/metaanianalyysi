#!/usr/bin/python3
import pandas as pd
from matplotlib.pyplot import *
from wetlandvuo_data import tee_data

#luetaan yhtälöt pisteitten valinnalle ja muodostetaan datamaskit
def tee_maskit(dt,nimet):
    yht = pd.read_csv('wetlandtyypin_pisteet.csv', index_col=0)
    maskit = np.empty([len(yht.index),dt.shape[0]], bool)
    for i in range(len(yht.index)):
        #vähintään kynnysarvon verran luokkaa ja enintään residuaalin päässä sovitussuorasta
        maskit[i,:] = (dt[:,i]>=yht.loc[nimet[i],'kynnysarvo']) & \
            ((yht.loc[nimet[i],'a0']+yht.loc[nimet[i],'a1']*dt[:,i]-dt[:,-1])**2 <= yht.loc[nimet[i],'resid']**2)
    return maskit

class Yhtalot():
    def __init__(self):
        self.yht = pd.read_csv('wetlandtyypin_pisteet.csv', index_col=0)
    def __call__(self,i):
        return lambda x: self.yht.iloc[i,0]+self.yht.iloc[i,1]*x
    def __str__(self):
        return self.yht.to_string()

def main():
    dt = tee_data()
    datax = dt[0]
    nimet = dt[2]
    maskit = tee_maskit(datax,nimet)
    yht = Yhtalot()
    print(yht)
    for i in range(len(maskit)):
        plot(datax[~maskit[i,:],i], datax[~maskit[i,:],-1], '.', color='r')
        plot(datax[maskit[i,:],i], datax[maskit[i,:],-1], '.', color='b')
        plot([0,1], yht(i)(np.array([0,1])), color='g')
        show()
    return

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

#!/usr/bin/python3
import pandas as pd
import numpy as np
from matplotlib.pyplot import *
import sys

def main():
    df = pd.read_csv('./wetlandvuo_randomforest_data.csv')
    dt = np.load('./wetlandvuo_randomforest.npz')
    #alussa: toistoja, rajat, indeksi
    rhattu = dt['rajat_hattu'].transpose(1,0,2)
    #for suo in df.drop('vuo',axis=1):
    print('\033[1;32mKaiken kaikkiaan\033[0m')
    summa = np.zeros(len(dt['rajat']))
    #for r in range(0,len(dt['rajat']),7):
    for r in [0,1,4,9,24,49,74,89,94,97,98]:
        for t in range(rhattu.shape[1]):
            summa[r] += np.mean(df.vuo<=rhattu[r,t,:])
        summa[r] /= rhattu.shape[1]
        print(dt['rajat'][r],summa[r])

    for suo in df.drop('vuo',axis=1):
        osraja = np.percentile(df[suo], 90)
        maski = df[suo] >= osraja
        print('\033[1;32mfrac(%s) ≥ %.4f\033[0m' %(suo, osraja))
        summa = np.zeros(len(dt['rajat']))
        for r in range(len(dt['rajat'])):
            for t in range(rhattu.shape[1]):
                summa[r] += np.mean(df.vuo[maski]<=rhattu[r,t,:][maski])
            summa[r] /= rhattu.shape[1]
        for r in [0,1,4,9,24,49,74,89,94,97,98]:
            print(dt['rajat'][r],summa[r])
        plot(dt['rajat'], summa)
        plot(dt['rajat'], dt['rajat']/100)
        title(suo)
        xlabel('percentile')
        ylabel('mean(ŷ≤y)')
        tight_layout()
        show()

if __name__=='__main__':
    sys.exit(main())

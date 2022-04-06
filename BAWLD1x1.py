#!/usr/bin/python3
import os, sys
import maalajit as ml

def main():
    turha,maa = ml.lue_maalajit(ml.tunnisteet.keys(),alkup=False)
    ml.maalajien_yhdistamiset(maa)
    maa *= 0.01
    maa.to_netcdf('%s.nc' %sys.argv[0][:-3])

if __name__ == '__main__':
    main()

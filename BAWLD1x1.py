#!/usr/bin/python3
import sys
import maalajit as ml

if __name__ == '__main__':
    turha,maa = ml.lue_maalajit(ml.tunnisteet_kaikki.keys(),alkup=False)
    ml.maalajien_yhdistamiset(maa)
    maa *= 0.01
    maa.to_netcdf('%s.nc' %sys.argv[0][:-3])

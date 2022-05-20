#!/usr/bin/python3
import maalajit as ml

if __name__ == '__main__':
    maat = ml.lue_maalajit(ml.tunnisteet_kaikki.keys())
    for maa,nimi in zip(maat, ['BAWLD05x05.nc', 'BAWLD1x1.nc']):
        ml.maalajien_yhdistamiset(maa)
        maa *= 0.01
        maa.to_netcdf(nimi)

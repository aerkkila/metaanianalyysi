#!/usr/bin/python3
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import cartopy.crs as ccrs
import cartopy.feature as feature
import sys
from config import LPX2019_t, LPX2019_m

def argumentit(args):
    global tallenna, muuttuja
    tallenna=False; muuttuja=LPX2019_m
    i=1
    while i < len(args):
        if args[i] == '-s':
            tallenna = True
        elif args[i] == '-m':
            i+=1
            muuttuja = args[i]
        i+=1
    return

kauden_nimet = ['whole year', 'summer', 'winter']
i_kausi=0

def kauden_kohdat(ajat,kauden_nimi):
    kaudet = { 'summer':(6,9), 'winter':(3,12), 'whole year':(1,13) }
    kohdat = ( kaudet[kauden_nimi][0] <= ajat.month ) & ( ajat.month < kaudet[kauden_nimi][1] )
    if kauden_nimi == 'winter':
        return ~kohdat
    return kohdat

class Piirtaja():
    def __init__(self):
        self.platecarree = ccrs.PlateCarree()
        self.kattavuus   = [-180,180,40,90]
        self.projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    def __call__(self,data):
        maski_lat = ( (data.lat>=self.kattavuus[2]) & (data.lat<=self.kattavuus[3]) )
        datamin = data.data[maski_lat].min()
        datamax = data.data[maski_lat].max()
        plt.clf()
        ax = plt.axes([0,0.02,0.94,0.95], projection=self.projektio)
        ax.set_extent(self.kattavuus,self.platecarree)
        ax.coastlines()
        ax.add_feature(feature.BORDERS)
        data.plot.pcolormesh(x='lon', y='lat', ax=ax, transform=ccrs.PlateCarree(),
                             cmap='seismic', norm=mcolors.DivergingNorm(0,max(datamin*6,-datamax),datamax))
        ax.set_title('%s mean flux' %kauden_nimet[i_kausi])
        plt.draw()

def vaihda_kausi(hyppy):
    global i_kausi, k_data
    i_kausi = (i_kausi + len(kauden_nimet) + hyppy) % len(kauden_nimet)
    k_data = data0[ kauden_kohdat(ajat,kauden_nimet[i_kausi]) ].mean(dim='time')
    piirtaja(k_data)

def nappainfunk(tapaht):
    if tapaht.key == 'right' or tapaht.key == 'o' or tapaht.key == 'i':
        vaihda_kausi(1)
    elif tapaht.key == 'left' or tapaht.key == 'g' or tapaht.key == 'a':
        vaihda_kausi(-1)

def main():
    global tallenna, muuttuja, k_data, ajat, data0
    argumentit(sys.argv)
    
    plt.rcParams.update({'font.size':18,'figure.figsize':(12,10)})
    
    data0 = xr.open_dataset(LPX2019_t)[muuttuja]
    ajat = pd.to_datetime(data0.time.data)

    fig = plt.figure()

    vaihda_kausi(0)

    if tallenna:
        while True:
            plt.savefig('kuvia/%s_%i.png' %(sys.argv[0][:-3],i_kausi) )
            if i_kausi == len(kauden_nimet)-1:
                exit()
            vaihda_kausi(1)
    else:
        fig.canvas.mpl_connect('key_press_event',nappainfunk)
        plt.show()

if __name__ == '__main__':
    piirtaja = Piirtaja()
    main()

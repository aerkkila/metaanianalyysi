#!/usr/bin/python3
import cartopy.crs as ccrs
from matplotlib.pyplot import *
from netCDF4 import Dataset
import matplotlib.patches as patches
import matplotlib, re, sys

luokat   = ['C.b', 'D.a', 'D.b', 'D.c', 'D.d', 'ET', 'EF']
cmapnimi = "jet"

def piirra_nopeasti(luokitus, cmap):
    lon_, lat_ = np.meshgrid(lon, lat)
    for i,luokka in enumerate(luokat):
        maski = luokitus[i,:].reshape([len(lat), len(lon)])
        plot(lon_[maski], lat_[maski], '.', color=cmap(i), label=luokka, transform=platecarree, alpha=0.8, markersize=3)

def piirra_tarkasti(luokitus, cmap, ax):
    dx = lon[1]-lon[0]
    dy = lat[1]-lat[0]
    for i,luokka in enumerate(luokat):
        maski_2D = luokitus[i,:].reshape([len(lat),len(lon)])
        plot(-1,-1,'.',markersize=24,color=cmap(i),label=luokka,transform=platecarree) #Ei piirrä mitään, vaan on legend-funktiota varten.
        #Piirtämistä nopeutetaan yhdistämällä vierekkäiset saman luokan pisteet yhdeksi suorakulmioksi.
        ensimmainen=0
        for lat1,maski in zip( lat, maski_2D ):
            if lat1 < 0:
                continue
            j=0
            while( j<len(lon) ):
                while( j<len(lon) ): #haetaan suorakulmion alkupiste
                    if maski[j]:
                        break
                    j+=1
                else:
                    break
                alku=j
                while( j<len(lon) ): #haetaan suorakulmion loppupiste
                    if not maski[j]:
                        break
                    j+=1
                ax.add_patch(patches.Rectangle( (lon[alku],lat1), dx*(j-alku),dy, color=cmap(i), transform=platecarree ))

def main():
    global lon, lat, platecarree
    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    kattavuus   = [-180,180,40,90]
    rcParams.update({'font.size':18,'figure.figsize':(12,10)})
    
    luokitus_ = Dataset('köppen1x1maski.nc', 'r')
    luokitus = np.zeros([len(luokat), 19800], bool)
    for k in luokitus_.variables:
        for li,l in enumerate(luokat):
            if re.match(l,k):
                luokitus[li,:] = luokitus[li,:] | np.ma.getdata(luokitus_[k]).flatten()[:]
    lon = np.ma.getdata(luokitus_['lon']).flatten()
    lat = np.ma.getdata(luokitus_['lat']).flatten()
    luokitus_.close()

    fig = figure()
    ax = axes([0,0.03,0.95,0.94], projection=projektio)
    ax.coastlines()
    ax.set_extent(kattavuus, platecarree)
    cmap = matplotlib.cm.get_cmap(cmapnimi, len(luokat))
    if '-f' in sys.argv:
        piirra_nopeasti(luokitus,cmap)
    else:
        piirra_tarkasti(luokitus,cmap,ax)
    leg=legend(loc='center left', bbox_to_anchor=(1,0.5))
    if '-s' in sys.argv:
        savefig('kuvia/%s.png' %(sys.argv[0][:-3]))
        clf()
    else:
        show()

if __name__ == '__main__':
    main()

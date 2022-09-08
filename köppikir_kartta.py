#!/usr/bin/python3
import cartopy.crs as ccrs
from matplotlib.pyplot import *
from netCDF4 import Dataset
import matplotlib.patches as patches
import matplotlib, re, sys, luokat

luokat_köpp = ['C.b', 'D.a', 'D.b', 'D.c', 'D.d', 'ET']
luokat_ikir = luokat.ikir
cmapnimi = "jet"

def piirrä_nopeasti(luokitus, cmap, luokat_):
    lon_, lat_ = np.meshgrid(lon, lat)
    for i,luokka in enumerate(luokat_):
        maski = luokitus[i,:].reshape([len(lat), len(lon)])
        plot(lon_[maski], lat_[maski], '.', color=cmap(i), label=luokka, transform=platecarree, alpha=0.8, markersize=3)

def piirrä_tarkasti(luokitus, cmap, ax, luokat_, värin_alku):
    dx = lon[1]-lon[0]
    dy = lat[1]-lat[0]
    for i,luokka in enumerate(luokat_):
        maski_2D = luokitus[i,:].reshape([len(lat),len(lon)])
        # Ei piirrä mitään, vaan on legend-funktiota varten.
        plot(-1,-1,'.',markersize=24,color=cmap(i+värin_alku),label=luokka.replace('_',' '),transform=platecarree)
        # Piirtämistä nopeutetaan yhdistämällä vierekkäiset saman luokan pisteet yhdeksi suorakulmioksi.
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
                ax.add_patch(patches.Rectangle((lon[alku],lat1), dx*(j-alku),dy, color=cmap(i+värin_alku), transform=platecarree))

def main():
    global lon, lat, platecarree
    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    kattavuus   = [-180,180,40,90]
    rcParams.update({'font.size':18,'figure.figsize':(10,10)})
    ds = Dataset('aluemaski.nc')
    maski = np.ma.getdata(ds['maski']).flatten()
    ds.close()

    if 'ikir' in sys.argv:
        luokitus_ = Dataset('ikirdata.nc', 'r')
        luokitus = np.zeros([len(luokat_ikir), 19800], bool)
        lon = np.ma.getdata(luokitus_['lon']).flatten()
        lat = np.ma.getdata(luokitus_['lat']).flatten()
        taul = np.ma.getdata(luokitus_['luokka'])
        taul = np.round(np.mean(taul, axis=0)).astype(int)
        for i,v in enumerate(luokat_ikir):
            k = luokat.ikir.index(v)
            luokitus[i] = (taul==k).flatten() * maski
        luokitus_.close()
        luokat_ = luokat_ikir
        värin_alku=1
        sijainti = [0.01, 0.01, 0.98, 0.98]
        ncol=1
        nimi = 'ikir_kartta'
    else:
        luokitus_ = Dataset('köppen1x1maski.nc', 'r')
        luokitus = np.zeros([len(luokat_köpp), 19800], bool)
        for k in luokitus_.variables:
            for li,l in enumerate(luokat_köpp):
                if re.match(l,k):
                    luokitus[li,:] = luokitus[li,:] | (np.ma.getdata(luokitus_[k]).flatten()[:] * maski)
        lon = np.ma.getdata(luokitus_['lon']).flatten()
        lat = np.ma.getdata(luokitus_['lat']).flatten()
        luokitus_.close()
        luokat_ = luokat_köpp
        värin_alku=1
        sijainti = [0.01, 0.01, 0.98, 0.98]
        ncol=2
        nimi = 'köppen_kartta'

    cmap = matplotlib.cm.get_cmap(cmapnimi, len(luokat_)+värin_alku)
    fig = figure()
    ax = axes(sijainti, projection=projektio)
    ax.coastlines()
    ax.set_extent(kattavuus, platecarree)
    if '-f' in sys.argv:
        piirrä_nopeasti(luokitus,cmap,luokat_)
    else:
        piirrä_tarkasti(luokitus,cmap,ax,luokat_,värin_alku)
    #leg=legend(loc='center left', bbox_to_anchor=(1,0.5))
    legend(loc='lower left', fancybox=False, framealpha=1, ncol=ncol)
    if '-s' in sys.argv:
        savefig('kuvia/%s.png' %(nimi))
        clf()
    else:
        show()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

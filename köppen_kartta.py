#!/usr/bin/python3
import cartopy.crs as ccrs
import xarray as xr
from matplotlib.pyplot import *
import matplotlib.patches as patches
import matplotlib
from argparse import ArgumentParser
from köppen_laatikko import luokan_tarkkuudeksi, valitse_luokat, pudota_keskiluokka

def argumentit():
    pars = ArgumentParser()
    pars.add_argument( 'tiedostot', nargs='?', default='köppen1x1.nc' )
    pars.add_argument( '-s', '--tallenna', nargs='?', type=int, const=1, default=0 )
    pars.add_argument( '-t', '--tarkkuus', type=int, default=2 )
    pars.add_argument( '-l', '--luokat', default='DE' )
    pars.add_argument( '-c', '--cmap', default='gist_rainbow_r' )
    pars.add_argument( '-f', '--fast', nargs='?', type=int, const=1, default=0 )
    pars.add_argument( '-k', '--keski_pois', nargs='?', type=int, const=0, default=1 ) # toimii käänteisesti
    return pars.parse_args()

def piirra_nopeasti(luokitus,luokat,cmap):
    lon,lat = np.meshgrid( luokitus.lon.data, luokitus.lat.data )
    for i,luokka in enumerate(luokat):
        maski = luokitus.sluokka.data==luokka
        plot( lon[maski], lat[maski], '.', color=cmap(i), label=luokka, transform=platecarree, alpha=0.8, markersize=3 )

def piirra_tarkasti(luokitus,luokat,cmap,ax):
    dx = luokitus.lon.data[1]-luokitus.lon.data[0]
    dy = luokitus.lat.data[1]-luokitus.lat.data[0]
    lon = luokitus.lon.data
    for i,luokka in enumerate(luokat):
        maski_2D = luokitus.sluokka.data==luokka
        plot(-1,-1,'.',markersize=24,color=cmap(i),label=luokka,transform=platecarree) #Ei piirrä mitään, vaan on legend-funktiota varten.
        #Piirtämistä nopeutetaan yhdistämällä vierekkäiset saman luokan pisteet yhdeksi suorakulmioksi.
        ensimmainen=0
        for lat,maski in zip( luokitus.lat.data, maski_2D ):
            if lat < 0:
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
                ax.add_patch(patches.Rectangle( (lon[alku],lat), dx*(j-alku),dy, color=cmap(i), transform=platecarree ))

if __name__ == '__main__':
    args = argumentit()
    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    kattavuus   = [-180,180,40,90]
    rcParams.update({'font.size':18,'figure.figsize':(12,10)})
    
    luokitus = xr.open_dataset(args.tiedostot)
    npdata = luokitus.sluokka.data.flatten()
    if args.keski_pois:
        pudota_keskiluokka(npdata)
    else:
        luokan_tarkkuudeksi(npdata,args.tarkkuus)
    if len(args.luokat):
        valitse_luokat( npdata, args.luokat )
    luokitus.sluokka.data = npdata.reshape(luokitus.sluokka.shape)

    fig = figure()
    ax = axes( [0,0.03,0.95,0.94], projection=projektio )
    ax.coastlines()
    ax.set_extent(kattavuus, platecarree)
    luokat = np.unique(luokitus.sluokka.data)
    luokat = luokat[luokat!='']
    cmap = matplotlib.cm.get_cmap( args.cmap, len(luokat) )
    if args.fast:
        piirra_nopeasti(luokitus,luokat,cmap)
    else:
        piirra_tarkasti(luokitus,luokat,cmap,ax)
    leg=legend( loc='center left', bbox_to_anchor=(1,0.5) )
    if args.tallenna:
        savefig( 'kuvia/%s.png' %(sys.argv[0][:-3]) )
        clf()
    else:
        show()

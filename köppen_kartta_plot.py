#!/usr/bin/python3
import cartopy.crs as ccrs
import xarray as xr
from matplotlib.pyplot import *
import matplotlib.patches as patches
import matplotlib
from argparse import ArgumentParser
from köppen_laatikko_plot import luokan_tarkkuudeksi, valitse_luokat, pudota_keskiluokka

def argumentit():
    pars = ArgumentParser()
    pars.add_argument( 'tiedostot', nargs='*', default=['köppen1x1.nc'] )
    pars.add_argument( '-s', '--tallenna', nargs='?', type=int, const=1, default=0 )
    pars.add_argument( '-t', '--tarkkuus', type=int, default=1 )
    pars.add_argument( '-l', '--luokat', default='' )
    pars.add_argument( '-c', '--cmap', default='gist_rainbow_r' )
    pars.add_argument( '-f', '--fast', nargs='?', type=int, const=1, default=0 )
    pars.add_argument( '-k', '--keski_pois', nargs='?', type=int, const=1, default=0 )
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
        plot(-1,-1,'.',color=cmap(i),label=luokka,transform=platecarree) #Ei piirrä mitään, vaan on legend-funktiota varten.
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

def aja(args):
    luokitus = xr.open_dataset(args.tiedostot[0])
    npdata = luokitus.sluokka.data.flatten()
    if args.keski_pois:
        pudota_keskiluokka(npdata)
    else:
        luokan_tarkkuudeksi(npdata,args.tarkkuus)
    if len(args.luokat):
        valitse_luokat( npdata, args.luokat )
    luokitus.sluokka.data = npdata.reshape(luokitus.sluokka.shape)

    fig = figure(figsize=(10,8))
    ax = axes( projection=projektio )
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
    for l in leg.get_lines():
        l.set_markersize(15)
        l.set_marker('.')

    if(args.tallenna):
        savefig( '%s_kartta%s%i.png' %(args.tiedostot[0],args.luokat,(-13 if args.keski_pois else args.tarkkuus)) )
        clf()
    if len(args.tiedostot) > 1:
        args.tiedostot = args.tiedostot[1:]
        aja()
    if not args.tallenna:
        show()

if __name__ == '__main__':
    args = argumentit()
    platecarree = ccrs.PlateCarree()
    projektio   = ccrs.LambertAzimuthalEqualArea(central_latitude=90)
    kattavuus   = [-180,180,40,90]
    aja(args)

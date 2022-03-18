#!/usr/bin/python3
import xarray as xr
import numpy as np
from numpy import sin
from config import LPX2019vuo
from matplotlib.pyplot import *
import prf_extent as prf
import sys

def argumentit(argv):
    global tarkk,verbose,tallenna,latraja
    tarkk = 5; verbose = False; tallenna = False; latraja = 50
    i=1
    while i<len(argv):
        a = argv[i]
        if a == '-v':
            verbose = True
        elif a == '-s':
            tallenna = True
        elif a == '-t':
            i += 1
            tarkk = int(argv[i])
        elif a == '-l0':
            i += 1
            latraja = int(argv[i])
        else:
            print("Varoitus: tuntematon argumentti \"%s\"" %a)
        i += 1
    return

def kuvaajan_viimeistely():
    xlabel("% permafrost")
    ylabel("flux (?/m$^2$)")
    title('CH4 flux, lat ≥ %d°N' %latraja)

_viimelat1x1 = np.nan
def pintaala1x1(lat):
    global _viimelat1x1, _viimeala1x1
    if lat == _viimelat1x1:
        return _viimeala1x1
    _viimelat1x1 = lat
    aste = 0.0174532925199
    R2 = 40592558970441
    _viimeala1x1 = aste*R2*( sin((lat+1)*aste) - sin(lat*aste) )
    return _viimeala1x1

class Vuo():
    def __init__(self,osdet,vuot,alat):
        self.osdet = osdet
        self.vuot = vuot
        self.alat = alat
        return
    def __str__(self):
        return ('%sVuo ja ikirouta:%s\n' %(vari1,vari0) +
                f'%sosuudet:%s\n{self.osdet}\n' %(vari2,vari0) +
                f'%svuot:%s\n{self.vuot}\n' %(vari2,vari0) +
                f'%salat:%s\n{self.alat}\n' %(vari2,vari0))

def laske_vuot():
    alku = int(ikirouta.min())
    loppu = int(ikirouta.max())
    osuudet = np.arange(alku,loppu+tarkk,tarkk)
    #luettava data
    ikirflat = ikirouta.data.flatten()
    latflat = np.meshgrid( ikirouta.lon.data, ikirouta.lat.data )[1].flatten()
    vuoflat = vuodata.data.flatten()
    #kirjoitettava data
    vuot = np.zeros(len(osuudet))
    alat = np.zeros(len(osuudet))
    for i in range(len(ikirflat)):
        ala = pintaala1x1(latflat[i])
        #pyöristettäköön indeksi ylöspäin, jotta 0 % on oma luokkansa ja 100 % sisältyy 100-ε %:in
        ind = int(np.ceil( (ikirflat[i]-alku) / tarkk ))
        alat[ind] += ala
        vuot[ind] += vuoflat[i]*ala
    return Vuo(osuudet,vuot,alat)

if __name__ == '__main__':
    rcParams.update({'font.size':13,'figure.figsize':(10,8)})
    argumentit(sys.argv)
    vari0 = '\033[0m'
    vari1 = '\033[1;32m'
    vari2 = '\033[1;33m'
    ncmuuttuja = 'posterior_bio'
    vuodata = xr.open_dataset(LPX2019vuo)[ncmuuttuja].mean(dim='time').loc[latraja:,:]
    ikiroutaolio = prf.Prf('1x1').rajaa([latraja,90])
    ikirouta = ikiroutaolio.data.mean(dim='time')

    vuoolio = laske_vuot()
    vuodata.close()
    if verbose:
        import locale
        locale.setlocale(locale.LC_ALL, '')
        print(f'%sIkiroutadata:%s\n{ikirouta}\n' %(vari1,vari0))
        print(vuoolio)
        print(locale.format_string( 'Yhteensä ikirouta-aluetta %.2f Mkm²', (np.sum(vuoolio.alat[1:])*1e-12) ))
    fig = figure()
    palkit = bar( vuoolio.osdet, vuoolio.vuot/vuoolio.alat, width=tarkk*0.8 )
    kuvaajan_viimeistely()
    tight_layout()
    if tallenna:
        savefig('kuvia/%s.png' %(sys.argv[0][:-3]))
    else:
        show()
#!/usr/bin/python3
import xarray as xr
import numpy as np
from numpy import sin
from config import edgartno_lpx_m, edgartno_lpx_t, tyotiedostot
import talven_ajankohta as taj
from matplotlib.pyplot import *
import prf as prf
import sys

def argumentit(argv):
    global tarkk,verbose,tallenna
    tarkk = 5; verbose = False; tallenna = False
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
        else:
            print("Varoitus: tuntematon argumentti \"%s\"" %a)
        i += 1
    return

def kuvaajan_viimeistely():
    xlabel("% permafrost")
    ylabel("flux (mol/m$^2$/s)")
    title('CH$_4$ flux')

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
        self.vari0 = '\033[0m'
        self.vari1 = '\033[1;32m'
        self.vari2 = '\033[1;33m'
        return
    def __str__(self):
        return ('%sVuo ja ikirouta:%s\n' %(self.vari1,self.vari0) +
                f'%sosuudet:%s\n{self.osdet}\n' %(self.vari2,self.vari0) +
                f'%svuot:%s\n{self.vuot}\n' %(self.vari2,self.vari0) +
                f'%salat:%s\n{self.alat}\n' %(self.vari2,self.vari0))

def laske_vuot(vuodata):
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
        if vuoflat[i]!=vuoflat[i]:
            continue
        ala = pintaala1x1(latflat[i])
        #pyöristettäköön indeksi ylöspäin, jotta 0 % on oma luokkansa ja 100 % sisältyy 100-ε %:in
        ind = int(np.ceil( (ikirflat[i]-alku) / tarkk ))
        alat[ind] += ala
        vuot[ind] += vuoflat[i]*ala
    return Vuo(osuudet,vuot,alat)

if __name__ == '__main__':
    rcParams.update({'font.size':13,'figure.figsize':(10,8)})
    argumentit(sys.argv)
    datamaski = xr.open_dataset(tyotiedostot + 'FT_implementointi/FT_percents_pixel_ease_flag/DOY/winter_end_doy_2014.nc')
    
    ikiroutaolio = prf.Prf('1x1').rajaa([datamaski.lat.min(),datamaski.lat.max()])
    ikirouta = ikiroutaolio.data.mean(dim='time')

    vuodata = xr.open_dataset(edgartno_lpx_t)[edgartno_lpx_m].mean(dim='record')
    vuoolio = laske_vuot( vuodata.loc[datamaski.lat.min():datamaski.lat.max(),:].\
                          where(datamaski.spring_start==datamaski.spring_start,np.nan) )
    vuodata.close()
    datamaski.close()
    if verbose:
        import locale
        locale.setlocale(locale.LC_ALL, '')
        print(f'%sIkiroutadata:%s\n{ikirouta}\n' %(vuoolio.vari1,vuoolio.vari0))
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

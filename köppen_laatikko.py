#!/usr/bin/python3
import xarray as xr
from matplotlib.pyplot import *
from argparse import ArgumentParser
import talven_ajankohta as taj
import pandas as pd
import warnings

def argumentit():
    pars = ArgumentParser()
    pars.add_argument( 'startend', nargs='*', default=['start','end'] )
    pars.add_argument( '-s', '--tallenna', nargs='?', type=int, const=1, default=0 )
    pars.add_argument( '-t', '--tarkkuus', type=int, default=2 )
    pars.add_argument( '-l', '--luokat', default='DE' )
    pars.add_argument( '-k', '--keski_pois', nargs='?', type=int, const=0, default=1 ) #toimii käänteisesti
    pars.add_argument( '-a', '--alaluokat', default=['D.c','D.d','ET'] ) #turhentaa argumentin luokat ja keski_pois
    return pars.parse_args()

def luokan_tarkkuudeksi( sluokka:np.ndarray, n:int ) -> np.ndarray:
    for i in range(len(sluokka)):
        if len(str(sluokka[i])) > n:
            sluokka[i] = str(sluokka[i])[:n]
    return sluokka

def pudota_keskiluokka( sluokka:np.ndarray ) -> np.ndarray:
    for i in range(len(sluokka)):
        if len(str(sluokka[i])) > 2:
            a = str(sluokka[i])
            sluokka[i] = a[0] + '.' + a[2]
    return sluokka

def valitse_alaluokat(sluokka, luokat):
    for i in range(len(sluokka)):
        if len(str(sluokka[i])) and not str(sluokka[i]) in luokat:
            sluokka[i] = ''
    return sluokka

def valitse_luokat( sluokka:np.ndarray, luokat:str ) -> np.ndarray:
    for i in range(len(sluokka)):
        if len(str(sluokka[i])) and not str(sluokka[i])[0] in luokat:
            sluokka[i] = ''
    return sluokka

def lue_luokitus_xr(ncnimi='köppen1x1.nc') -> xr.DataArray:
    luokitus = xr.open_dataset(ncnimi).sluokka
    if not len(args.alaluokat):
        print("Varoitus: %s sai argumentteja, jotka on poistettu käytöstä" %(__name__))
        return luokitus
    npdata = luokitus.data.flatten()
    pudota_keskiluokka(npdata)
    valitse_alaluokat(npdata,args.alaluokat)
    luokitus.data = npdata.reshape(luokitus.shape)
    return luokitus

def lue_luokitus( ncnimi='köppen1x1.nc' ) -> np.ndarray:
    luokitus = xr.open_dataset(ncnimi).sluokka.data.flatten()
    if len(args.alaluokat):
      pudota_keskiluokka(luokitus)
      valitse_alaluokat(luokitus,args.alaluokat)
    else:
        if args.keski_pois:
            pudota_keskiluokka(luokitus)
        else:
            luokan_tarkkuudeksi( luokitus, args.tarkkuus )
        if len(args.luokat):
            valitse_luokat( luokitus, args.luokat )
    return luokitus

def _dataframe_luokka_doy(paivat, args, taytto, _doy=None) -> pd.DataFrame:
    luokitus = lue_luokitus('köppen1x1.nc')
    luokat = np.unique(luokitus)
    luokat = luokat[luokat!='']
    uusi = pd.DataFrame( columns=luokat, index=range(np.product(paivat.shape)) )
    for luokka in luokat:
        a = paivat.copy()
        a[ luokitus != luokka ] = taytto
        uusi[luokka] = a.flatten()
    return uusi if _doy is None else (uusi,_doy)

def dataframe_luokka_doy( startend='start', palauta_doy=False ) -> pd.DataFrame:
    doy = taj.lue_doyt(startend).transpose( ... , 'time' )
    paivat = doy.data
    pit = (np.product(paivat.shape[:2]))
    paivat = np.reshape( paivat, [pit,paivat.shape[2]] ) #taulukon jäsen on yhden pisteen aikasarja
    taytto = [np.nan]*paivat.shape[-1]
    return _dataframe_luokka_doy( paivat,args,taytto, doy if palauta_doy else None )

def dataframe_luokka_avgdoy( startend='start', palauta_doy=False ) -> pd.DataFrame:
    doy = taj.lue_avgdoy(startend)
    return _dataframe_luokka_doy( doy.data.flatten(),args,np.nan, doy if palauta_doy else None )

if __name__ == '__main__':
    rcParams.update({ 'font.size': 18,
                      'figure.figsize': (12,10) })
    args = argumentit()
    for s_e in args.startend:
        df = dataframe_luokka_doy(s_e,False)
        fig = figure()
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)
            df.boxplot( whis=(5,95) )
        ylabel('winter %s doy' %s_e)
        gca().tick_params( axis='y', which='both', left=True )
        tight_layout()
        if args.tallenna:
            savefig( 'kuvia/köppen_laatikko_%s%s%i.png' %(s_e,args.luokat,(-13 if args.keski_pois else args.tarkkuus)) )
            clf()
    if not args.tallenna:
        show()
else:
    apu = sys.argv
    sys.argv = [sys.argv[0]]
    args = argumentit()
    sys.argv = apu

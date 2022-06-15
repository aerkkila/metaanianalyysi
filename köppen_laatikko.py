#!/usr/bin/python3
import xarray as xr
from matplotlib.pyplot import *
import pandas as pd
import warnings, sys
from valitse_painottaen import valitse_painottaen
from multiprocessing import Process

kluokat = ['D.c','D.d','ET']
s_e_muuttuja = {'start':'talven_alku', 'end':'talven_loppu'}

def pudota_keskiluokka(sluokka:np.ndarray) -> np.ndarray:
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

def valitse_luokat(sluokka:np.ndarray, luokat:str) -> np.ndarray:
    for i in range(len(sluokka)):
        if len(sluokka[i]) and not sluokka[i] in luokat:
            sluokka[i] = ''
    return sluokka

def lue_luokitus(ncnimi='köppen1x1.nc') -> np.ndarray:
    luokitus = xr.open_dataset(ncnimi).sluokka.data.flatten()
    pudota_keskiluokka(luokitus)
    valitse_luokat(luokitus, kluokat)
    return luokitus

# Tämä yhdistää ajankohdan luokitteluun.
def _dataframe_luokka_doy(paivat, indeksit=None) -> pd.DataFrame:
    luokitus = lue_luokitus('köppen1x1.nc')
    if not indeksit is None:
        luokitus = luokitus[indeksit]
    luokat = np.unique(luokitus)
    luokat = luokat[luokat!='']
    uusi = pd.DataFrame(columns=luokat, index=range(np.product(paivat.shape)))
    taytto = [np.nan]*paivat.shape[-1]
    for luokka in luokat:
        a = paivat.copy()
        a[luokitus != luokka] = taytto
        uusi[luokka] = a.flatten()
    return uusi

# Tämä lukee ajankohdan ja palauttaa toisen funktion kautta sen yhdistettynä luokitteluun.
def dataframe_luokka_doy(startend, ftnum) -> pd.DataFrame:
    kerroin = 8
    paivat_xr = xr.open_dataset('kausien_pituudet%i.nc' %ftnum)[s_e_muuttuja[startend]].transpose(... , 'vuosi')
    indeksit = valitse_painottaen(paivat_xr.lat.data, paivat_xr.lon.data, kerroin)
    pit = (np.product(paivat_xr.shape[:2]))
    paivat = np.reshape( paivat_xr.data, [pit,paivat_xr.shape[2]] ) #taulukon jäsen on yhden pisteen aikasarja
    paivat_pain = np.empty([pit*kerroin,paivat.shape[1]], np.float32)
    for i in range(paivat.shape[1]):
        paivat_pain[:,i] = paivat[:,i][indeksit]
    paivat_pain = _dataframe_luokka_doy(paivat_pain, indeksit)
    return paivat_pain

#prf_köppen_laatikko käyttää tätä
def dataframe_luokka_avgdoy(startend='start', palauta_doy=False) -> pd.DataFrame:
    paivat = taj.lue_avgdoy(startend)
    return _dataframe_luokka_doy(paivat.data.flatten(),np.nan, paivat if palauta_doy else None)

def aja(ftnum):
    for s_e in ['start','end']:
        df = dataframe_luokka_doy(s_e,ftnum)
        fig = figure()
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)
            df.boxplot(whis=(5,95), widths=0.75)
        ylabel('winter %s, data %i' %(s_e,ftnum))
        gca().tick_params(axis='y', which='both', left=True)
        if s_e[0] == 's':
            ylim([-140,100])
        else:
            ylim([-10,220])
        tight_layout()
        if '-s' in sys.argv:
            nimi = 'kuvia/yksittäiset/köppen_laat_%s_ft%i.png' %(s_e, ftnum)
            print(nimi)
            savefig(nimi)
            clf()
        else:
            show()

def main():
    rcParams.update({ 'font.size': 18,
                      'figure.figsize': (5,10) })
    luvut = [0,1,2]
    pros = np.empty(len(luvut), object)
    for i,l in enumerate(luvut):
        pros[i] = Process(target=aja, args=[l])
        pros[i].start()
    for p in pros:
        p.join()

if __name__ == '__main__':
    main()

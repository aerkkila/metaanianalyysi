#!/bin/env python
import sys, struct
from matplotlib.pyplot import *
import numpy as np

kansio = '../kuvia'

def lue_köntti(pit):
    raaka = sys.stdin.buffer.read(pit*8)
    if len(raaka) == 0:
        return 0
    assert(len(raaka) == pit*8)
    return np.ndarray(pit, dtype=np.float64, buffer=raaka)

# sys.stdin.readline() ei toimi, koska myöhemmin tulee binääridataa, mistä Python ei ole iloinen. Onpa huono kieli.
def lue_rivi():
    lista = bytearray(b'')
    while True:
        a = sys.stdin.buffer.read(1)
        if len(a) == 0 or struct.unpack("b", a)[0] == 10: # jälkimmäinen ehto tarkoittaa rivinvaihtoa
            break
        lista.append(a[0])
    return lista.decode('UTF-8')

def luo_värit(dt):
    r = np.empty(len(dt), object)
    cmap = get_cmap('copper_r', 255)
    mi = min(dt)
    kerr = 1/max(dt) * 255
    for i in range(len(dt)):
        r[i] = cmap(int((dt[i]-mi)*kerr))
    return r

def nimeä(kausi):
    ax.set_xlabel(nimi.replace('_',' ').replace(' cold','').replace(' warm',''))
    ax.set_ylabel('nmol s$^{-1}$ m$^{-2}$')
    title(kausi.replace('_',' '))

def päivitä_rajat():
    ind = np.searchsorted(vuo, fraja)
    ind0 = len(vuo)-ind
    ax.clear()
    if molemmista:
        maski = ~(wdata0[ind0:ind] < wraja)
        ax.scatter(wd1[ind0:ind][maski], vuo[ind0:ind][maski], marker='.', c=värit[ind0:ind][maski])
    else:
        maski = ~(wdata0[:ind] < wraja)
        ax.scatter(wd1[:ind][maski], vuo[:ind][maski], marker='.', c=värit[:ind][maski])
    draw()

def päivitä_wraja(arvo):
    global wraja
    wraja = arvo
    päivitä_rajat()

def päivitä_fraja(arvo):
    global fraja
    fraja = arvo
    päivitä_rajat()

def näppäin(tapaht):
    global molemmista
    if tapaht.key!=' ':
        return
    molemmista = not molemmista
    päivitä_rajat()

def lue_sovitus():
    xs = lue_köntti(2)
    ys = lue_köntti(2)
    pit = struct.unpack("i", sys.stdin.buffer.read(4))[0]
    xb = lue_köntti(pit)
    yb1 = lue_köntti(pit)
    yb2 = lue_köntti(pit)
    return dict(xs=xs, ys=ys, xb=xb, yb1=yb1, yb2=yb2)

def main():
    global wdata0, wd1, vuo, värit, ax, nimi, wraja, fraja, molemmista
    molemmista = True
    tallenna = '-s' in sys.argv
    sov = 'sovitteet' in sys.argv
    rcParams.update({'figure.figsize':(8,7), 'font.size':15})
    raaka = sys.stdin.buffer.read(4)
    pit = struct.unpack("i", raaka)[0]

    wdata0    = lue_köntti(pit)
    vuo       = lue_köntti(pit)
    järjestys = np.argsort(vuo)
    wdata0    = wdata0[järjestys]
    värit     = luo_värit(wdata0)
    vuo       = vuo[järjestys]

    if sov:
        pass#vakio = lue_köntti(1)[0]

    wdata1 = []
    nimet  = []
    kaudet = []
    viivat = []
    while True:
        nimet.append(lue_rivi())
        if not nimet[-1]:
            nimet = nimet[:-1]
            break
        kaudet.append(lue_rivi())
        wdata1.append(lue_köntti(pit)[järjestys])
        if sov:
            viivat.append(lue_sovitus())
        else:
            viivat.append(lue_köntti(2))

    for i,nimi in enumerate(nimet):
        wd1 = wdata1[i]
        fig = figure()

        if sov:
            ax = axes()
            wraja = np.nan
            fraja = np.nan
            päivitä_rajat()
            nimeä(kaudet[i])
            ax.plot(viivat[i]['xs'], viivat[i]['ys'], 'k') # suora
            ax.plot(viivat[i]['xb'], viivat[i]['yb1'], 'k', linestyle='--') # matala
            ax.plot(viivat[i]['xb'], viivat[i]['yb2'], 'k', linestyle='--') # korkea
            tight_layout()
            if tallenna:
                savefig(kansio+'/wregressio_suora_%s_%s.png' %(kaudet[i],nimi))
            else:
                show()
            continue

        if tallenna:
            ax = axes()
            wraja = np.nan
            fraja = np.nan
            päivitä_rajat()
            nimeä(kaudet[i])
            ax.axhline(viivat[i][0], color='k')
            ax.axhline(viivat[i][1], color='k')
            tight_layout()
            savefig(kansio+'/wregressio_%s_%s.png' %(kaudet[i],nimi))
            continue

        ax = axes([0.08, 0.05, 0.9, 0.87])
        liuku = Slider(
            ax      = axes([0.25, 0.96, 0.66, 0.02]),
            label   = "wetland >=",
            valmin  = 0.05,
            valmax  = 1,
            valfmt  = '%.3f',
            valinit = 0.05
        )
        liuku.on_changed(päivitä_wraja)
        liukuf = Slider(
            ax      = axes([0.25, 0.94, 0.66, 0.02]),
            label   = "flux <=",
            valmin  = 0,
            valmax  = 180,
            valfmt  = '%i',
            valinit = 180
        )
        liukuf.on_changed(päivitä_fraja)
        wraja = 0.05
        fraja = 180

        fig.canvas.mpl_connect('key_press_event', näppäin)
        päivitä_rajat()
        ax.axhline(viivat[i][0], color='k')
        ax.axhline(viivat[i][1], color='k')
        nimeä(kaudet[i])
        show()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

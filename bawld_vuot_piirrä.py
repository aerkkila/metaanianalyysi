#!/usr/bin/python3
import xarray as xr
import numpy as np
from matplotlib.pyplot import *
import config, locale

def wlvuo(maski):
    return vuo[maski]/wl[maski]

ei_paivit__ = False
def paivita_wetlandraja(arvo):
    global wetlandraja,ei_paivit__
    if ei_paivit__:
        return
    ei_paivit__ = True
    liuku.set_val(arvo)
    ei_paivit__ = False
    wetlandraja = arvo
    maski = (wl<wetlandraja) & (luokmaski)
    viivat.set_xdata(osuus[maski])
    viivat.set_ydata(vuo[maski])
    avg = np.mean(vuo[maski])
    avgviiva.set_ydata([avg]*2)
    teksti.set_text(locale.format_string('σ = %.2e', avg))
    teksti.set_y(avg)
    draw()

def paivita_osuusraja_wl(arvo):
    global osuusraja_wl
    osuusraja_wl = arvo
    maski = (wl>=osuusraja_wl)
    v = wlvuo(maski)
    viivat_wl.set_xdata(wl[maski])
    viivat_wl.set_ydata(v)
    avg = np.mean(v)
    avgviiva_wl.set_ydata([avg]*2)
    teksti_wl.set_text(locale.format_string('σ = %.2e', avg))
    teksti_wl.set_y(avg)
    draw()

def painettaessa(tapaht):
    if tapaht.key == 'down' or tapaht.key == 'a':
        paivita_wetlandraja(wetlandraja-0.01)
    elif tapaht.key == 'up' or tapaht.key == 'i':
        paivita_wetlandraja(wetlandraja+0.01)
    elif tapaht.key == 'left' or tapaht.key == 'g':
        paivita_wetlandraja(wetlandraja-0.001)
    elif tapaht.key == 'right' or tapaht.key == 'o':
        paivita_wetlandraja(wetlandraja+0.001)
    else:
        return

def main():
    global viivat,avgviiva,viivat_wl,avgviiva_wl,wl,vuo,luokmaski,osuus,wetlandraja,osuusraja_wl,liuku
    global teksti, teksti_wl
    locale.setlocale(locale.LC_ALL,'')
    luokka='boreal_forest'
    wlluokka='wetland'
    osuusraja = 0.05
    wetlandraja = 0.010
    osuusraja_wl = osuusraja
    vuot = xr.open_dataarray(config.edgartno_dir+'posterior.nc').mean(dim='time')
    baw = xr.open_dataset('BAWLD1x1.nc')

    vuo = vuot.sel({'lat':slice(baw.lat.min(), baw.lat.max())}).data.flatten()
    osuus = baw[luokka].data.flatten()
    luokmaski = (osuus>=osuusraja)
    if not any(luokmaski):
        return
    wl = baw[wlluokka].data.flatten()

    vuot.close()
    baw.close()
    ax = axes([0.08,0.07,0.8,0.77])

    maski = (wl<wetlandraja) & (luokmaski)
    viivat, = plot(osuus[maski], vuo[maski], '.', label=luokka, color='b')
    avg = np.mean(vuo[maski])
    avgviiva, = plot([osuusraja,1], [avg]*2, color='deepskyblue')
    teksti = text(1.02,avg,locale.format_string('σ = %.2e', avg))

    maski = (wl>=osuusraja_wl)
    v = wlvuo(maski)
    viivat_wl, = plot(wl[maski], v, 'x', label=wlluokka, color='r')
    avg = np.mean(v)
    avgviiva_wl, = plot([osuusraja,1], [avg]*2, color='lightsalmon')
    teksti_wl = text(1.02,avg,locale.format_string('σ = %.2e', avg))

    grid('on')
    ymax = v.max()*0.66666
    ymin = min(v.min(), vuo.min())
    ylim([ymin,ymax])
    ylabel('CH$_4$ (mol/m$^2$/s)')
    xlabel('osuus')
    legend(frameon=True)
    
    liuku = Slider(
        ax      = axes([0.15, 0.93, 0.72, 0.04]),
        label   = "%s <" %wlluokka,
        valmin  = 0,
        valmax  = 1-osuusraja,
        valfmt  = '%.3f',
        valinit = wetlandraja
    )
    liuku.on_changed(paivita_wetlandraja)
    gcf().canvas.mpl_connect('key_press_event', painettaessa)
    wlliuku = Slider(
        ax      = axes([0.15, 0.87, 0.72, 0.04]),
        label   = "%s >=" %wlluokka,
        valmin  = 0,
        valmax  = 1,
        valfmt  = '%.3f',
        valinit = osuusraja_wl
    )
    wlliuku.on_changed(paivita_osuusraja_wl)
    show()

if __name__ == '__main__':
    rcParams.update({'figure.figsize':(12,10), 'font.size':14})
    main()

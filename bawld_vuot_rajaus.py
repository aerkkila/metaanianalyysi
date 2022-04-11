#!/usr/bin/python3
import xarray as xr
import numpy as np
from matplotlib.pyplot import *
import config, locale

def luokan_vuo(maski,ind2):
    return vuo[maski]#/osuus[ind2][maski]

def paivita_raja(ind2):
    maski = luokmaski[ind2*2] & luokmaski[ind2*2+1]
    v = luokan_vuo(maski,ind2)
    viivat[ind2].set_xdata(osuus[ind2][maski])
    viivat[ind2].set_ydata(v)
    avg = np.mean(v)
    avgviiva[ind2].set_ydata([avg]*2)
    teksti[ind2].set_text(locale.format_string('σ = %.2e', avg))
    teksti[ind2].set_y(avg)
    draw()
    return

def paivita_raja_kuiva_kuiva(arvo):
    rajat[0] = arvo
    luokmaski[0] = (osuus[0]>=rajat[0])
    paivita_raja(0)
    return

def paivita_raja_wl_kuiva(arvo):
    rajat[1] = arvo
    luokmaski[1] = (osuus[1]<rajat[1])
    paivita_raja(0)
    return

def paivita_raja_wl_wl(arvo):
    rajat[2] = arvo
    luokmaski[2] = (osuus[1]>=rajat[2])
    paivita_raja(1)
    return

def paivita_raja_yht_wl(arvo):
    rajat[3] = arvo
    luokmaski[3] = (osuus[0]+osuus[1]>=rajat[3])
    paivita_raja(1)
    return

def main():
    global viivat,avgviiva,teksti,vuo,luokmaski,osuus,rajat
    locale.setlocale(locale.LC_ALL,'')
    kuivaluokka='tundra_dry'
    wlluokka='wetland'
    raja_kuiva_kuiva = 0.2 #vähintään kuivaa kuivassa
    raja_wl_kuiva = 0.010 #alle tämän verran märkää kuivassa
    raja_wl_wl = 0.05 #vähintään märkää märässä
    raja_yht_wl = 0.8 #vähintään näin paljon yhteensä kuiva- ja märkäluokkaa
    rajat = [raja_kuiva_kuiva, raja_wl_kuiva, raja_wl_wl, raja_yht_wl]
    
    vuot = xr.open_dataarray(config.edgartno_dir+'posterior.nc').mean(dim='time')
    baw = xr.open_dataset('BAWLD1x1.nc')

    vuo = vuot.sel({'lat':slice(baw.lat.min(), baw.lat.max())}).data.flatten()
    kuiva = baw[kuivaluokka].data.flatten()
    wl = baw[wlluokka].data.flatten()
    osuus = [kuiva,wl]
    luokmaski = [(kuiva>=raja_kuiva_kuiva), (wl<raja_wl_kuiva),
                 (wl>=raja_wl_wl), (kuiva+wl>=raja_yht_wl)]
    if not any(luokmaski[0]):
        return

    vuot.close()
    baw.close()
    ax = axes([0.08,0.07,0.8,0.72])

    #kuiva luokka
    maski = (luokmaski[0]) & (luokmaski[1])
    viivat_k, = plot(kuiva[maski], vuo[maski], '.', label=kuivaluokka, color='b')
    avg = np.mean(vuo[maski])
    avgviiva_k, = plot([0.02, 0.98], [avg]*2, color='deepskyblue')
    teksti_k = text(1.02,avg,locale.format_string('σ = %.2e', avg))

    #märkä luokka
    maski = (luokmaski[2]) & (luokmaski[3])
    v = luokan_vuo(maski,1)
    viivat_w, = plot(wl[maski], v, 'x', label=wlluokka, color='r')
    avg = np.mean(v)
    avgviiva_w, = plot([0.02, 0.98], [avg]*2, color='lightsalmon')
    teksti_w = text(1.02,avg,locale.format_string('σ = %.2e', avg))

    viivat = [viivat_k, viivat_w]
    avgviiva = [avgviiva_k, avgviiva_w]
    teksti = [teksti_k, teksti_w]

    grid('on')
    ymax = v.max()*0.66666
    ymin = min(v.min(), vuo.min())
    ylim([ymin,ymax])
    ylabel('CH$_4$ (mol/m$^2$/s)')
    xlabel('osuus')
    legend(loc='center right', frameon=True)
    
    liuku_kk = Slider(
        ax      = axes([0.25, 0.96, 0.66, 0.02]),
        label   = "kuivaa kuivassa >=",
        valmin  = 0,
        valmax  = 1,
        valfmt  = '%.3f',
        valinit = rajat[0]
    )
    liuku_kk.on_changed(paivita_raja_kuiva_kuiva)
    liuku_wk = Slider(
        ax      = axes([0.25, 0.88, 0.66, 0.02]),
        label   = "märkää kuivassa <",
        valmin  = 0,
        valmax  = 1,
        valfmt  = '%.3f',
        valinit = rajat[1]
    )
    liuku_wk.on_changed(paivita_raja_wl_kuiva)
    liuku_ww = Slider(
        ax      = axes([0.25, 0.92, 0.66, 0.02]),
        label   = "märkää märässä >=",
        valmin  = 0,
        valmax  = 1,
        valfmt  = '%.3f',
        valinit = rajat[2]
    )
    liuku_ww.on_changed(paivita_raja_wl_wl)
    liuku_yw = Slider(
        ax      = axes([0.25, 0.84, 0.66, 0.02]),
        label   = "yhteensä märässä >=",
        valmin  = 0,
        valmax  = 1,
        valfmt  = '%.3f',
        valinit = rajat[3]
    )
    liuku_yw.on_changed(paivita_raja_yht_wl)
    show()

if __name__ == '__main__':
    rcParams.update({'figure.figsize':(12,10), 'font.size':14})
    main()

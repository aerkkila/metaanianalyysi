#!/usr/bin/python
import numpy as np
from netCDF4 import Dataset
from matplotlib.pyplot import *
import luokat, warnings
from multiprocessing import Process

def argumentit():
    global tallenna, tarkk, verbose
    tallenna=False; tarkk=2; verbose=False
    i = 1
    while i < len(sys.argv):
        a = sys.argv[i]
        if a == '-s':
            tallenna = True
        elif a == '-v':
            verbose = True
        elif a == 'start' or a == 'end':
            startend = a
        elif a == '-t' or a == '--tarkkuus':
            i += 1
            tarkk = int(sys.argv[i])
        else:
            print("Varoitus: tuntematon argumentti \"%s\"" %a)
        i += 1
    return

def alanolla(ind):
    apu = yarrlis[ind]
    m = np.argmax(apu)
    for n in range(m,0,-1):
        if(apu[n] == 0):
            return n
    return 0

def ylänolla(ind):
    apu = yarrlis[ind]
    pit = len(apu)
    m = np.argmax(apu)
    for n in range(m,pit):
        if(apu[n] == 0):
            return n
    return pit-1
    
def laita_xrajat():
    a1 = xarrlis[0][alanolla(0)]
    a2 = xarrlis[-1][alanolla(-1)]
    a = min(a1, a2) - 5
    a1 = xarrlis[0][ylänolla(0)]
    a2 = xarrlis[-1][ylänolla(-1)]
    b = max(a1, a2) + 5
    xlim([a,b])

def vaihda_ikirluokka(hyppy:int):
    global ikir_ind
    ikir_ind = (ikir_ind + len(luokat.ikir) + hyppy) % len(luokat.ikir)
    if xarrlis[ikir_ind] is None:
        maski = ikirdat==ikir_ind
        xarrlis[ikir_ind],yarrlis[ikir_ind] = pintaalat1x1(päivät, päivät[maski], tarkk, alat[maski])
        return True
    return False

def vaihda_ikirluokka_piirtäen(hyppy:int):
    vaihda_ikirluokka(hyppy)
    for i,suorak in enumerate(palkit):
        suorak.set_height(yarrlis[ikir_ind][i]/1000/tarkk)
    title(luokat.ikir[ikir_ind])
    gca().relim()
    gca().autoscale_view()
    laita_xrajat()
    draw()
    return

def nappainfunk(tapaht):
    if tapaht.key == 'right' or tapaht.key == 'o' or tapaht.key == 'i':
        vaihda_ikirluokka_piirtäen(1)
    elif tapaht.key == 'left' or tapaht.key == 'g' or tapaht.key == 'a':
        vaihda_ikirluokka_piirtäen(-1)
    return

# Diskretisoi darr-DataArrayn tarkk-tarkkuudella ja
# laskee paljonko pinta-alaa on kullakin syntyneellä osuudella.
def pintaalat1x1(kokodata,darr,tarkk,alat):
    minluku = int(np.nanmin(kokodata))
    maxluku = int(np.nanmax(kokodata))
    lukualat = np.zeros( (maxluku - minluku) // tarkk + 1 )
    for i,luku in enumerate(darr):
        if luku != luku:
            continue
        lukualat[(int(luku)-minluku)//tarkk] += alat[i]
    return np.arange(minluku,maxluku+1,tarkk), lukualat

al_muuttuja = ['jaatym_alku','talven_alku','talven_loppu']
al_nimi = ['freezing_start', 'winter_start', 'summer_start']

def aja(kaudet, ftnum, ikirdat, alat):
    global ikir_ind, xarrlis, yarrlis, päivät, palkit, aln
    ikir_ind=0
    for alm, aln in zip(al_muuttuja, al_nimi):
        päivät = np.ma.getdata(kaudet[alm], False)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            päivät = np.nanmean(päivät, axis=0).flatten()
        xarrlis = [None]*len(luokat.ikir)
        yarrlis = xarrlis.copy()
        maski = ikirdat==ikir_ind
        xarrlis[ikir_ind],yarrlis[ikir_ind] = pintaalat1x1(päivät, päivät[maski], tarkk, alat[maski])

        if verbose:
            import locale
            locale.setlocale(locale.LC_ALL,'')
            tulosta = lambda : print(locale.format_string('%s: %.2f Mkm²', (luokat.ikir[ikir_ind].replace('_',' '),
                                                                            np.sum(yarrlis[ikir_ind])*1e-6)))
            tulosta()
            while vaihda_ikirluokka(1):
                tulosta()
        else:
            while vaihda_ikirluokka(1):
                pass

        fig = figure()
        palkit = bar(xarrlis[ikir_ind], yarrlis[ikir_ind]/1000, width=0.8*tarkk)
        xlabel('%s%s' %(aln.replace('_',' '), '' if ftnum<0 else ', data%i' %ftnum))
        ylabel('extent (1000 km$^2$)')
        title(luokat.ikir[ikir_ind])
        tight_layout()
        vaihda_ikirluokka_piirtäen(0)
        if not tallenna:
            fig.canvas.mpl_connect('key_press_event',nappainfunk)
            show()
            continue
        while True:
            savefig("kuvia/yksittäiset/ikir%i_%s%s.png" %(ikir_ind,aln,
                                                          '' if ftnum<0 else '_ft%i' %ftnum))
            if ikir_ind+1 == len(luokat.ikir):
                ikir_ind = 0
                break
            vaihda_ikirluokka_piirtäen(1)

def main():
    global ikirdat, alat
    rcParams.update({'font.size':19,'figure.figsize':(12,10)})
    argumentit()
    ikir_ind = 0
    kerroin = 8
    ftluvut = [-1]
    ft_oletus = 2
    avaa_kaudet = lambda l: Dataset("kausien_pituudet%i.nc" %(ft_oletus if l<0 else l))
    ikirdat = np.ma.getdata(Dataset('ikirdata.nc')['luokka'])
    ikirdat = np.round(np.mean(ikirdat, axis=0)).astype(int).flatten()
    alat = np.load('pintaalat.npy')

    if(len(ftluvut) == 1):
        a = avaa_kaudet(ftluvut[0])
        aja(a, ftluvut[0], ikirdat, alat)
        a.close()
        return

    pros = np.empty(len(ftluvut),object)
    for i,l in enumerate(ftluvut):
        kaudet = avaa_kaudet(l)
        if(i==0):
            ikirdat = xr.open_dataset("prfdata_avg.nc")['luokka'].sel({'lat':slice(kaudet.lat.min(),kaudet.lat.max())})
        pros[i] = Process(target=aja, args=[kaudet, l, ikirdat, alat])
        pros[i].start()
    for p in pros:
        p.join()
    ikirdat.close()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

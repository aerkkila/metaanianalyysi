from numpy import sin
import numpy as np
# laskee paljonko pinta-alaa on kullakin xjaon osuudella (km²).
# xjako on oltava tasavälinen
# Jos dt on dataframe, tämä on hirvittävän hidas. Olkoon dt numpy-array.
def pintaalat1x1(dt,lat,lon,xjako):
    aste = 0.0174532925199
    R2 = 40592558970441
    PINTAALA = lambda _lat: aste*R2*( sin((_lat+1)*aste) - sin(_lat*aste) )*1.0e-6
    
    lukualat = np.zeros(len(xjako))
    tarkk = xjako[1]-xjako[0]
    minluku = xjako[0]
    for j,la in enumerate(lat):
        ala = PINTAALA(la)
        x_rantu = dt[ j*lon.size : (j+1)*lon.size ]
        x_rantu = x_rantu[x_rantu >= minluku]
        for luku in x_rantu.astype(int):
            lukualat[(luku-minluku)//tarkk] += ala
    return lukualat

def luo_xjako(dt,tarkk,luokat2):
    minluku = int(999999999)
    maxluku = int(-999999999)
    for luok in luokat2:
        d = dt[luok]
        try:
            minluku = min(minluku,int(np.nanmin(d)))
            maxluku = max(maxluku,int(np.nanmax(d)))
        except:
            continue # Tällöin taulukon d kaikki jäsenet olivat epälukuja. Kyse ei ole virheestä.
    return np.arange(minluku,maxluku+1,tarkk)

def tee_luokka(xtaul,ytaul,dflista,dfind,luokat2,tarkk):
    xtaul[dfind] = luo_xjako(dflista[dfind], tarkk, luokat2)
    for i,mluok in enumerate(luokat2):
        tmp = dflista[dfind]
        ytaul[dfind,i] = pintaalat1x1( np.array(tmp[mluok]), np.array(tmp.lat), np.array(tmp.lon), xtaul[dfind] )

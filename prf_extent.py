#!/usr/bin/python3
from PIL import Image
import numpy as np
import re, os

def lue(hila='1x1') -> dict:
    tyotstot = '/media/levy/Tyotiedostot/'
    kansio = tyotstot + 'PermafrostExtent/'
    vuodet = []
    nimi0 = 'PRF_Extent'
    nimi1 = '_%s.tif' %hila
    for tiednimi in os.listdir(kansio):
        vuosi = re.search( '(?<=%s)[0-9]+(?=%s)'%(nimi0,nimi1), tiednimi )
        if vuosi:
            vuodet.append(vuosi.group(0))
    vuodet = sorted(np.array(vuodet,int))
    tiednimi = kansio + nimi0 + str(vuodet[0]) + nimi1
    with Image.open(tiednimi) as im:
        muoto = im.size[::-1]
    tifdata = np.empty([len(vuodet),np.product(muoto)])
    for i,vuosi in enumerate(vuodet):
        with Image.open( kansio + nimi0 + str(vuosi) + nimi1 ) as im:
            tifdata[i] = np.array(im.getdata())
    muoto = [ len(vuodet), muoto[0], muoto[1] ]
    return { 'vuodet':vuodet, 'data':tifdata.reshape(muoto) }

def rajaa1x1( data, lat01 ):
    alku = int(np.ceil(90-lat01[1]))
    loppu = int(np.ceil(90-lat01[0]))
    return data[:,alku:loppu,:]

class Prf():
    def __init__(self,hila='1x1'):
        a = lue(hila)
        self.vuodet = a['vuodet']
        self.data   = a['data'  ]
        self.hila = hila
        return
    def __str__(self):
        return ( f'muoto: {self.data.shape}\n'
                 f'hila: {self.hila}\n'
                 f'vuodet: {self.vuodet}\n'
                 f'data: {self.data}' )
    def rajaa(self,lat01):
        if self.hila == '1x1':
            self.data = rajaa1x1(self.data,lat01)
        else:
            print( 'Rajaaminen ei onnistu. Tuntematon muoto: \"%s\".' %(self.hila) )
        return self

luokat = ['distinguishing isolated', 'sporadic', 'discontinuous', 'continuous']

def luokittelu_str(data:np.ndarray) -> np.ndarray:
    uusi = np.empty_like(data,dtype=object)
    uusi[ (0 < data) & (data<10) ] = luokat[0]
    uusi[ (10<=data) & (data<50) ] = luokat[1]
    uusi[ (50<=data) & (data<90) ] = luokat[2]
    uusi[ (90<=data)             ] = luokat[3]
    return uusi

def luokittelu_num(data:np.ndarray) -> np.ndarray:
    uusi = np.empty_like(data,dtype=float)
    uusi[       (0 == data)      ] = np.nan
    uusi[ (0 < data) & (data<10) ] = 0
    uusi[ (10<=data) & (data<50) ] = 1
    uusi[ (50<=data) & (data<90) ] = 2
    uusi[ (90<=data)             ] = 3
    return uusi

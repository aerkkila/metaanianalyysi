import numpy as np

aste = 0.0174532925199
R2 = 40592558970441
PINTAALA1x1 = lambda _lat: aste*R2*( np.sin((_lat+1)*aste) - np.sin(_lat*aste) )*1.0e-6
def pintaalat1x1(lat):
    alat = np.empty_like(lat)
    for i,la in enumerate(lat):
        alat[i] = PINTAALA1x1(la)
    return alat

def pintaalan_painotus(alat):
    painot = alat/alat[0]
    for i in range(1,len(painot)):
        painot[i] += painot[i-1]
    for i in range(len(painot)):
        painot[i] /= painot[-1]
    return painot

def hae_indeksi(ran, rajat):
    pituus = len(rajat)
    alempi = 0
    ylempi = pituus-1
    while True:
        ind = (alempi+ylempi)//2
        if ran < rajat[ind]:
            if ind==0 or rajat[ind-1] <= ran:
                return ind
            ylempi = ind
            continue
        alempi = ind
        if alempi == ylempi-1:
            return ylempi
    return

#Eteläisimmät hilaruudut ovat noin 8 kertaa niin suuria kuin pohjoisimmat.
#Tällä valitaan datasta hilaruutuja painottaen todennäköisyyksiä leveyspiirin mukaan.
#Mieluiten kerroin > 8, jotta eteläisimpiäkin hilaruutuja tulee keskimäärin vähintään 1.
def valitse_painottaen(lat, lon, kerroin, tehdaanko_mitaan=True):
    if not tehdaanko_mitaan:
        if lon is None:
            return np.arange(0,len(lat))
        return np.arange(0,len(lat)*len(lon))
    if not lon is None:
        lon,lat = np.meshgrid(lon,lat)
        lat = lat.flatten()
    n_samp = int(len(lat)*kerroin)
    painot = pintaalan_painotus(pintaalat1x1(lat))
    indeksit = np.empty(n_samp,int)
    luvut = np.random.default_rng(12345).random(n_samp)
    for i in range(n_samp):
        indeksit[i] = hae_indeksi(luvut[i], painot)
    return indeksit

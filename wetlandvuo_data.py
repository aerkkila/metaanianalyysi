import numpy as np
import xarray as xr

nimet = ['bog', 'fen', 'bog+fen', 'marsh', 'tundra_wetland', 'permafrost_bog', 'wetland']
kaudet = ['whole_year', 'summer', 'freezing', 'winter']

def tee_data(kausi='whole_year', priori=False):
    raja_wl = 0.0
    dsbaw = xr.open_dataset('./BAWLD1x1.nc')[nimet]
    dsbaw = xr.where(dsbaw.wetland>=raja_wl, dsbaw, np.nan)
    muuttuja = 'flux_bio_prior' if priori else 'flux_bio_posterior'
    dsvuo = xr.open_dataset('./flux1x1.nc')[muuttuja]
    k = xr.open_dataset('kaudet.nc')
    t0 = max(k.time[0],  dsvuo.time[0])
    t1 = min(k.time[-1], dsvuo.time[-1])
    dsvuo = vuo.sel(time=slice(t0, t1))
    if kausi != 'whole_year':
        kausien_pituudet = xr.open_dataset('kausien_pituudet.nc')[kausi].mean(dim='vuosi').data.flatten()
        num = 1 if kausi=='summer' else 2 if kausi=='freezing' else 3 if kausi=='winter' else 0
        dsvuo = dsvuo.where(kaudet.data==num, np.nan)
    else:
        kausien_pituudet = [365.25]*55*360
    dsvuo = dsvuo.mean(dim='time')
    k.close()
    dsvuo *= 1e9
    lon,lat = np.meshgrid(dsvuo.lon.data, dsvuo.lat.data)
    lon = lon.flatten()
    lat = lat.flatten()

    ds = dsbaw
    dt = np.empty([len(ds.keys()), ds[list(ds.keys())[0]].data.size])
    for i,key in enumerate(ds.keys()):
        dt[i,:] = ds[key].data.flatten()
    dt = dt.transpose()
    dty = dsvuo.data.flatten()
    lasku = 0
    #dropna
    for i in range(dt.shape[0]):
        if all(dt[i,:] == dt[i,:]) and dty[i] == dty[i]:
            lasku += 1
    uusix = np.empty([lasku, dt.shape[1]])
    uusiy = np.empty(lasku)
    uusilat = np.empty(lasku)
    uusilon = np.empty(lasku, np.float32)
    uusikausi = np.empty(lasku, np.float32)
    maski = np.zeros(dt.shape[0], bool)
    ind = 0
    for i in range(dt.shape[0]):
        if all(dt[i,:] == dt[i,:]) and dty[i] == dty[i]:
            uusix[ind,:] = dt[i,:]
            uusiy[ind] = dty[i]
            uusilat[ind] = lat[i]
            uusilon[ind] = lon[i]
            uusikausi[ind] = kausien_pituudet[i]
            maski[i] = True
            ind += 1
    return [uusix, uusiy, list(ds.keys()), uusilat, uusikausi, maski, uusilon]

def tee_data2(*args, **kwargs):
    dt = tee_data(*args, **kwargs)
    return {'x':dt[0], 'y':dt[1], 'wlnimet':dt[2], 'lat':dt[3], 'lon':dt[6], 'kausi':dt[4], 'maski':dt[5]}

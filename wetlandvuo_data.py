import numpy as np
import xarray as xr
from copy import copy

def tee_data(muoto='numpy', tmp=False, pakota=False):
    tallennusnimi = 'wetlandvuo_data.npz'
    if muoto=='numpy' and not tmp and not pakota:
        try:
            dt1 = np.load(tallennusnimi)
            dt = deepcopy(dt1)
            dt1.close()
            return [dt['x'], dt['y'], dt['nimet'], dt['lat']]
        except:
            pass
    raja_wl = 0.03
    dsbaw = xr.open_dataset('./BAWLD1x1.nc')\
        [['wetland','bog','fen','marsh','tundra_wetland','permafrost_bog']]
    dsbaw = xr.where(dsbaw.wetland>=raja_wl, dsbaw, np.nan)
    dsvuo = xr.open_dataarray('./flux1x1_whole_year.nc').mean(dim='time')
    dsvuo *= 1e9
    pit = dsvuo.lon.data.size
    lat = dsvuo.lat.data
    lat = np.repeat(lat,pit).reshape([len(lat),pit]).flatten() #meshgrid lat-koordinaatista

    if muoto=='numpy':
        ds = dsbaw.drop_vars('wetland')
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
        ind = 0
        for i in range(dt.shape[0]):
            if all(dt[i,:] == dt[i,:]) and dty[i] == dty[i]:
                uusix[ind,:] = dt[i,:]
                uusiy[ind] = dty[i]
                uusilat[ind] = lat[i]
                ind += 1
        if not tmp:
            np.savez(tallennusnimi, x=uusix, y=uusiy, nimet=list(ds.keys()), uusilat=lat)
        return [uusix, uusiy, list(ds.keys()), uusilat]

    #pandas tästä eteenpäin
    ds = dsbaw.drop_vars('wetland').assign({dsvuo.name:dsvuo})
    df = ds.to_dataframe()
    df.dropna(how='any', inplace=True)
    return df.reset_index(drop=True)

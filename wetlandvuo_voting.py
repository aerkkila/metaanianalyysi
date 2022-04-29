#!/usr/bin/python3
from sklearn import linear_model
import numpy as np
import xarray as xr
from voting_model import Voting

def tee_data(muoto='pandas'):
    raja_wl = 0.25
    dsbaw = xr.open_dataset('./BAWLD1x1.nc')\
        [['wetland','bog','fen','marsh','tundra_wetland','permafrost_bog']]
    dsbaw = xr.where(dsbaw.wetland>=raja_wl, dsbaw, np.nan)
    dsvuo = xr.open_dataarray('./flux1x1_whole_year.nc').mean(dim='time').\
        sel({'lat':slice(dsbaw.lat.min(), dsbaw.lat.max())})
    dsvuo *= 1e9
    ds = dsbaw.drop_vars('wetland').assign({dsvuo.name:dsvuo})

    if muoto=='numpy':
        dt = np.empty([len(ds.keys()), ds[list(ds.keys())[0]].data.size])
        for i,key in enumerate(ds.keys()):
            dt[i,:] = ds[key].data.flatten()
        dt = dt.transpose()
        lasku = 0
        #dropna
        for i in range(dt.shape[0]):
            if all(dt[i,:] == dt[i,:]):
                lasku += 1
        uusi = np.empty([lasku, dt.shape[1]])
        ind = 0
        for i in range(dt.shape[0]):
            if all(dt[i,:] == dt[i,:]):
                uusi[ind,:] = dt[i,:]
                ind += 1
        return uusi

    #pandas tästä eteenpäin
    df = ds.to_dataframe()
    df.dropna(how='any', inplace=True)
    return df.reset_index(drop=True)

def main():
    np.random.seed(12345)
    tyyppi = 'numpy'
    dt = tee_data(tyyppi)
    if tyyppi == 'pandas':
        datax = dt.drop('vuo', axis=1)
        datay = dt.vuo
    elif tyyppi == 'numpy':
        datax = dt[:,:-1]
        datay = dt[:,-1]
    vm = Voting(linear_model.LinearRegression(), tyyppi, samp_kwargs={'n':50})
    vm.fit(datax, datay)
    print(vm.predict(datax, palauta=True)[:10])
    print(vm.prediction(50)[:10])
    print(vm.prediction(90)[:10])
    return 0

if __name__=='__main__':
    main()

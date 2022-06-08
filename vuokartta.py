#!/usr/bin/python3
import xarray as xr
from matplotlib.pyplot import *

ds = xr.open_dataset('flux1x1_whole_year.nc').flux_bio_posterior.mean(dim='time')
ds.plot.pcolormesh()
show()

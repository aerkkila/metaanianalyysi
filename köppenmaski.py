#!/usr/bin/python3
import numpy as np
import xarray as xr
import re

luokat = ['D.c', 'D.d', 'ET']

if __name__ == '__main__':
    koppmaski = xr.open_dataset("köppen1x1maski.nc").astype(bool)
    taul = np.zeros([len(luokat),koppmaski.ET.size], bool)
    for nimi in koppmaski.keys():
        for ind_luok,luok in enumerate(luokat):
            if not re.match(luok,nimi):
                continue
            taul[ind_luok,:] |= koppmaski[nimi].data.flatten()
    np.save("köppenmaski.npy",taul)

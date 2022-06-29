#!/usr/bin/python3
import numpy as np
import xarray as xr
import re

luokat = ['D.c', 'D.d', 'ET']

if __name__ == '__main__':
    koppmaski = xr.open_dataset("köppen1x1maski.nc").astype(bool)
    taul = np.zeros([len(luokat),koppmaski.ET.size], bool)
    luvut = np.zeros(koppmaski.ET.size, np.int8)
    for nimi in koppmaski.keys():
        for ind_luok,luok in enumerate(luokat):
            if not re.match(luok,nimi):
                continue
            taul[ind_luok,:] |= koppmaski[nimi].data.flatten()
            luku = ind_luok+1 * koppmaski[nimi].data.flatten() * (ind_luok+1)
            luvut[koppmaski[nimi].data.flatten()] = ind_luok+1
    np.save("köppenmaski.npy",taul)
    np.savetxt("köppenmaski.txt", luvut, fmt="%i", delimiter='', newline='')

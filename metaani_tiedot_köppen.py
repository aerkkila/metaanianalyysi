#!/usr/bin/python3
import xarray as xr
import numpy as np
import sys
from metaani_tiedot_ import taul_pintaaloista

def main():
    dt = xr.open_dataset('./köppen_metaani_kokovuosi.nc')
    if '-s' in sys.argv:
        f = open('%s.txt' %(sys.argv[0][:-3]), 'w')
    else:
        f = sys.stdout
    f.write('kokovuosi\n%s\n' %taul_pintaaloista(dt).to_string())
    dt.close()
    dt = xr.open_dataset('./köppen_metaani_jäätymiskausi.nc')
    f.write('\njäätymiskausi\n%s\n' %taul_pintaaloista(dt))
    f.close()
    dt.close()

if __name__ == '__main__':
    main()

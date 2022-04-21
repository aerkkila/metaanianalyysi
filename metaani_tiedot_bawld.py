#!/usr/bin/python3
import config, sys
from metaani_tiedot_ import taul_pintaaloista
from bawld_metaani import bawld_metaani

def main():
    baw = bawld_metaani(config.edgartno_dir + 'posterior.nc')
    if '-s' in sys.argv[1:]:
        with open('%s.txt' %(sys.argv[0][:-3]), 'w') as f:
            f.write('%s\n' %taul_pintaaloista(baw).to_string())
    else:
        print(taul_pintaaloista(baw))
    baw.close()

if __name__ == '__main__':
    main()

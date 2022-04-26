#!/usr/bin/python3
from vuo_kartta_köppen import main
from flux1x1 import kaudet
import config, sys

if __name__ == '__main__':
    arg0 = sys.argv[0]
    for kausi in kaudet.keys():
        nimi = './vuo_bawld_%s.nc' %kausi
        sys.argv[0] = '%s_%s.py' %(arg0[:-3],kausi)
        main(nimi)

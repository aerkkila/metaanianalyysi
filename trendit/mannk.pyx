import numpy as np
from ctypes import *

cdef extern from "lue.c":
    int kausia, vuosia
    struct taul:
        int vuodet[15],
        double data[4][15],
        char kausinimet[4][32],
        char lajinimi[40]
    void lue_tahan(char* muuttuja, int luok, int kosteikko, taul* dest)

cdef taul tietue
lue_tahan(b"emissio", 1, 1, &tietue)

ydata = np.array(tietue.data)[:kausia,:vuosia]
xdata = np.array(tietue.vuodet)[:vuosia]

from libc.stdio cimport *
import numpy as np

cdef FILE* f = fopen("sovitteet.txt", "r")
cdef char sana[64]
kaudet = [b'summer', b'freezing', b'winter']
lajit = [b'bog', b'fen', b'marsh', b'permafrost_bog', b'tundra_wetland']
y = np.empty([len(kaudet),len(lajit)], np.float32)
err = np.empty([2,len(kaudet),len(lajit)], np.float32)

cdef lue_laji(int k, int l):
    cdef float y0, y1
    assert(fscanf(f, "%f", &y0) == 1)
    y[k,l] = y0
    assert(fscanf(f, "%f", &y1) == 1)
    err[0,k,l] = y0-y1
    assert(fscanf(f, "%f", &y1) == 1)
    err[1,k,l] = y1-y0

cdef lue_kausi(int k):
    cdef int sij = ftell(f)
    for l from 0 <= l < len(lajit):
        laji = lajit[l]
        while True:
            assert(fscanf(f, "%s", sana) == 1)
            if laji in sana:
                lue_laji(k, l)
                break
        fseek(f, sij, SEEK_SET)

for k from 0 <= k < len(kaudet):
    kausi = kaudet[k]
    while True:
        assert(fscanf(f, "%s", sana) == 1)
        if not kausi in sana:
            continue
        lue_kausi(k)
        break
    fseek(f, 0, SEEK_SET)

fclose(f)

x = np.arange(len(kaudet)*len(lajit))
y = y.flatten()
err = err.reshape([err.shape[0], err.shape[1]*err.shape[2]])

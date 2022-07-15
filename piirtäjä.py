#!/usr/bin/python3
from matplotlib.pyplot import *
import numpy as np
import sys, struct

rcParams.update({'figure.figsize':(12,10), 'font.size':13})
raaka = sys.stdin.buffer.read()

#raaka = nimi\n(pit)(data)(cdf)
while len(raaka):
    ind = raaka.index(10)
    nimi = raaka[:ind].decode('UTF-8')
    raaka = raaka[ind+1:]
    pit = struct.unpack("i", raaka[:4])[0] * 4
    raaka = raaka[4:]
    dt = np.ndarray(pit//4, dtype=np.float32, buffer=raaka[:pit])
    raaka = raaka[pit:]
    cdf = np.ndarray(pit//4, dtype=np.float32, buffer=raaka[:pit])
    raaka = raaka[pit:]
    vuo = dt*1e9
    alku = np.searchsorted(vuo, 0.001)

    if 1:
        dydx = np.diff(cdf[alku:]) / np.diff(vuo[alku:])
        plot(vuo[alku+1:], dydx, label=nimi)
    else:
        plot(vuo[alku:], cdf[alku:], label=nimi)
    print(np.mean(vuo), nimi)

xscale('log')#, linthreshx=0.01)
yscale('log')
xlabel('flux nmol/m/s$^2$')
ylabel('pdf')
legend()#loc='center right')
tight_layout()
show();

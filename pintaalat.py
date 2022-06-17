#!/usr/bin/python3
# muodostaa litteän taulukon, jossa on 55*360-resoluution 1x1-asteisen alueen pintaalat

import numpy as np

aste = 0.0174532925199
R2 = 40592558970441
PINTAALA1x1 = lambda _lat: aste*R2*(np.sin((_lat+1)*aste) - np.sin(_lat*aste))*1.0e-6

if __name__ == '__main__':
    lat0 = 29.5
    data = np.empty(19800)
    for i in range(55):
        data[i*360:(i+1)*360] = PINTAALA1x1(lat0+i)
    np.save("pintaalat.npy", data)

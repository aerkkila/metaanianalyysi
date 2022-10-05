#!/usr/bin/python
from matplotlib.pyplot import *
import numpy as np
import sys, struct

kansio = '../kuvia'

# sys.stdin.readline() ei toimi, koska myöhemmin tulee binääridataa, mistä Python ei ole iloinen.
def lue_rivi():
    lista = bytearray(b'')
    while True:
        a = sys.stdin.buffer.read(1)
        if len(a) == 0 or struct.unpack("b", a)[0] == 10:
            break
        lista.append(a[0])
    return lista.decode('UTF-8')

def main():
    global tehtiin, datastot, rajastot, nimet
    rcParams.update({'figure.figsize':(12,10), 'font.size':13})
    raaka = sys.stdin.buffer.read(8)
    pit,nboot = struct.unpack("ii", raaka)
    if nboot == 0:
        return
    kausi = lue_rivi()
    menetelmä = lue_rivi()
    ax = axes()
    data = np.empty([pit+1, 0], np.float64)
    alue = np.empty([0, 2, pit-1], np.float64)
    while(True):
        raaka = sys.stdin.buffer.read((pit+1)*8)
        if(len(raaka)==0):
            break
        dt = np.ndarray([pit+1,1], dtype=np.float64, buffer=raaka)
        data = np.concatenate([data, dt], axis=1)

        raaka = sys.stdin.buffer.read((pit-1)*nboot*8)
        dt = np.ndarray([nboot, pit-1], dtype=np.float64, buffer=raaka)
        dt = np.percentile(dt, [5,95], axis=0).reshape([1,2,pit-1])
        alue = np.concatenate([alue, dt], axis=0)
        #alue = np.concatenate([alue, np.concatenate([np.min(dt, axis=1).reshape([1,pit-1,1]),
        #                                             np.max(dt, axis=1).reshape([1,pit-1,1])], axis=2)], axis=0)

    värit = ['#ff0000', '#00ff00', '#0000ff']
    (nimet,tunniste) = (['bog', 'fen', 'marsh'],'bfm') if pit == 4 else (['permafrost_bog', 'tundra_wetland'],'pt')
    for i in range(pit-1):
        ax.plot(data[-1,:], data[i,:], c=värit[i], linewidth=2.5, label=nimet[i])
        ax.plot(data[-1,:], alue[:,0,i], c=värit[i], linestyle='--')
        ax.plot(data[-1,:], alue[:,1,i], c=värit[i], linestyle='--')
    #for i in range(pit-2):
    #    ax.fill_between(data[-1,:], alue[:,i,0], alue[:,i,1], color=värit[i], alpha=0.2)
    #ax.fill_between(data[:,-1], alue[:,0,0], alue[:,0,1], color='#ff000058')
    #ax.fill_between(data[:,-1], alue[:,1,0], alue[:,1,1], color='#00ff0058')
    #ax.fill_between(data[:,-1], alue[:,2,0], alue[:,2,1], color='#0000ff58')
    xlabel('upper flux limit')
    ylabel('flux')
    title(kausi)
    legend(loc='upper left')
    ax.twinx()
    ylabel('number of data')
    plot(data[-1,:], data[-2,:], color='k')
    if '-s' in sys.argv:
        savefig(kansio + '/wregressio_käyrä_%s_%s_%s.png' %(tunniste,kausi,menetelmä))
    else:
        show()

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

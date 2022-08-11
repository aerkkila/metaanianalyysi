#!/usr/bin/python
import pandas as pd
import numpy as np
import luokat

ftnrot = [2]

def main():
    nrows = len(luokat.ikir) + len(luokat.wetl) + len(luokat.kopp)
    ncols = len(luokat.kaudet) * len(ftnrot)
    nptaul,index = (np.empty([nrows,ncols*2]), np.empty(nrows, object))
    wyind = luokat.kaudet.index('whole_year')

    apu = [s.replace('_',' ') for s in luokat.kaudet]
    cols = [("%s" %(k) ,"%s" %(y)) for k in apu for y in ["Tg","‰"] ]

    for ppnum,pp in enumerate(luokat.pripost):
        rivi = 0
        for luoknum,luok in enumerate(luokat.luokittelut):
            rivilisa = -1
            sarake = 0
            for kausinum,kausi in enumerate(luokat.kaudet):
                for ftnum,ftnro in enumerate(ftnrot):
                    nimi = "vuotaulukot/%svuo_%s_%s_ft%i.csv" %(luok, pp, kausi, ftnro)
                    csv = pd.read_csv(nimi, comment='#', index_col=0, usecols=[0,1])
                    if rivilisa < 0:
                        rivilisa = len(csv.index)
                        apu = [s.replace('_',' ') for s in csv.index.to_list()]
                        index[rivi:rivi+rivilisa] = apu
                    # osuussarake muunnetaan vasta myöhemmin
                    nptaul[rivi: rivi+rivilisa, sarake*2:sarake*2+2] = np.tile(csv.iloc[:,0].to_numpy(), (2,1)).transpose()
                    sarake += 1
            rivi += rivilisa

        for i in range(nptaul.shape[0]):
            nptaul[i, 1::2] /= nptaul[i,wyind]/1000
        csv = pd.DataFrame(nptaul, index=index, columns=pd.MultiIndex.from_tuples(cols))
        s = csv.style
        s.format(precision=0, subset=(csv.index, csv.columns[1::2]))
        s.format(precision=5, subset=(csv.index, csv.columns[0::2]))
        s.to_latex('vuosummat_%s.tex' %(pp), hrules=True)

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

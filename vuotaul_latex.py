#!/usr/bin/python
import pandas as pd
import numpy as np
import luokat, os

def main():
    kolme = 3
    nrows = len(luokat.ikir) + len(luokat.wetl)+1 + len(luokat.kopp)
    ncols = len(luokat.kaudet)
    nptaul,index = (np.empty([nrows,ncols*kolme]), np.empty(nrows, object))
    wyind = luokat.kaudet.index('whole_year')

    apu = [s.replace('_',' ') for s in luokat.kaudet]
    cols = [("%s" %(k) ,"%s" %(y)) for k in apu for y in ["Tg","‰","nmol/m²/s"]]

    for ppnum,pp in enumerate(luokat.pripost):
        rivi = 0
        for luoknum,luok in enumerate(luokat.luokittelut):
            rivilisa = -1
            sarake = 0
            for kausinum,kausi in enumerate(luokat.kaudet):
                nimi = "vuotaulukot/%svuo_%s_%s_ft2.csv" %(luok, pp, kausi)
                csv = pd.read_csv(nimi, comment='#', index_col=0)
                if rivilisa < 0:
                    rivilisa = len(csv.index)
                    apu = [s.replace('_',' ') for s in csv.index.to_list()]
                    index[rivi:rivi+rivilisa] = apu
                # osuussarake muunnetaan vasta myöhemmin
                nptaul[rivi: rivi+rivilisa, sarake*kolme:(sarake+1)*kolme] = \
                    np.concatenate([np.tile(csv.iloc[:,0].to_numpy(), (2,1)).transpose(), csv.iloc[:,[1]].to_numpy()], axis=1)
                sarake += 1
            rivi += rivilisa

        for i in range(nptaul.shape[0]):
            nptaul[i, 1::kolme] /= nptaul[i,wyind]/1000
        csv = pd.DataFrame(nptaul, index=index, columns=pd.MultiIndex.from_tuples(cols))
        s = csv.style
        s.format(precision=0, subset=(csv.index, csv.columns[1::kolme]))
        s.format(precision=3, subset=(csv.index, csv.columns[0::kolme]))
        s.format(precision=3, subset=(csv.index, csv.columns[2::kolme]))
        nimi = 'vuosummat_%s.tex' %(pp)
        s.to_latex(nimi, hrules=True)
        os.system('ed -s %s <<EOF\n1\ns/rrr/rrr|/g\nw\nq\nEOF' %nimi) # lisätään pystyviivat kausien väleihin

        #taulukosta tiivistelmä
        csv.drop(columns=csv.columns.to_list()[:3], inplace=True) # kokovuosi pois
        csv.drop(columns=csv.columns.to_list()[::3], inplace=True) # Tg pois
        csv.drop(index=['wetland'], inplace=True)
        s = csv.style
        s.format(precision=0, subset=(csv.index, csv.columns[0::2]))
        s.format(precision=3, subset=(csv.index, csv.columns[1::2]))
        nimi = 'vuosummat_tiivistelmä_%s.tex' %(pp)
        s.to_latex(nimi, hrules=False)
        os.system('ed -s %s <<EOF\n1\ns/rr/rr|/g\nw\nq\nEOF' %nimi) # lisätään pystyviivat kausien väleihin

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')
        exit()

#!/usr/bin/python3
import pandas as pd
from wetlandvuo_data import kaudet

if __name__=='__main__':
    kansio = 'wetlandvuo_tulos/'
    summa = pd.read_csv(kansio + "summataul.csv", index_col=0)
    for k_ind,kausi in enumerate(kaudet):
        r2 = pd.read_csv(kansio + "r2taul_%s.csv" %(kausi), index_col=0)
        vuo = pd.read_csv(kansio + "täysvuo_%s.csv" %(kausi), index_col=0)
        vuo90 = pd.read_csv(kansio + "täysvuo90_%s.csv" %(kausi), index_col=0)
        tied = open(kansio + 'yhdistelmä_%s.csv' %(kausi), 'w')
        tied.write(",R²,vuo(nmol/m²/s),vuo90%,kauden_summa(Tg)\n")
        for wtyyppi in r2.index:
            tied.write("%s,%.3f,%.3f,%.3f,%.3f\n"
                       %(wtyyppi, r2.loc[wtyyppi,'kaikki_2sel.'], vuo.loc[wtyyppi,'kaikki_2sel.'], vuo90.loc[wtyyppi,'kaikki_2sel.'], summa.loc[kausi,'kaikki_2sel.']))
        tied.close()

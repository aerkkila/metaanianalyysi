#!/usr/bin/python
from virhepalkit import *
from matplotlib.pyplot import *

hakemisto = '../'

lajit = [l.decode('UTF-8') for l in lajit]
rcParams.update({'figure.figsize':(12,10), 'font.size':14})
assert(len(x)%3 == 0)
pit = len(x) // 3

erivärit = 'rkb'
for i in range(len(kaudet)):
    sl = slice(i*pit,(i+1)*pit)
    errorbar(x[sl], y[sl], err[:,sl], fmt='o', color=erivärit[i])
    plot([np.nan], 'o', label=kaudet[i].decode('UTF-8'), color=erivärit[i])

xticks(x, lajit*len(kaudet), rotation=90)
ylabel('nmol m$^{-2}$ s$^{-1}$')
grid('on', axis='y')
lim = gca().get_yticks()[1:-1]
yticks(np.arange(lim[0], lim[-1], 2.5))
legend(loc='upper right')
tight_layout()
if '-s' in sys.argv:
    savefig(hakemisto + 'kuvia/wregressio_virhepalkit.png')
else:
    show()

#!/bin/env python
from virhepalkit import *
from matplotlib.pyplot import *

hakemisto = '../'

lajit = [l.decode('UTF-8').replace('_',' ') for l in lajit]
rcParams.update({'figure.figsize':(10,8), 'font.size':15})
assert(len(x)%3 == 0)
pit = len(x) // 3

def piirrä(kausi, ax=None):
    if ax is None:
        ax = gca()
    sl = slice(kausi*pit,(kausi+1)*pit)
    ax.errorbar(x[sl], y[sl], err[:,sl], fmt='o', color=erivärit[kausi]) # piirtää kaiken
    ax.plot([np.nan], 'o', label=kaudet[kausi].decode('UTF-8'), color=erivärit[kausi]) # ei piirrä, vaan legendiä varten

erivärit = 'rkb'
for i in range(len(kaudet)):
    piirrä(i)

xticks(x, lajit*len(kaudet), rotation=90)
ylabel('nmol m$^{-2}$ s$^{-1}$')
grid('on', axis='y')
lim = gca().get_yticks()[1:-1]
yticks(np.arange(lim[0], lim[-1], 2.5))
legend(loc='upper right', fancybox=0)

# piirretään suurennosalue talvesta
ax = gca()
axins = ax.inset_axes([0.65, 0.25, 0.20, 0.48])
talvi = 2
piirrä(talvi, axins)
axins.grid('on', axis='y')
# valitaan alkuperäisen alue
väli = (x[1]-x[0]) * 0.3
val = np.zeros(len(x), bool) # talvi ilman marshia
val[pit*2:] = True
val[pit*2+2] = False
ymin = min(y[val]-err[0,val])
ymax = max(y[val]+err[1,val])
tilaa = (ymax - ymin) * 0.04
axins.set_ylim(ymin-tilaa, ymax+tilaa)
axins.set_xlim(x[talvi*pit]-väli, x[(talvi+1)*pit-1]+väli)
axins.set_xticks([])
# merkitään alue zoomatuksi
ax.indicate_inset_zoom(axins, edgecolor='k')

tight_layout()
if '-s' in sys.argv:
    savefig(hakemisto + 'kuvia/wregressio_virhepalkit.png')
else:
    show()

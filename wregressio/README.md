## Separating wetland subcategories using linear regression
**wregressio<area>.c** finds methane flux values for wetland subcategories using linear regression with all frac(category)/frac(wetland) as explanatory variables and flux/frac(wetland) as y. Bog-fen-marsh and permafrost_bog-tundra-wetland areas are handled separately. Program executes in these steps.

1. Find the optimal limit for flux using cross validation. \
   Higher fluxes are discarded and the same surface area with lowest flux values is also discarded.

2. Predict the flux and get confidence interval using the bootstrapping method.

3. Call **piirrä.py** to draw scatterplots and regression curves.

**laske.sh** automates calling wregressio<area>.out \
**virhepalkit.py[x]** &rarr; wregressio_virhepalkit.py draws the flux values and errorbars calculated by wregressio<area>.c. \
**piirrä.py** &rarr; wregressio\_suora_{season}_{category}.png is called from wregressio.c to draw the scatterplots. \
**taulukko_rajat.c** &rarr; wregr_rajat.tex reads output from wregressio.c and compiles some parameters into latex table

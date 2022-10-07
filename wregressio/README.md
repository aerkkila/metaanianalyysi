## Separating wetland subcategories using linear regression
**wregressio<area>.c** finds methane flux values for wetland subcategories using linear regression with all frac(category)/frac(wetland) as explanatory variables and flux/frac(wetland) as y. Bog-fen-marsh and permafrost_bog-tundra-wetland areas are handled separately. Steps are these.

1. Find the optimal limit for flux using cross validation. \
   Higher fluxes are discarded and the same number of lowest flux values are also discarded. \
   The parameter to optimize is error in total emission rate when calculated from predicted fluxes.

2. Predict the flux and get confidence interval using bootstrap-method.

**laske.sh** automates calling wregressio<area>.out \
**virhepalkit.py[x]** draws the flux values and errorbars calculated by wregressio<area>.c.

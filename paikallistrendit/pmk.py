"""
A fork of the following program:

Created on 05 March 2018
Update on 28 May 2021
@author: Md. Manjurul Hussain Shourov
version: 1.4.2
Approach: Vectorisation
Citation: Hussain et al., (2019). pyMannKendall: a python package for non parametric Mann Kendall family of trend tests.. Journal of Open Source Software, 4(39), 1556, https://doi.org/10.21105/joss.01556
"""

import numpy as np
from scipy.stats import norm
from collections import namedtuple


# vectorization approach to calculate mk score, S
def __mk_score(x):
    n = len(x)
    s = 0
    for k in range(n-1):
        s = s + np.sum(x[k+1:n] > x[k]) - np.sum(x[k+1:n] < x[k])
    return s

	
# original Mann-Kendal's variance S calculation
def __variance_s(x):
    n = len(x)
    # calculate the unique data
    unique_x = np.unique(x)
    g = len(unique_x)

    # calculate the var(s)
    if n == g:            # there is no tie
        return (n*(n-1)*(2*n+5))/18
        
    # there are some ties in data
    tp = np.empty(g)
    for i in range(g):
        tp[i] = np.sum(x == unique_x[i])
    return (n*(n-1)*(2*n+5) - np.sum(tp*(tp-1)*(2*tp+5)))/18


# standardized test statistic Z
def __z_score(s, var_s):
    if s > 0:
        return (s - 1)/np.sqrt(var_s)
    if s == 0:
        return 0
    return (s + 1)/np.sqrt(var_s)


# calculate the p_value in two tail test
__p_value = lambda z: 2*(1-norm.cdf(abs(z)))  


# Original Sens Estimator
def __sens_estimator(x, xakseli):
    idx = 0
    n = len(x)
    d = np.empty(int(n*(n-1)/2))

    for i in range(n-1):
        d[idx: idx+n-1-i] = (x[i+1:] - x[i]) / (xakseli[i+1:n] - xakseli[i])
        idx = idx + n-1-i

    return d


def sens_slope(x, xakseli):
    res = namedtuple('Sens_Slope_Test', ['slope','intercept'])
    n = len(x)
    slope = np.median(__sens_estimator(x, xakseli))
    if n%2:
        intercept = np.median(x) - xakseli[n//2] * slope
    else:
        ind = n//2
        intercept = np.median(x) - np.mean(xakseli[ind-1:ind+1]) * slope
    return res(slope, intercept)


def original_test(x, xakseli):
    """
    This function checks the Mann-Kendall (MK) test (Mann 1945, Kendall 1975, Gilbert 1987).
    Input:
        x: yvalues: a 1-D numpy array without NAN values
        xakseli: xvalues like yvalues, naming confusion is due to the original pymannkendall library
    Output:
        p: p-value of the significance test
        slope: Theil-Sen estimator/slope
        intercept: intercept of Kendall-Theil Robust Line
    Examples
    --------
	  >>> import numpy as np
      >>> import pymannkendall as mk
      >>> x = np.random.rand(1000)
      >>> p,slope,intercept = mk.original_test(x)
    """
    res = namedtuple('Mann_Kendall_Test', ['p', 'slope', 'intercept'])
    
    s = __mk_score(x)
    var_s = __variance_s(x)
    
    z = __z_score(s, var_s)
    p = __p_value(z)
    slope, intercept = sens_slope(x, xakseli)

    return res(p, slope, intercept)

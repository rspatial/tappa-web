---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Kriging

## Alberta rainfall

Recreating Figures 10.2 and 10.13 in
[O'Sullivan and Unwin (2010)](http://www.wiley.com/WileyCDA/WileyTitle/productCd-0470288574.html).

```{code-cell} python
:tags: [krig0]
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import statsmodels.api as sm
from scipy.spatial.distance import pdist, squareform

DATA = Path("../../data").resolve()
ROSU = DATA / "rosu"

a = pd.read_csv(ROSU / "alberta.csv")
a.head()
```

Figure 10.2 — trend surface and sample labels:

```{code-cell} python
:tags: [krig1]
m = sm.OLS(a["z"], sm.add_constant(a[["x", "y"]])).fit()
print(m.summary().tables[1])

fig, ax = plt.subplots(figsize=(6, 6))
ax.scatter(a["x"], a["y"], s=30)
for _, row in a.iterrows():
    ax.text(row["x"], row["y"], f"{row['z']:.0f}", fontsize=8, va="bottom")
ax.set_xlim(0, 60)
ax.set_ylim(0, 60)
ax.set_aspect("equal")

xy = np.array(np.meshgrid(np.arange(0, 61), np.arange(0, 61))).reshape(2, -1).T
zhat = m.predict(sm.add_constant(xy))
Z = zhat.reshape(61, 61)
ax.contour(np.arange(0, 61), np.arange(0, 61), Z, colors="black");
```

Distance matrix for locations:

```{code-cell} python
coords = a[["x", "y"]].to_numpy()
dp = squareform(pdist(coords))
np.fill_diagonal(dp, np.nan)
dp[:5, :5]
```

Semivariance cloud (Figure 10.13):

```{code-cell} python
:tags: [krig5]
zvals = a["z"].to_numpy()
dz = squareform(pdist(zvals.reshape(-1, 1)))
semivar = dz ** 2 / 2.0

mask = ~np.isnan(dp)
fig, ax = plt.subplots(figsize=(6, 5))
ax.scatter(dp[mask], semivar[mask], s=20)
ax.set_xlim(0, 80)
ax.set_ylim(0, 220)
ax.set_xlabel("Distance between locations")
ax.set_ylabel("Semivariance");
```

Binned semivariance:

```{code-cell} python
:tags: [krig10]
binwidth = 8
lag = np.floor(dp / binwidth).astype(int) + 1
lsv = {}
dlag = {}
for k in np.unique(lag[~np.isnan(lag)]):
    sel = lag == k
    lsv[k] = np.nanmean(semivar[sel])
    dlag[k] = np.nanmean(dp[sel])

fig, ax = plt.subplots(figsize=(6, 5))
ax.scatter(list(dlag.values()), list(lsv.values()), s=30)
ax.set_xlim(0, 80)
ax.set_xlabel("Distance")
ax.set_ylabel("Semivariance");
```

Continue with the [Interpolation](../analysis/4-interpolation) chapter for
variogram modelling and kriging in *tappa*.

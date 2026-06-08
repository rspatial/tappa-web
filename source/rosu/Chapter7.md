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

# Spatial autocorrelation

This page accompanies Chapter 7 in
[O'Sullivan and Unwin (2010)](https://www.wiley.com/en-us/Geographic+Information+Analysis%2C+2nd+Edition-p-9780470288573).

```{code-cell} python
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import tappa as pt

DATA = Path("../../data").resolve()
ROSU = DATA / "rosu"
DATA, ROSU
```

## The area of a polygon

Create a polygon like Figure 7.2 and compute area "by hand" first.

```{code-cell} python
xy = np.array([
    [1.7, 4.9],
    [2.6, 7.0],
    [5.6, 7.6],
    [8.1, 6.1],
    [7.2, 2.7],
    [3.3, 2.7],
], dtype=float)

g = np.column_stack([
    np.ones(xy.shape[0], dtype=int),  # id
    np.ones(xy.shape[0], dtype=int),  # part
    xy[:, 0], xy[:, 1]
])
sppol = pt.vect(g, type="polygons", crs="+proj=utm +zone=1")
sppol
```

```{code-cell} python
p = np.vstack([xy, xy[0]])
x = p[1:, 0] - p[:-1, 0]
y = (p[1:, 1] + p[:-1, 1]) / 2
manual_area = np.sum(x * y)
manual_area
```

And now with `pt.expanse()`.

```{code-cell} python
pt.expanse(sppol)
```

```{admonition} Note
:class: note

The original *R* handout includes a "contact numbers" section for the lower 48
USA states. We skip it here because reproducing that workflow with historical
state boundaries is slow and the original GADM export used in that example is no
longer straightforward to reproduce. OSU Table 7.1 also appears to use a
different data vintage. You can try `pt.relate()` on your own polygon data to
recreate that exercise.
```

## Spatial structure (Auckland TB data)

```{code-cell} python
pols = pt.vect(str(ROSU / "auctb.gpkg"))
pols
```

```{code-cell} python
tb = pols["TB"].astype(float)
bins = np.arange(0, 451, 50)
cats = pd.cut(tb, bins=bins, include_lowest=True, right=False)
codes = cats.codes
palette = plt.cm.Greys(np.linspace(0.2, 0.9, len(cats.categories)))
cols = [palette[i] if i >= 0 else (0.8, 0.8, 0.8, 1.0) for i in codes]

fig, ax = plt.subplots(figsize=(7, 6))
pt.plot(pols, ax=ax, col=cols, border="white", legend=False)
ax.set_title("Estimated TB incidence in Auckland census areas")
```

Build several neighbour definitions with `pt.adjacent()`, `pt.nearby()`,
`pt.delaunay()`, and `pt.centroids()`.

```{code-cell} python
v = pt.centroids(pols)
xyc = pt.crds(v)

wr = pt.adjacent(pols, type="rook", pairs=True, symmetrical=True)
wq = pt.adjacent(pols, type="queen", pairs=True, symmetrical=True)
wd1 = pt.nearby(v, distance=1000, pairs=True)
wd25 = pt.nearby(v, distance=2500, pairs=True)
k3 = pt.nearby(v, k=3, pairs=True)
k6 = pt.nearby(v, k=6, pairs=True)
d = pt.delaunay(v)
```

```{code-cell} python
def draw_pairs(ax, pairs, title):
    pt.plot(pols, ax=ax, col="lightgray", border="white", legend=False)
    for a, b in pairs:
        ax.plot([xyc[a, 0], xyc[b, 0]], [xyc[a, 1], xyc[b, 1]],
                color="red", lw=1.5)
    pt.points(v, ax=ax, col="black", s=8)
    ax.set_title(title)
    ax.set_xticks([]); ax.set_yticks([])


fig, axes = plt.subplots(4, 2, figsize=(11, 14))
draw_pairs(axes[0, 0], wr, "Rook adjacency")
draw_pairs(axes[0, 1], wq, "Queen adjacency")
draw_pairs(axes[1, 0], wd1, "Distance <= 1000 m")
draw_pairs(axes[1, 1], wd25, "Distance <= 2500 m")
draw_pairs(axes[2, 0], k3, "k nearest (k=3)")
draw_pairs(axes[2, 1], k6, "k nearest (k=6)")

pt.plot(pols, ax=axes[3, 0], col="lightgray", border="white", legend=False)
pt.lines(d, ax=axes[3, 0], col="red", lwd=1.5)
axes[3, 0].set_title("Delaunay triangulation")
axes[3, 0].set_xticks([]); axes[3, 0].set_yticks([])

axes[3, 1].axis("off")
fig.tight_layout();
```

## Moran's *I*

Compute Moran's *I* "by hand", following OSU Eq. 7.7.

\[
I = \frac{n}{\sum_{i=1}^{n}(y_i - \bar{y})^2}
    \frac{\sum_{i=1}^{n}\sum_{j=1}^{n} w_{ij}(y_i-\bar{y})(y_j-\bar{y})}
         {\sum_{i=1}^{n}\sum_{j=1}^{n} w_{ij}}
\]

```{code-cell} python
y = pols["TB"].astype(float)
n = y.size
ybar = y.mean()
dy = y - ybar

pm = np.outer(dy, dy)
wm = pt.adjacent(pols, type="rook", pairs=False).astype(int)
pmw = pm * wm

spmw = pmw.sum()
smw = wm.sum()
vr = n / np.sum(dy ** 2)
MI = vr * (spmw / smw)
MI
```

Now compute Moran's *I* with `pt.autocor()` using a numeric vector and the
weights matrix.

```{code-cell} python
pt.autocor(y, wm, method="moran")
```

Expected value under spatial randomness:

```{code-cell} python
EI = -1 / (n - 1)
EI
```

### Monte Carlo significance

```{code-cell} python
rng = np.random.default_rng(7)
nsim = 999
I_obs = float(pt.autocor(y, wm, method="moran"))
mc = np.array([pt.autocor(rng.permutation(y), wm, method="moran")
               for _ in range(nsim)])
p_hi = (mc >= I_obs).sum() / (nsim + 1)
I_obs, p_hi
```

```{code-cell} python
fig, ax = plt.subplots(figsize=(6, 4))
ax.hist(mc, bins=24, edgecolor="black")
ax.axvline(I_obs, color="red", lw=2, label=f"Observed I = {I_obs:.3f}")
ax.set_xlabel("Simulated Moran's I")
ax.set_ylabel("Frequency")
ax.legend();
```

### Moran scatter plot

```{code-cell} python
neigh_sum = wm @ y
neigh_n = wm.sum(axis=1)
lagged_y = neigh_sum / neigh_n

slope, intercept = np.polyfit(y, lagged_y, 1)
xx = np.linspace(y.min(), y.max(), 100)

fig, ax = plt.subplots(figsize=(6, 5))
ax.scatter(y, lagged_y, color="red", s=60)
ax.plot(xx, slope * xx + intercept, color="blue", lw=2)
ax.axhline(lagged_y.mean(), ls="--", color="black")
ax.axvline(ybar, ls="--", color="black")
ax.set_xlabel("y (TB)")
ax.set_ylabel("spatially lagged y")
ax.set_title("Moran scatter plot");
```

The slope of the fitted line is close to Moran's *I*:

```{code-cell} python
slope
```

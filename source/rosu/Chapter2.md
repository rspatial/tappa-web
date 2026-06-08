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

# Pitfalls and potential

## Introduction

This page shows how you can implement the examples provided in Chapter 2 of
[O'Sullivan and Unwin (2010)](https://www.wiley.com/en-us/Geographic+Information+Analysis%2C+2nd+Edition-p-9780470288573).
Go through the examples slowly, line by line. Inspect the objects created and
read the API documentation for the functions used.

## The Modifiable Areal Unit Problem

Below we recreate the data shown on page 37. There is one region divided into
6 × 6 = 36 grid cells. For each cell we have values for two variables.

```{code-cell} python
:tags: [ch2-1]
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import statsmodels.api as sm
import tappa as pt

ind = np.array([
    87, 95, 72, 37, 44, 24,
    40, 55, 55, 38, 88, 34,
    41, 30, 26, 35, 38, 24,
    14, 56, 37, 34,  8, 18,
    49, 44, 51, 67, 17, 37,
    55, 25, 33, 32, 59, 54], dtype=float)

dep = np.array([
    72, 75, 85, 29, 58, 30,
    50, 60, 49, 46, 84, 23,
    21, 46, 22, 42, 45, 14,
    19, 36, 48, 23,  8, 29,
    38, 47, 52, 52, 22, 48,
    58, 40, 46, 38, 35, 55], dtype=float)

fig, ax = plt.subplots(figsize=(5, 4))
ax.scatter(ind, dep)
ax.set_xlabel("ind")
ax.set_ylabel("dep");
```

Fit a linear regression model (`dep ~ ind`):

```{code-cell} python
X = sm.add_constant(ind)
m = sm.OLS(dep, X).fit()
m.summary().tables[1]
```

```{code-cell} python
:tags: [ch2-2]
fig, ax = plt.subplots(figsize=(5, 4))
ax.scatter(ind, dep)
xline = np.linspace(ind.min(), ind.max(), 50)
ax.plot(xline, m.predict(sm.add_constant(xline)))
```

A plot closer to the one in the book:

```{code-cell} python
:tags: [ch2-3]
fig, ax = plt.subplots(figsize=(5, 5))
ax.scatter(ind, dep, marker="D", s=50)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.set_xticks(np.arange(0, 101, 20))
ax.set_yticks(np.arange(0, 101, 20))
ax.set_xlabel("")
ax.set_ylabel("")
for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)

f = f"y = {m.params[1]:.4f}x + {m.params[0]:.4f}"
ax.text(0, 96, f, va="top")
R2 = np.corrcoef(dep, m.fittedvalues)[0, 1] ** 2
ax.text(0, 85, f"$R^2$ = {R2:.4f}", va="top")
px = np.array([ind.min(), ind.max()])
py = m.predict(sm.add_constant(px))
ax.plot(px, py, color="black", lw=2);
```

Turn the vectors into matrices:

```{code-cell} python
mi = ind.reshape(6, 6)
md = dep.reshape(6, 6)
mi
```

Turn the matrices into `SpatRaster` objects:

```{code-cell} python
:tags: [ch2-4a]
ri = pt.rast(mi)
rd = pt.rast(md)
ri
```

```{code-cell} python
:tags: [ch2-4b]
pt.plot(ri, legend=False, figsize=(4, 4));
```

Aggregate sets of 2 columns (scheme 1):

```{code-cell} python
:tags: [ch2-5a]
ai1 = pt.aggregate(ri, [1, 2], fun="mean")
ad1 = pt.aggregate(rd, [1, 2], fun="mean")
pt.as_matrix(ai1)
```

```{code-cell} python
:tags: [ch2-5b]
pt.plot(ai1, legend=False, figsize=(4, 4));
```

Combine layers and coerce to a `DataFrame`:

```{code-cell} python
:tags: [ch2-6]
s1 = pt.rast([ai1, ad1])
s1 = pt.set_names(s1, ["ind", "dep"])
d1 = pt.as_data_frame(s1)
d1.head()
```

```{code-cell} python
ma1 = sm.OLS(d1["dep"], sm.add_constant(d1["ind"])).fit()
ma1.params
```

Aggregation scheme 2 (2 rows, 1 column):

```{code-cell} python
:tags: [ch2-7]
ai2 = pt.aggregate(ri, [2, 1], fun="mean")
ad2 = pt.aggregate(rd, [2, 1], fun="mean")
s2 = pt.rast([ai2, ad2])
s2 = pt.set_names(s2, ["ind", "dep"])
d2 = pt.as_data_frame(s2)
ma2 = sm.OLS(d2["dep"], sm.add_constant(d2["ind"])).fit()
m.params, ma1.params, ma2.params
```

Figure 2.1-style panel (simplified):

```{code-cell} python
:tags: [figmaup]
def plot_maup(r1, r2, title=""):
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.5))
    for ax, r, ttl in zip(axes[:2], (r1, r2), title.split("|") if "|" in title else [title, ""]):
        pt.plot(pt.as_polygons(r, aggregate=False), ax=ax, col="none", border="black")
        vals = pt.values(r).ravel()
        for cell, val in enumerate(vals):
            rc = pt.row_col_from_cell(r, [cell])[0]
            xy = pt.xy_from_cell(r, [cell])[0]
            ax.text(xy[0], xy[1], f"{val:.0f}", ha="center", va="center", fontsize=9)
        if ttl:
            ax.set_title(ttl)
        ax.set_axis_off()
    i = pt.values(r1).ravel()
    d = pt.values(r2).ravel()
    axes[2].scatter(i, d, marker="D", s=50)
    axes[2].set_xlim(0, 100)
    axes[2].set_ylim(0, 100)
    mod = sm.OLS(d, sm.add_constant(i)).fit()
    px = np.array([i.min(), i.max()])
    axes[2].plot(px, mod.predict(sm.add_constant(px)), color="black", lw=2)
    axes[2].set_xlabel("ind")
    axes[2].set_ylabel("dep")
    return fig

plot_maup(ri, rd, "Independent variable|Dependent variable")
plot_maup(ai1, ad1, "Aggregation scheme 1")
plot_maup(ai2, ad2, "Aggregation scheme 2");
```

## Distance, adjacency, interaction, neighborhood

Data for Figure 2.2 (page 46):

```{code-cell} python
pts = np.array([
    [40, 43], [1, 101], [54, 111], [104, 65], [60, 22], [20, 2]], dtype=float)
pts
```

```{code-cell} python
:tags: [points]
fig, ax = plt.subplots(figsize=(5, 5))
ax.scatter(pts[:, 0], pts[:, 1], s=60, c="red")
for label, (x, y) in zip("ABCDEF", pts):
    ax.text(x + 5, y + 5, label)
ax.set_xlim(0, 120)
ax.set_ylim(0, 120)
ax.set_xlabel("X")
ax.set_ylabel("Y");
```

### Distance

```{code-cell} python
from scipy.spatial.distance import pdist, squareform

D = squareform(pdist(pts))
np.round(D)
```

### Adjacency

Points within distance 50:

```{code-cell} python
a = D < 50
np.fill_diagonal(a, False)
adj50 = a.astype(int)
adj50
```

Three nearest neighbors:

```{code-cell} python
cols = np.argsort(D, axis=1)[:, 1:4]
rowcols = np.column_stack([
    np.repeat(np.arange(6), 3),
    cols.ravel(),
])
Ak3 = np.zeros_like(adj50)
Ak3[rowcols[:, 0], rowcols[:, 1]] = 1
Ak3
```

### Weights matrix

```{code-cell} python
W = 1.0 / D
np.fill_diagonal(W, np.nan)
rtot = np.nansum(W, axis=1)
W = W / rtot[:, None]
np.nansum(W, axis=1)
```

### Proximity polygons

```{code-cell} python
:tags: [ch2-20]
vp = pt.vect(pts)
v = pt.voronoi(vp)

fig, ax = plt.subplots(figsize=(6, 6))
palette = [plt.cm.rainbow(i / max(pt.nrow(v) - 1, 1)) for i in range(pt.nrow(v))]
pt.plot(v, ax=ax, border="gray", col=palette)
pt.points(vp, ax=ax, s=50)
for label, row in zip("ABCDEF", pts):
    ax.text(row[0] + 2, row[1] + 2, label, fontsize=12)
ax.set_axis_off();
```

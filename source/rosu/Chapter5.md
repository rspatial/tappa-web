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

# Point pattern analysis

## Introduction

This page accompanies Chapter 5 of
[O'Sullivan and Unwin (2010)](https://www.wiley.com/en-us/Geographic+Information+Analysis%2C+2nd+Edition-p-9780470288573),
using *Python* and *tappa*.

```{code-cell} python
:tags: [imports]
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist, squareform, cdist
import tappa as pt

DATA = Path("../../data").resolve()
ROSU = DATA / "rosu"

city = pt.vect(str(DATA / "city.gpkg"))
crime = pt.vect(str(DATA / "crime.gpkg"))
counties = pt.vect(str(DATA / "counties.gpkg"))

print("city polygons:", city.nrow())
print("crime points :", crime.nrow())
print("counties     :", counties.nrow())
```

A map of the city and crime point locations.

```{code-cell} python
ax = pt.plot(city, col="lightblue", legend=False, figsize=(8, 4))
pt.points(crime, ax=ax, color="red", s=4, marker="+");
```

A sorted table of crime categories.

```{code-cell} python
crime_df = pt.vect_as_df(crime)
tb = crime_df["CATEGORY"].value_counts(dropna=True).sort_values()
tb
```

Get event coordinates and remove duplicates.

```{code-cell} python
xy = pt.geom(crime)[:, 2:4]
print("all points   :", xy.shape)
xy = np.unique(xy, axis=0)
print("unique events:", xy.shape)
xy[:5]
```

## Basic statistics

Compute the mean center and standard distance.

```{code-cell} python
mc = xy.mean(axis=0)
sd = float(np.sqrt(((xy - mc) ** 2).sum() / xy.shape[0]))
mc, round(sd, 2)
```

Plot points, mean center, and standard-distance circle.

```{code-cell} python
bearing = np.linspace(0, 2 * np.pi, 360)
circle = np.column_stack([mc[0] + sd * np.cos(bearing), mc[1] + sd * np.sin(bearing)])

ax = pt.plot(city, col="lightblue", legend=False, figsize=(8, 4.5))
ax.scatter(xy[:, 0], xy[:, 1], s=2, color="black")
ax.scatter(mc[0], mc[1], marker="*", s=260, color="red")
ax.plot(circle[:, 0], circle[:, 1], color="red", lw=2);
```

## Density and quadrat counts

Compute average point density.

```{code-cell} python
city_area = pt.expanse(city)[0]
dens = xy.shape[0] / city_area
print(f"city area: {city_area:.2f}")
print(f"density  : {dens:.6g} points per map-unit squared")
```

Create quadrats using a 1000-unit raster resolution.

```{code-cell} python
r = pt.rast(city, resolution=1000)
r = pt.rasterize(city, r)

ax = pt.plot(r, figsize=(8, 4), legend=False)
pt.points(crime, ax=ax, color="red", s=4);
```

Count points in each quadrat.

```{code-cell} python
nc = pt.rasterize(crime, r, fun="count", background=0)
ncrimes = pt.mask(nc, r)

ax = pt.plot(ncrimes, figsize=(8, 4))
pt.lines(city, ax=ax);
```

Frequency table of quadrat counts.

```{code-cell} python
f = pt.freq(ncrimes)
f
```

```{code-cell} python
f_df = f.copy()
f_df.head()
```

```{code-cell} python
fig, ax = plt.subplots(figsize=(5.5, 3.8))
ax.scatter(f_df["value"], f_df["count"], s=24)
ax.set_xlabel("Crimes per quadrat")
ax.set_ylabel("Number of quadrats");
```

Mean, variance, and VMR (variance-to-mean ratio):

```{code-cell} python
vals = pt.values(ncrimes, mat=False)
vals = vals[~np.isnan(vals)]

mu = vals.mean()
s2 = vals.var(ddof=1)
vmr = s2 / mu

print(f"mu  = {mu:.3f}")
print(f"s2  = {s2:.3f}")
print(f"VMR = {vmr:.3f}")
```

## Distance-based measures

Pairwise event distances.

```{code-cell} python
dm = squareform(pdist(xy))
np.fill_diagonal(dm, np.nan)
dm[:5, :5].round(1)
```

Nearest-neighbor distance per event:

```{code-cell} python
dmin = np.nanmin(dm, axis=1)
dmin[:6].round(2)
```

Mean nearest-neighbor distance:

```{code-cell} python
mdmin = dmin.mean()
mdmin
```

Nearest-neighbor index (which point is nearest to each point):

```{code-cell} python
dm_inf = np.where(np.isnan(dm), np.inf, dm)
wdmin = np.argmin(dm_inf, axis=1)
wdmin[:6]
```

Plot the 25 most isolated events and their nearest neighbors.

```{code-cell} python
:tags: [pp10]
ord_ = np.argsort(dmin)[::-1]
far25 = ord_[:25]
neighbors = wdmin[far25]

ax = pt.plot(city, col="lightblue", legend=False, figsize=(8, 4.5))
ax.scatter(xy[:, 0], xy[:, 1], s=2, color="black")
ax.scatter(xy[far25, 0], xy[far25, 1], s=28, color="blue")
ax.scatter(xy[neighbors, 0], xy[neighbors, 1], s=35, facecolors="none", edgecolors="red")
for i, j in zip(far25, neighbors):
    ax.plot([xy[i, 0], xy[j, 0]], [xy[i, 1], xy[j, 1]], color="red", lw=0.8);
```

## G, F, and K functions

### G function

```{code-cell} python
g_distance = np.sort(np.unique(np.round(dmin)))
Gd = np.array([np.sum(dmin < d) for d in g_distance], dtype=float) / len(dmin)

fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
axes[0].plot(g_distance, Gd, lw=2)
axes[0].set_title("G(d)")
axes[0].set_xlabel("Distance")
axes[0].set_ylabel("G(d)")
axes[1].plot(g_distance, Gd, lw=2)
axes[1].set_xlim(0, 500)
axes[1].set_title("G(d), first 500 units")
axes[1].set_xlabel("Distance");
```

### F function

Use raster-cell centers as the reference locations.

```{code-cell} python
centers = pt.as_points(r)
p_xy = pt.geom(centers)[:, 2:4]

d2 = cdist(p_xy, xy)
mind = d2.min(axis=1)

f_distance = np.sort(np.unique(np.round(mind)))
Fd = np.array([np.sum(mind < d) for d in f_distance], dtype=float) / len(mind)

fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(f_distance, Fd, lw=2)
ax.set_xlim(0, 3000)
ax.set_xlabel("Distance")
ax.set_ylabel("F(d)");
```

Expected Poisson process curve:

```{code-cell} python
def ef(d, lam):
    return 1 - np.exp(-lam * np.pi * d ** 2)


d_grid = np.arange(0, 2001)
expected = ef(d_grid, dens)
```

Combined F, G, expected plot.

```{code-cell} python
fig, ax = plt.subplots(figsize=(6.2, 4.2))
ax.plot(g_distance, Gd, lw=2, color="red", label="G(d)")
ax.plot(f_distance, Fd, lw=2, color="blue", label="F(d)")
ax.plot(d_grid, expected, lw=2, color="black", label="Expected")
ax.set_xlim(0, 2000)
ax.set_ylim(0, 1.02)
ax.set_xlabel("Distance")
ax.set_ylabel("F(d) or G(d)")
ax.legend();
```

### K function

```{code-cell} python
k_distance = np.arange(1, 30000, 100)
pair_d = pdist(xy)
Kd = np.array([np.sum(pair_d < d) for d in k_distance], dtype=float) / (len(k_distance) * dens)

fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(k_distance, Kd, lw=2)
ax.set_xlabel("Distance")
ax.set_ylabel("K(d)");
```

## Questions

1. *What does the VMR suggest about clustering or dispersion in this pattern?*
2. *What does the combined F/G/expected plot suggest about the pattern?*
3. *Create one random point pattern for the city with the same number of events and compare its G function to the observed one.*
4. *Run a Monte Carlo simulation to test whether the observed mean nearest-neighbor distance differs from CSR.*

## About `spatstat`

`spatstat` is an *R-only* package and is not used in this Python tutorial.
For an extended Python point-pattern workflow (including more library-based
methods), see [Point pattern analysis in Python](../analysis/8-pointpat.md).

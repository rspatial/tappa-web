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

We are using a dataset of crimes in a (US) city. Read the data.

```{code-cell} python
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tappa as pt

DATA = Path("../../data").resolve()
city  = pt.vect(str(DATA / "city.gpkg"))
crime = pt.vect(str(DATA / "crime.gpkg"))
print("city :", city.nrow(), "polygon")
print("crime:", crime.nrow(), "points")
```

A map of both datasets.

```{code-cell} python
ax = pt.plot(city, col="lightblue", legend=False, figsize=(8, 4))
pt.points(crime, ax=ax, color="red", s=4, marker="+");
```

A sorted table of the incidence of crime types.

```{code-cell} python
crime_df = pt.vectAsDF(crime)
tb = crime_df["CATEGORY"].value_counts(dropna=True).sort_values()
tb
```

Get the coordinates of the crime data, removing duplicate locations.

```{code-cell} python
xy = pt.crds(crime)
print("all crimes:", xy.shape)
xy = np.unique(xy, axis=0)
print("unique:", xy.shape)
xy[:5]
```

## Basic statistics

Compute the *mean centre* and *standard distance*.

```{code-cell} python
mc = xy.mean(axis=0)
sd = float(np.sqrt(((xy - mc) ** 2).sum() / xy.shape[0]))
mc, round(sd, 2)
```

Plot the data, with a "summary circle" of radius `sd` around the
mean centre.

```{code-cell} python
bearing = np.linspace(0, 2 * np.pi, 360)
circle = np.column_stack([mc[0] + sd * np.cos(bearing),
                          mc[1] + sd * np.sin(bearing)])

ax = pt.plot(city, col="lightblue", legend=False, figsize=(8, 4))
ax.scatter(xy[:, 0], xy[:, 1], color="black", s=2)
ax.scatter(*mc, color="red", marker="*", s=300)
ax.plot(circle[:, 0], circle[:, 1], color="red", lw=2);
```

## Density

A basic point density.

```{code-cell} python
city_area = pt.expanse(city)[0]
dens = xy.shape[0] / city_area
print(f"city area:  {city_area:.0f} (sq map units)")
print(f"density:    {dens:.4g} points / unit²")
```

**Question 1a**: *What is the unit of `dens`?*

**Question 1b**: *What is the number of crimes per square km?*

### Quadrat counts

Make a quadrat grid (1000-unit cells).

```{code-cell} python
r = pt.rast(city, resolution=1000)
r = pt.rasterize(city, r)
ax = pt.plot(r, figsize=(8, 4), legend=False)
pt.points(crime, ax=ax, color="red", s=4);
```

Number of events per quadrat (using `rasterize` with `fun="count"`):

```{code-cell} python
nc = pt.rasterize(crime, r, fun="count", background=0)
ncrimes = pt.mask(nc, r)
ax = pt.plot(ncrimes, figsize=(8, 4))
pt.lines(city, ax=ax);
```

Frequency table of cell counts.

```{code-cell} python
vals = pt.values(ncrimes, mat=False)
vals = vals[~np.isnan(vals)].astype(int)
freq = pd.Series(vals).value_counts().sort_index()
freq.head()
```

```{code-cell} python
fig, ax = plt.subplots(figsize=(5, 3.5))
ax.scatter(freq.index, freq.values, s=20)
ax.set_xlabel("count per quadrat"); ax.set_ylabel("# quadrats");
```

Mean number of cases per quadrat.

```{code-cell} python
mu = vals.mean()
mu
```

Variance and variance-to-mean ratio.

```{code-cell} python
s2  = vals.var(ddof=1)
VMR = s2 / mu
print(f"s²  = {s2:.3f}")
print(f"VMR = {VMR:.3f}")
```

**Question 2**: *What does this VMR score tell us about the point
pattern?*

## Distance-based measures

Pairwise distances between points.

```{code-cell} python
from scipy.spatial.distance import pdist, squareform

dm = squareform(pdist(xy))
np.fill_diagonal(dm, np.nan)
dm[:5, :5].round(1)
```

Minimum distance from each point to its nearest neighbour.

```{code-cell} python
dmin = np.nanmin(dm, axis=1)
dmin[:6].round(2)
```

Mean nearest-neighbour distance.

```{code-cell} python
dmin.mean()
```

For each point, find *which* point is its nearest neighbour.

```{code-cell} python
wdmin = np.nanargmin(np.where(np.isnan(dm), np.inf, dm), axis=1)
wdmin[:6]
```

Plot the 25 most isolated cases together with their nearest
neighbour.

```{code-cell} python
ord_ = np.argsort(dmin)[::-1]
far25 = ord_[:25]
neighbours = wdmin[far25]

ax = pt.plot(city, col="lightblue", legend=False, figsize=(8, 4))
ax.scatter(xy[:, 0], xy[:, 1], s=2, color="black")
ax.scatter(xy[far25, 0],     xy[far25, 1],     color="blue", s=30)
ax.scatter(xy[neighbours, 0], xy[neighbours, 1],
           facecolors="none", edgecolors="red", s=40)
for i, j in zip(far25, neighbours):
    ax.plot([xy[i, 0], xy[j, 0]], [xy[i, 1], xy[j, 1]],
            color="red", lw=0.7);
```

### G function

```{code-cell} python
distance = np.sort(np.unique(np.round(dmin)))
Gd = np.array([np.sum(dmin < d) for d in distance]) / len(dmin)

fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
axes[0].plot(distance, Gd, lw=2)
axes[0].set_title("G(d)")
axes[1].plot(distance, Gd, lw=2)
axes[1].set_xlim(0, 500)
axes[1].set_title("G(d)  — first 500 m");
```

### F function

The *F* function is computed from raster cell centres.

```{code-cell} python
from scipy.spatial.distance import cdist

p_xy = pt.crds(pt.asPoints(r))
d2 = cdist(p_xy, xy)
mind = d2.min(axis=1)

Fdist = np.sort(np.unique(np.round(mind)))
Fd = np.array([np.sum(mind < d) for d in Fdist]) / len(mind)

fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(Fdist, Fd, lw=2)
ax.set_xlim(0, 3000)
ax.set_xlabel("d"); ax.set_ylabel("F(d)");
```

Expected (Poisson) distribution.

```{code-cell} python
def ef(d, lam):
    return 1 - np.exp(-1 * lam * np.pi * d ** 2)


d_grid   = np.arange(2001)
expected = ef(d_grid, dens)
```

Combined plot.

```{code-cell} python
fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(distance, Gd, color="red",  lw=2, label="G(d)")
ax.plot(Fdist,    Fd, color="blue", lw=2, label="F(d)")
ax.plot(d_grid, expected, color="black", lw=2, label="expected")
ax.set_xlim(0, 2000); ax.set_ylim(0, 1.1)
ax.set_xlabel("Distance"); ax.set_ylabel("F(d) or G(d)")
ax.legend();
```

**Question 3**: *What does this plot suggest about the point
pattern?*

### K function

```{code-cell} python
distance = np.arange(1, 30_000, 100)
d_lower  = squareform(np.nan_to_num(dm, nan=0))
Kd = np.array([np.sum(d_lower < d) for d in distance]) / \
     (len(distance) * dens)

fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(distance, Kd, lw=2);
```

**Question 4**: *Generate a single random pattern of events for the
city, with the same number of events as the crime data, and compare
its G function with that of the observed data.*

## Kernel density estimation

`scipy.stats.gaussian_kde` can be used to estimate a smooth density
surface — the Python equivalent of `density(ppp)` in `spatstat`.

```{code-cell} python
from scipy.stats import gaussian_kde

xy_all = pt.crds(crime)
kde = gaussian_kde(xy_all.T)

ext = pt.ext(city).vector
xs = np.linspace(ext[0], ext[1], 200)
ys = np.linspace(ext[2], ext[3], 200)
X, Y = np.meshgrid(xs, ys)
Z = kde(np.vstack([X.ravel(), Y.ravel()])).reshape(X.shape)

fig, ax = plt.subplots(figsize=(8, 4))
im = ax.imshow(Z, origin="lower",
               extent=(ext[0], ext[1], ext[2], ext[3]),
               cmap="viridis")
pt.lines(city, ax=ax, color="white", lw=1)
fig.colorbar(im, ax=ax, label="density");
```

The integral of the density over the area should approximately match
the number of points.

```{code-cell} python
dx = (ext[1] - ext[0]) / X.shape[1]
dy = (ext[3] - ext[2]) / Y.shape[0]
print("∑z·Δa =", round(Z.sum() * dx * dy, 1),
      "  n_pts =", xy_all.shape[0])
```

## Crime by category

Maps with the city limits and the incidence of *Auto Theft*,
*Drunk in Public*, *DUI*, and *Arson*.

```{code-cell} python
fig, axes = plt.subplots(2, 2, figsize=(10, 7))
cat_arr = crime_df["CATEGORY"].to_numpy()
for ax_, off in zip(axes.flat,
                    ["Auto Theft", "Drunk in Public", "DUI", "Arson"]):
    pt.plot(city, col="gray", legend=False, ax=ax_)
    mask = (cat_arr == off)
    if mask.any():
        sub = crime[mask]
        pt.points(sub, ax=ax_, color="red", s=8)
    ax_.set_title(off)
plt.tight_layout()
```

**Question 5**: *Why is population density a good predictor of being
booked for "drunk in public" but maybe not for "arson"?*

## PySAL / pointpats

Above we used home-brew functions. In research you would normally use a
dedicated point-pattern library. In Python that role is filled by
`pointpats` (part of PySAL), which is the closest analogue to R's
`spatstat`.

```{code-cell} python
try:
    import geopandas as gpd
    from pointpats import PointPattern, Khat, kde
except ImportError:
    print("Install pointpats and geopandas to run this section")
```

Build a `PointPattern` from the crime coordinates, using the city polygon
as the study window:

```{code-cell} python
:tags: [pp20]
if "PointPattern" in globals():
    city_gdf = gpd.read_file(DATA / "city.gpkg")
    xy_all = pt.crds(crime)
    pp = PointPattern(xy_all, hull=city_gdf.geometry.unary_union)
    pp
```

Kernel density of all crimes:

```{code-cell} python
:tags: [pp21]
if "PointPattern" in globals():
    kde_surf = kde(pp)
    fig, ax = plt.subplots(figsize=(8, 4))
    kde_surf.plot(ax=ax, cmap="viridis")
    pt.lines(city, ax=ax, color="white", lw=1);
```

Split the pattern by crime category and compare densities:

```{code-cell} python
:tags: [pp27]
if "PointPattern" in globals():
    cats = crime_df["CATEGORY"].unique()[:4]
    fig, axes = plt.subplots(2, 2, figsize=(9, 7))
    for ax_, cat in zip(axes.flat, cats):
        sub_xy = pt.crds(crime[crime_df["CATEGORY"] == cat])
        sub_pp = PointPattern(sub_xy, hull=city_gdf.geometry.iloc[0])
        kde(sub_pp).plot(ax=ax_, cmap="magma")
        pt.lines(city, ax=ax_, color="white", lw=0.8)
        ax_.set_title(cat)
    plt.tight_layout();
```

Estimate K functions for two offence types and compare them:

```{code-cell} python
:tags: [pp29]
if "PointPattern" in globals():
    def _pp_for(cat):
        mask = crime_df["CATEGORY"] == cat
        sub_xy = pt.crds(crime[mask.to_numpy()])
        return PointPattern(sub_xy, hull=city_gdf.geometry.unary_union)

    theft_pp = _pp_for("Auto Theft")
    arson_pp = _pp_for("Arson")
    k_theft = Khat(theft_pp, intervals=30)
    k_arson = Khat(arson_pp, intervals=30)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    k_theft.plot(ax=axes[0], title="Auto Theft")
    k_arson.plot(ax=axes[1], title="Arson");
```

**Question 6**: *Compare the K plots for "Auto Theft" and "Arson". What
do they suggest about spatial clustering?*

**Question 7**: *Why might population density be a good predictor of
"drunk in public" but not for "arson"?*

## Further reading

The `pointpats` Python package (part of PySAL) offers a more complete
implementation of the spatstat-style functions, including K-cross,
Kolmogorov-Smirnov tests against a covariate, and Monte-Carlo
envelopes. See the [PySAL documentation](https://pysal.org/) for
details.

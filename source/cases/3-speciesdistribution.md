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

# Analyzing species distribution data

## Introduction

In this case study we show some techniques that can be used to analyze species
distribution data with *tappa*. Before going through this document you should at
least be somewhat familiar with *Python* and
[spatial data manipulation](../spatial/index). This document is based on an
analysis of the distribution of wild potato species by Hijmans and Spooner (2001).
Wild potatoes (Solanaceae; *Solanum* sect. *Petota*) are relatives of the
cultivated potato. There are nearly 200 different species that occur in the
Americas.

## Import and prepare data

The data we will use is bundled with the tutorial site under `data/cases/`.

```{code-cell} python
:tags: [a1]
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pandas.plotting import scatter_matrix
import tappa as pt

DATA = Path("../../data").resolve()
CASES = DATA / "cases"
```

The extracted file is a CSV (comma-separated values). We can read it with:

```{code-cell} python
:tags: [a1b]
f = CASES / "wildpot.csv"
f.name
v = pd.read_csv(f)
v.head()
```

The coordinates in `v` are expressed in degrees, minutes, and seconds (in
separate columns). We compute longitude and latitude as single decimal numbers.

```{code-cell} python
:tags: [a3]
dms_cols = ["LongD", "LongM", "LongS", "LatD", "LatM", "LatS"]
for col in dms_cols:
    v[col] = pd.to_numeric(v[col], errors="coerce")

v["lon"] = -1 * (v["LongD"] + v["LongM"] / 60 + v["LongS"] / 3600)
v["lat"] = v["LatD"] + v["LatM"] / 60 + v["LatS"] / 3600
v.loc[v["LatH"] == "S", "lat"] *= -1
v.head()
```

Get a `SpatVector` with most of the countries of the Americas.

```{code-cell} python
:tags: [a4]
cn = pt.vect(str(CASES / "pt_countries.gpkg"))
type(cn)
```

Make a quick map.

```{code-cell} python
:tags: [a5]
fig, ax = plt.subplots(figsize=(8, 5))
pt.plot(cn, ax=ax)
ax.set_xlim(-120, -40)
ax.set_ylim(-40, 40)
pt.points(
    pt.vect(v[["lon", "lat"]].to_numpy(), crs="+proj=longlat +datum=WGS84"),
    ax=ax,
    s=4,
    color="red",
);
```

And create a `SpatVector` for the potato data.

```{code-cell} python
:tags: [a6]
sp = pt.vect(v, geom=("lon", "lat"), crs="+proj=longlat +datum=WGS84")
sp
```

## Summary statistics

We first summarise the data by country. We can use the country variable in the
data, or extract that from the countries `SpatVector`.

```{code-cell} python
:tags: [b1]
v["COUNTRY"].value_counts().head()
# note Peru and PERU
v["COUNTRY"] = v["COUNTRY"].str.upper()
v["COUNTRY"].value_counts().head()

# same fix for the SpatVector
df = pt.vect_as_df(sp).copy()
df["COUNTRY"] = df["COUNTRY"].str.upper()
sp = pt.set_values(sp, df)
```

Below we determine the country using a spatial query with `intersect`.

```{code-cell} python
:tags: [b2]
vv = pt.intersect(pt.subset(sp, cols=["COUNTRY"]), cn)
vv_df = pt.vect_as_df(vv)
# terra names intersect columns COUNTRY_1 / COUNTRY_2; rename like R names(vv)[1] <- "ptCountry"
vv_df.columns = ["ptCountry", "COUNTRY"]
vv_df.head()
vv_df["COUNTRY"].value_counts().head()
```

This table is similar to the previous one, but it is not the same. Let's find
the records that are not in the same country according to the original data and
the spatial query.

```{code-cell} python
:tags: [b3]
vv_df = pt.vect_as_df(vv)
vv_df.columns = ["ptCountry", "COUNTRY"]
vv_df.loc[vv_df["COUNTRY"].isna(), "COUNTRY"] = ""
vv_df.loc[vv_df["COUNTRY"] == "UNITED STATES, THE", "COUNTRY"] = "UNITED STATES"
vv_df.loc[vv_df["COUNTRY"] == "BRASIL", "COUNTRY"] = "BRAZIL"

mismatch = vv_df["ptCountry"].str.upper() != vv_df["COUNTRY"]
mismatch.sum()
vv_df.loc[mismatch].head()

fig, ax = plt.subplots(figsize=(8, 5))
pt.plot(cn, ax=ax)
ax.set_xlim(-120, -40)
ax.set_ylim(-40, 40)
pt.points(sp, ax=ax, s=2, color="blue", marker="+")
pt.points(pt.subset(vv, rows=mismatch.to_numpy().nonzero()[0].tolist()),
          ax=ax, s=64, color="red", marker="x");
```

All observations that are in a different country than their attribute data
suggests are very close to an international border, or in the water. That
suggests that the coordinates of the potato locations are not very precise (or
the borders are inexact). Otherwise, this is reassuring (and a-typical). There
are often several inconsistencies, and it can be hard to find out whether the
locality coordinates are wrong or whether the borders are wrong; but further
inspection is warranted in those cases.

We can compute the number of species for each country.

```{code-cell} python
:tags: [b4]
spc = (
    v.groupby("COUNTRY")["SPECIES"]
    .nunique()
    .reset_index(name="nspp")
)

cn_df = pt.vect_as_df(cn).copy()
cn_df.loc[cn_df["COUNTRY"] == "UNITED STATES, THE", "COUNTRY"] = "UNITED STATES"
cn_df.loc[cn_df["COUNTRY"] == "BRASIL", "COUNTRY"] = "BRAZIL"
cn = pt.set_values(cn, cn_df)

cns = pt.merge(cn, spc, on="COUNTRY", how="left")
fig, ax = plt.subplots(figsize=(8, 5))
pt.plot(
    cns,
    y="nspp",
    ax=ax,
    breaks=[1, 5, 10, 20, 30, 40, 90],
    col="terrain_r",
    na_color="lightgray",
);
```

The map shows that Peru is the country with most potato species, followed by
Bolivia and Mexico. We can also tabulate the number of occurrences of each
species by each country.

```{code-cell} python
:tags: [b5]
tb = pd.crosstab(v["COUNTRY"], v["SPECIES"])
tb.shape
tb.iloc[:5, 1:3]
```

Because the countries have such different sizes and shapes, the comparison is
not fair (larger countries will have more species, on average, than smaller
countries). Some countries are also very large, hiding spatial variation. To map
species richness it is in most cases better to use a raster (grid) with cells of
equal area, and that is what we will do next.

## Projecting spatial data

To use a raster with equal-area cells, the data need to be projected to an
equal-area coordinate reference system (CRS). If the longitude/latitude data were
used, cells of say 1 square degree would get smaller as you move away from the
equator.

For small areas, particularly if they only span a few degrees of longitude, UTM
can be a good CRS, but in this case we will use a CRS that can be used for a
complete hemisphere: Lambert Equal Area Azimuthal. For this CRS you must choose
a map origin for your data. This should be somewhere in the center of the points,
to minimize distortion. In this case, a reasonable location is (-80, 0).

```{code-cell} python
:tags: [c1]
laea = "+proj=laea +lat_0=0 +lon_0=-80"
clb = pt.project(cn, laea)
pts = pt.project(sp, laea)

fig, ax = plt.subplots(figsize=(8, 5))
pt.plot(clb, ax=ax)
pt.points(pts, ax=ax, s=4, color="red");
```

Note that the shape of the countries is now much more similar to their shape on
a globe than before we projected. The axis numbers express the distance from the
origin (-80, 0) in metres.

## Species richness

Let's determine the distribution of species richness using a raster. First we
need an empty template raster with the correct extent and resolution. Here we
use 200 by 200 km cells.

```{code-cell} python
:tags: [d1]
r = pt.rast(clb, resolution=200_000)
r
```

The *R* tutorial passes a custom function to `rasterize()` to count *unique*
species per cell. *tappa* rasterize currently supports named summary functions
(`count`, `mean`, …) via the C++ core; for unique species we bin points by
cell in Python.

```{code-cell} python
def rasterize_nunique(x, template, field):
    """Count unique non-NA values of *field* per raster cell."""
    xy = pt.crds(x)
    cells = pt.cell_from_xy(template, xy)
    values = pt.vect_as_df(x)[field].to_numpy()
    out = np.full(pt.ncell(template), np.nan)
    groups = defaultdict(set)
    for cell, val in zip(cells, values):
        if np.isnan(cell) or pd.isna(val):
            continue
        groups[int(cell)].add(val)
    for cell, uniq in groups.items():
        out[cell] = len(uniq)
    return pt.set_values(template.deepcopy(), out)
```

Now compute species richness and the number of observations for each cell.

```{code-cell} python
:tags: [d2]
rich = rasterize_nunique(pts, r, "SPECIES")
fig, ax = plt.subplots(figsize=(8, 5))
pt.plot(rich, ax=ax)
pt.lines(clb, ax=ax, color="black", linewidth=0.5);
```

```{code-cell} python
:tags: [d3]
obs = pt.rasterize(pts, r, field="SPECIES", fun="count")
fig, ax = plt.subplots(figsize=(8, 5))
pt.plot(obs, ax=ax)
pt.lines(clb, ax=ax, color="black", linewidth=0.5);
```

A cell-by-cell comparison of the number of species and the number of
observations.

```{code-cell} python
:tags: [d3b]
o = pt.values(obs).ravel()
ri = pt.values(rich).ravel()
mask = ~np.isnan(o) & ~np.isnan(ri)
fig, ax = plt.subplots(figsize=(6, 6))
ax.scatter(o[mask], ri[mask], s=20, alpha=0.7)
ax.set_xlabel("Observations")
ax.set_ylabel("Richness");
```

Clearly there is an association between the number of observations and the
number of species. It may be that the number of species in some places is
inflated just because more research was done there.

The problem is that this association will almost always exist. When there are
only few species in an area, researchers will not continue to go there to
increase the number of (redundant) observations. However, in this case, the
relationship is not as strong as it can be, and there is a clear pattern in
species richness maps; it is not characterised by sudden random-like changes in
richness (it looks like there is spatial autocorrelation, which is a good
thing). Ways to correct for this collector bias include rarefaction and richness
estimators.

There are often gradients of species richness over latitude and altitude. Here is
a plot of the latitudinal gradient in species richness.

```{code-cell} python
:tags: [d4]
d = v[["lat", "SPECIES"]].copy()
d["lat"] = d["lat"].round()
g = d.groupby("lat")["SPECIES"].nunique()
xs = g.index.to_numpy(dtype=float)
ys = g.to_numpy(dtype=float)
smooth = pd.Series(ys, index=xs).rolling(3, center=True, min_periods=1).mean()

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(xs, ys, "o", color="steelblue")
ax.plot(xs, smooth.to_numpy(), color="darkred", linewidth=2)
ax.set_xlabel("Latitude")
ax.set_ylabel("Species richness");
```

**Question:** The distribution of species richness has two peaks. What would
explain the low species richness between -5 and 15 degrees?

## Range size

Let's estimate range sizes of the species. Hijmans and Spooner use two ways:
(1) maxD, the maximum distance between any pair of points for a species, and
(2) CA50, the total area covered by circles of 50 km around each occurrence.
Here we also add the convex hull. We use the projected coordinates.

```{code-cell} python
:tags: [f2]
spp = pt.vect_as_df(pts)["SPECIES"].unique()
maxD = np.full(len(spp), np.nan)

for s, species in enumerate(spp):
    rows = pt.vect_as_df(pts)["SPECIES"] == species
    p = pt.subset(pts, rows=rows.to_numpy().nonzero()[0].tolist())
    if pt.nrow(p) < 2:
        continue
    d = pt.distance(p)
    np.fill_diagonal(d, np.nan)
    maxD[s] = np.nanmax(d)

fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(np.sort(maxD[~np.isnan(maxD)])[::-1] / 1000)
ax.set_ylabel("maxD (km)");
```

Compute CA50 (area covered by 50 km buffers, standardised to one circle).

```{code-cell} python
:tags: [f3]
CA = np.full(len(spp), np.nan)
for s, species in enumerate(spp):
    rows = pt.vect_as_df(pts)["SPECIES"] == species
    p = pt.subset(pts, rows=rows.to_numpy().nonzero()[0].tolist())
    m = pt.aggregate(pt.buffer(p, 50_000))
    CA[s] = pt.expanse(m)[0]

CA = CA / (np.pi * 50_000**2)
fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(np.sort(CA[~np.isnan(CA)])[::-1])
ax.set_ylabel("CA50");
```

Make convex hull range polygons.

```{code-cell} python
:tags: [f4]
hull = [None] * len(spp)
for s, species in enumerate(spp):
    rows = pt.vect_as_df(pts)["SPECIES"] == species
    p = pt.subset(pts, rows=rows.to_numpy().nonzero()[0].tolist())
    if pt.nrow(p) <= 3:
        continue
    h = pt.hull(p, type="convex")
    if pt.geomtype(h)[0] == "polygons":
        hull[s] = h
```

Plot the hulls and compute their areas.

```{code-cell} python
:tags: [f4b]
h = [h for h in hull if h is not None]
hh = pt.merge(h)
fig, ax = plt.subplots(figsize=(8, 5))
pt.plot(hh, ax=ax);
```

```{code-cell} python
:tags: [f4c]
ahull = pt.expanse(hh)
fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(np.sort(ahull)[::-1] / 1000)
ax.set_ylabel("Area of convex hull (km²)");
```

```{code-cell} python
cHull = np.full(len(spp), np.nan)
valid = [i for i, h in enumerate(hull) if h is not None]
cHull[valid] = ahull
```

Compare all three measures.

```{code-cell} python
:tags: [f5]
d = pd.DataFrame({"maxD": maxD, "CA": CA, "cHull": cHull})
scatter_matrix(d.dropna(), figsize=(8, 8), diagonal="hist", alpha=0.6);
```

## Exercises

### Exercise 1. Mapping species richness at different resolutions

Make maps of the number of observations and of species richness at 50, 100,
250, and 500 km resolution. Discuss the differences.

### Exercise 2. Mapping diversity

Make a map of Shannon Diversity *H* for the potato data, at 200 km resolution.

a) First make a function that computes Shannon Diversity (H) from a vector of
species names:

$$H = -\sum p \ln(p)$$

where `p` is the proportion of each species.

b) Use the function with the `rasterize_nunique` pattern above, replacing
`len(uniq)` with your Shannon function applied to the species in each cell.

### Exercise 3. Mapping traits

There is information about two traits in the data set in fields `PLRV1` /
`PLRV2` (tolerance to Potato Leaf Roll Virus) and `FROST` (frost tolerance).
Make a map of average frost tolerance.

## References

Hijmans, R.J., and D.M. Spooner, 2001. Geographic distribution of wild potato
species. *American Journal of Botany* 88:2101–2112.

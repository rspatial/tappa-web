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

# Scale and distance

## Introduction

Scale, aggregation, and distance are two key concepts in spatial data
analysis that can be difficult to come to grips with. This chapter
first discusses scale and related concepts (resolution, aggregation,
and zonation). The second part discusses distance and adjacency.

## Scale and resolution

The term "scale" is tricky. In its narrow geographic sense it is the
ratio of a distance on a (paper) map to the actual distance. So if a
distance of 1 cm on map "A" represents 100 m in the real world, the
map scale is 1/10,000 (1:10,000 or 10⁻⁴). If 1 cm on map "B"
represents 10 km in the real world, the scale of that map is
1/1,000,000. The first map "A" would have a relatively large scale
(and high resolution) compared to the second map "B", which would have
a small scale (and low resolution). It follows that if "A" and "B"
were the same physical size, "B" would represent a much larger area
(would have a much larger "spatial extent"). For that reason, most
people would refer to "B" as having a "larger scale". That is
technically wrong, but there is not much point in fighting it, and it
is simply best to avoid the term "scale", and certainly "small scale"
and "large scale", because that technically means the opposite of what
most people think. *If* you want to use these terms, you should
probably use them how they are commonly understood; unless you are
among cartographers, of course.

Now that mapping has become a computer-based activity, scale is even
more treacherous. You can use the same data to make maps of different
sizes. These would all have a different scale. With digital data we
are more interested in the *inherent* or *measurement* scale of the
data. This is sometimes referred to as "grain" but here we use
"(spatial) resolution". For raster data the notion of resolution is
straightforward: it is the size of the cells. For vector data
resolution is not as well defined and can vary largely within a data
set, but you can think of it as the average distance between the
nodes (coordinate pairs) of the lines or polygons. Point data do not
have a resolution, unless cases that are within a certain distance of
each other are merged into a single point.

In the digital world it is easy to create a "false resolution", either
by dividing raster cells into smaller cells, or by adding nodes
between nodes of polygons. Imagine polygons with soils data for a
country, where each polygon covers, on average, an area of 100 × 100
= 10,000 km². You can transfer the soil properties associated with
each polygon (e.g. pH) to a 1 km² raster, and then claim a 1 km²
spatial-resolution soils map. So we need to distinguish the resolution
of the *representation* (the data) and the resolution of the
*measurements*. The lower of the two is the one that matters.

Why does scale/resolution matter?

First, different processes have different spatial and temporal scales
at which they operate ([Levin, 1992](http://www.esa.org/history/Awards/papers/Levin_SA_MA.pdf))
— in this context, "scale" refers both to extent and resolution.
Processes that operate over a larger extent (a forest) can be studied
at a larger resolution (trees), whereas processes operating over a
smaller extent (a tree) may need to be studied at the level of leaves.

From a practical perspective: resolution affects our estimates of
length and size. If you wanted to know the length of the coastline of
Britain, you could use a digital coastline data set. The higher the
resolution, the longer the coastline would appear to be. This is not
just a problem of representation; theoretically the length of a
coastline is not defined, as it becomes infinite as resolution
approaches zero (this is illustrated [here](http://rspatial.org/cases/2-coastline.html)).

Resolution also affects our understanding of relationships between
variables. We want data at the highest spatial (and temporal)
resolution possible. We can *aggregate* to lower resolutions, but it
is not nearly as easy — or even impossible — to correctly
*disaggregate* ("downscale") to a higher resolution.

## Zonation

Geographic data are often aggregated by zones. While we would like
data at the most granular meaningful level (individuals, households,
plots), reality is that we often only get aggregated data: mean values
for a census district rather than individual incomes; counts for a
country, province, or set of raster cells.

The areas used to aggregate data are arbitrary (relative to the data
of interest). The way the borders are drawn (how large, what shape,
where) can strongly affect the patterns we see and the outcome of any
analysis. This is sometimes called the *Modifiable Areal Unit
Problem* (MAUP). The problem of analyzing aggregated data is referred
to as *Ecological Inference*.

To illustrate the effect of zonation and aggregation, we create a
region with 1000 households. For each household we know where they
live and what their annual income is, then aggregate the data to a set
of zones.

```{code-cell} python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tappa as pt

rng = np.random.default_rng(0)
xy = np.column_stack([rng.uniform(0, 100, 1000),
                      rng.uniform(0, 100, 1000)])
income = (rng.uniform(size=1000)
          * np.abs((xy[:, 0] - 50) * (xy[:, 1] - 50))) / 500
```

Inspect the data, both spatially and non-spatially. The first two
plots show that there are many poor people and a few rich people. The
third shows that there is a clear spatial pattern in where the rich
and poor live.

```{code-cell} python
fig, axes = plt.subplots(1, 3, figsize=(11, 3.5))
axes[0].scatter(np.arange(1000), np.sort(income), s=4)
axes[0].set_ylabel("income")
axes[1].hist(income, bins=np.arange(0, 5.01, 0.5))
axes[1].set_xlim(0, 5)
axes[2].scatter(xy[:, 0], xy[:, 1], s=2 + 8 * income, alpha=0.6)
axes[2].set_xlim(0, 100); axes[2].set_ylim(0, 100)
axes[2].set_aspect("equal")
fig.tight_layout();
```

Income inequality is often expressed with the
[Gini coefficient](https://en.wikipedia.org/wiki/Gini_coefficient).

```{code-cell} python
n = income.size
G = (2 * np.sum(np.sort(income) * np.arange(1, n + 1)) / income.sum()
     - (n + 1)) / n
G
```

For our data set the Gini coefficient is about 0.58.

Now assume that the household data was grouped by some kind of census
districts. We create different districts (in our case rectangular
raster cells) and compute the mean income for each district.

```{code-cell} python
v = pt.vect(xy)
v["income"] = income

grids = []
for nc, nr in [(1, 4), (4, 1), (2, 2), (3, 3), (5, 5), (10, 10)]:
    g = pt.rast(xmin=0, xmax=100, ymin=0, ymax=100, ncols=nc, nrows=nr)
    grids.append(pt.rasterize(v, g, field="income", fun="mean"))
r1, r2, r3, r4, r5, r6 = grids
```

Have a look at the plots of the income distribution and the
sub-regional averages.

```{code-cell} python
fig, axes = plt.subplots(2, 3, figsize=(10, 6))
for ax, r, title in zip(axes.ravel(), [r1, r2, r3, r4, r5, r6],
                        ["1×4", "4×1", "2×2", "3×3", "5×5", "10×10"]):
    pt.plot(r, ax=ax, legend=False)
    ax.set_title(title)
fig.tight_layout();
```

It is not surprising that the smaller the regions get, the better the
real pattern is captured. But in all cases the histograms show that we
do not capture the full income distribution.

```{code-cell} python
fig, axes = plt.subplots(1, 3, figsize=(11, 3.5))
for ax, r, title in zip(axes, [r4, r5, r6], ["3×3", "5×5", "10×10"]):
    vals = pt.values(r).ravel()
    vals = vals[~np.isnan(vals)]
    ax.hist(vals, bins=np.arange(0, 5.01, 0.5))
    ax.set_xlim(0, 5)
    ax.set_title(title)
fig.tight_layout();
```

## Distance

Distance is a numerical description of how far apart things are. It
is the most fundamental concept in geography. Waldo Tobler's First
Law of Geography states that "everything is related to everything
else, but near things are more related than distant things". But how
far away are things? Of course we can compute distance "as the crow
flies", but that is often not relevant. You may need to consider
national borders, mountains, or other barriers. The distance between
A and B may even be asymmetric (e.g. when going faster downhill than
uphill).

### Distance matrix

Distances are often described in a *distance matrix*, which holds the
distance between every pair of objects of interest. If the distance
is symmetric, only half the matrix needs to be filled.

Set up a small set of points using x-y coordinates:

```{code-cell} python
labels = ["A", "B", "C", "D", "E", "F"]
pts = np.array([
    [40, 43],
    [101, 1],
    [111, 54],
    [104, 65],
    [60, 22],
    [20, 2],
], dtype=float)
pts
```

Plot the points and labels:

```{code-cell} python
fig, ax = plt.subplots(figsize=(5, 5))
ax.scatter(pts[:, 0], pts[:, 1], color="red", s=60)
for (x, y), lab in zip(pts, labels):
    ax.text(x + 5, y + 5, lab)
ax.set_xlim(0, 120); ax.set_ylim(0, 120)
ax.set_xlabel("X"); ax.set_ylabel("Y");
```

Use `scipy.spatial.distance.pdist` to compute the planar distance
matrix and `squareform` to expand it.

```{code-cell} python
from scipy.spatial.distance import pdist, squareform

dis = pdist(pts)              # condensed (upper-triangular) form
D = squareform(dis)           # full n × n matrix
np.set_printoptions(precision=2, suppress=True)
pd.DataFrame(D, index=labels, columns=labels).round(2)
```

We can check the first off-diagonal value with Pythagoras' theorem:

```{code-cell} python
np.sqrt((40 - 101) ** 2 + (43 - 1) ** 2)
```

Distance matrices are used in many non-geographical applications. For
example, they are commonly used to build cluster diagrams (dendrograms).

```{code-cell} python
from scipy.cluster.hierarchy import linkage, dendrogram

Z = linkage(dis, method="complete")
fig, ax = plt.subplots(figsize=(6, 3.5))
dendrogram(Z, labels=labels, ax=ax);
```

### Distance for longitude/latitude coordinates

Now consider that the values in `pts` were coordinates in degrees
(longitude / latitude). Then the Cartesian distance computed by
`pdist` would be incorrect. In that case we use `tappa`'s
`distanceXY`, which knows about geographic coordinates.

```{code-cell} python
gdis = pt.distance_xy(pts, lonlat=True)
gdis = squareform(gdis) if gdis.ndim == 1 else gdis
pd.DataFrame(gdis, index=labels, columns=labels).round(0)
```

The unit of the values is **metres** (the default for
`distanceXY` with `lonlat=True`).

## Spatial influence

An important step in spatial statistics and modelling is to get a
measure of the spatial influence between geographic objects. This can
be expressed as a function of adjacency or (inverse) distance and is
often summarized as a *spatial weights matrix*. Influence is of course
very complex and cannot really be measured directly; it can be
estimated in many ways. For example the influence between a set of
polygons (countries) can be expressed as having a shared border or
not (being adjacent), as the "crow-fly" distance between their
centroids, or as the length of a shared border, and in other ways.

### Adjacency

Adjacency is an important concept in some spatial analyses. In some
cases objects are considered adjacent when they "touch" (e.g.
neighbouring countries); in others adjacency is based on distance.
Distance-based adjacency is the most common approach for point data.

We create an adjacency matrix for the point data analysed above.
Define points as "adjacent" if they are within a distance of 50 from
each other. Given the distance matrix `D` this is easy:

```{code-cell} python
a = D < 50
pd.DataFrame(a, index=labels, columns=labels)
```

In adjacency matrices the diagonal values are often set to `NA` (we
do not consider a point to be adjacent to itself), and the
`True / False` values are commonly stored as `1 / 0`:

```{code-cell} python
Adj50 = a.astype(float)
np.fill_diagonal(Adj50, np.nan)
pd.DataFrame(Adj50, index=labels, columns=labels)
```

### Two nearest neighbours

What if you wanted to compute the "two nearest neighbours" (or three,
or four) adjacency matrix? For each row, sort the column indices by
the values in that row.

```{code-cell} python
cols = np.argsort(D, axis=1)
cols
```

Then take columns 1 and 2 (column 0 would be each point's distance to
itself):

```{code-cell} python
cols23 = cols[:, 1:3]
pd.DataFrame(cols23, index=labels, columns=["k1", "k2"])
```

Build the row/column index pairs and use them to flip on the
appropriate entries in `Ak3`.

```{code-cell} python
Ak3 = np.zeros_like(Adj50)
np.fill_diagonal(Ak3, np.nan)
rows = np.repeat(np.arange(6), 2)
Ak3[rows, cols23.ravel()] = 1
pd.DataFrame(Ak3, index=labels, columns=labels)
```

### Weights matrix

Rather than expressing spatial influence as a binary value, it is
often expressed as a continuous value. The simplest approach is
inverse distance (the further away, the lower the value).

```{code-cell} python
with np.errstate(divide="ignore"):
    W = 1 / D
pd.DataFrame(W, index=labels, columns=labels).round(4)
```

Such a "spatial weights" matrix is often *row-normalised* so that the
sum of the weights in each row is 1. First we replace the `inf`
entries on the diagonal with `NaN` (where do they come from?):

```{code-cell} python
W[~np.isfinite(W)] = np.nan
```

Compute the row sums.

```{code-cell} python
rtot = np.nansum(W, axis=1)
rtot
```

Divide each row by its total and check that the row sums add up to 1.

```{code-cell} python
W = W / rtot[:, None]
np.nansum(W, axis=1)
```

The values in the columns do *not* add up to 1.

```{code-cell} python
np.nansum(W, axis=0)
```

### Spatial influence for polygons

Above we looked at adjacency for a set of points. Now we look at it
for polygons.

```{code-cell} python
from pathlib import Path
DATA = Path("../../data").resolve()
p = pt.vect(str(DATA / "lux.shp"))
```

We create a "rook's case" neighbours matrix.

```{code-cell} python
wr = pt.adjacent(p, "rook", pairs=False)
wr.shape
```

```{code-cell} python
pd.DataFrame(wr.astype(int)).iloc[:6, :11]
```

Compute the number of neighbours for each area.

```{code-cell} python
i = wr.sum(axis=1)
i
```

Expressed as a percentage:

```{code-cell} python
counts = pd.Series(i).value_counts().sort_index()
(100 * counts / counts.sum()).round(1)
```

Plot the links between the polygons.

```{code-cell} python
nb = pt.adjacent(p, "rook", pairs=True, symmetrical=True)
v = pt.centroids(p)
xy_c = pt.crds(v)

fig, ax = plt.subplots(figsize=(6, 5))
pt.plot(p, col="lightgray", border="white", legend=False, ax=ax)
for k in range(nb.shape[0]):
    a, b = nb[k]
    ax.plot([xy_c[a, 0], xy_c[b, 0]],
            [xy_c[a, 1], xy_c[b, 1]],
            color="red", lw=2);
```

Now some alternative approaches to compute "spatial influence".

Distance-based:

```{code-cell} python
wd10 = pt.nearby(v, distance=10_000)
wd25 = pt.nearby(v, distance=25_000)
```

Nearest neighbours:

```{code-cell} python
k3 = pt.nearby(v, k=3)
k6 = pt.nearby(v, k=6)
```

Plot a few of them. The neighbour pairs are returned as 0-based
feature indices. For the *k*-nearest mode we ask `pt.nearby` to
return pairs directly.

```{code-cell} python
k3_pairs = pt.nearby(v, k=3, pairs=True)

fig, axes = plt.subplots(1, 3, figsize=(12, 4))
for ax, pairs, title in zip(axes,
                            [nb, wd25, k3_pairs],
                            ["adjacency", "25 km", "k=3"]):
    pt.plot(p, col="lightgray", border="white", legend=False, ax=ax)
    for a, b in pairs:
        ax.plot([xy_c[a, 0], xy_c[b, 0]],
                [xy_c[a, 1], xy_c[b, 1]],
                color="red", lw=2)
    ax.set_title(f"({title})")
    ax.set_xticks([]); ax.set_yticks([])
fig.tight_layout();
```

```{admonition} TODO
:class: warning

Raster-based distance metrics (cost distance and resistance distance,
the equivalents of R `terra::costDist` and graph-based resistance
calculations) are not yet covered here. The plain `distance` for
SpatRaster is available via `pt.distance()`.
```

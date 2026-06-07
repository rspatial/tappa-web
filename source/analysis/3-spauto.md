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

## Introduction

Spatial autocorrelation is an important concept in spatial statistics.
It is both a *nuisance*, as it complicates statistical tests, and a
*feature*, as it allows for spatial interpolation. Its computation and
properties are often misunderstood. This chapter discusses what it
is, and how statistics describing it can be computed.

Autocorrelation (whether spatial or not) is a measure of similarity
(correlation) between nearby observations. To understand spatial
autocorrelation, it helps to first consider temporal autocorrelation.

### Temporal autocorrelation

If you measure something about the same object over time — for example
a person's weight or wealth — it is likely that two observations close
in time are also similar in measurement. Say that over a couple of
years your weight went from 50 to 80 kg. It is unlikely it was 60 kg
one day, 50 kg the next, and 80 the day after that. Rather it
probably went up gradually, with the occasional tapering off, or even
a reverse in direction. The same may be true for your bank account,
but that may also have a marked monthly trend. To measure the degree
of association over time, we can compute the correlation of each
observation with the next observation.

Let `d` be a vector of daily observations.

```{code-cell} python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

rng = np.random.default_rng(0)
d = rng.choice(np.arange(1, 101), size=10, replace=False)
d
```

Compute the auto-correlation.

```{code-cell} python
a = d[:-1]
b = d[1:]
fig, ax = plt.subplots(figsize=(4, 4))
ax.scatter(a, b, s=40)
ax.set_xlabel("t"); ax.set_ylabel("t-1");
```

```{code-cell} python
np.corrcoef(a, b)[0, 1]
```

The autocorrelation computed above is small. Even though this is a
random sample, you (almost) never get a value of zero. We computed
the *one-lag* autocorrelation — that is, we compared each value to its
immediate neighbour, and not to other nearby values.

After sorting the numbers in `d`, autocorrelation becomes very strong
(unsurprisingly).

```{code-cell} python
d.sort()
d
```

```{code-cell} python
a = d[:-1]
b = d[1:]
fig, ax = plt.subplots(figsize=(4, 4))
ax.scatter(a, b, s=40)
ax.set_xlabel("t"); ax.set_ylabel("t-1");
np.corrcoef(a, b)[0, 1]
```

The auto-correlation function (ACF) shows the autocorrelation
[computed in a slightly different
way](http://stats.stackexchange.com/questions/10947/formula-for-autocorrelation-in-r-vs-excel)
for several lags. It is 1 at lag 0 (each point is identical to
itself), very high when comparing with the nearest neighbour, and
then tapers off.

```{code-cell} python
def acf(x, n_lags=None):
    x = np.asarray(x, dtype=float)
    n = x.size
    if n_lags is None:
        n_lags = n - 1
    xm = x - x.mean()
    var0 = (xm ** 2).sum()
    return np.array([(xm[:n - k] * xm[k:]).sum() / var0
                     for k in range(n_lags + 1)])


lags = np.arange(d.size)
fig, ax = plt.subplots(figsize=(5, 3.5))
ax.vlines(lags, 0, acf(d))
ax.axhline(0, color="black", lw=0.5)
ax.set_xlabel("Lag"); ax.set_ylabel("ACF");
```

### Spatial autocorrelation

The concept of *spatial* autocorrelation is an extension of temporal
autocorrelation. It is a bit more complicated though: time is
one-dimensional and only goes in one direction (ever forward). Spatial
objects have (at least) two dimensions and complex shapes, and it may
not be obvious what counts as "near".

Measures of spatial autocorrelation describe the degree to which
observations (values) at spatial locations (points, polygons, or
raster cells) are similar to each other. So we need two things:
**observations** and **locations**.

Spatial autocorrelation in a variable can be *exogenous* (caused by
another spatially autocorrelated variable, e.g. rainfall) or
*endogenous* (caused by the process at play, e.g. the spread of a
disease).

A commonly used statistic that describes spatial autocorrelation is
*Moran's I*; we'll discuss it here in detail. Other indices include
*Geary's C* and, for binary data, the *join-count* index. The
semi-variogram also expresses the amount of spatial autocorrelation
in a data set (see the chapter on interpolation).

## Example data

Read the example data.

```{code-cell} python
from pathlib import Path
import tappa as pt

DATA = Path("../../data").resolve()

p = pt.vect(str(DATA / "lux.shp"))
p = p[p["NAME_1"] == "Diekirch"]
p["value"] = np.array([10, 6, 4, 11, 6])
pt.vect_as_df(p)
```

Let's say we are interested in spatial autocorrelation in the
`value` variable. If there were spatial autocorrelation, regions of
similar values would be spatially clustered.

Here is a plot of the polygons. We use `pt.centroids` to place the
labels.

```{code-cell} python
ax = pt.plot(p, col=["#ff5050", "#ffaa00", "#ffff66",
                     "#aaff66", "#66cc66"], legend=False, figsize=(5, 4))
v = pt.centroids(p)
pt.points(v, ax=ax, color="white", s=300)
pt.text(p, "ID_2", ax=ax, cex=1.2);
```

## Adjacent polygons

Now we need to determine which polygons are "near", and how to
quantify that. Here we use *adjacency* as the criterion.

```{code-cell} python
w = pt.adjacent(p, type="rook", pairs=True, symmetrical=True)
print("type:", type(w).__name__, "shape:", w.shape)
w
```

Each row of `w` is a pair of feature indices (0-based) that share at
least one edge. The matrix tells us something about the
neighbourhood: the average number of neighbours is
`2 * len(w) / nrow(p)`.

```{code-cell} python
n_edges = len(w)
print(f"average neighbours: {2 * n_edges / p.nrow():.2f}")
```

**Question 1**: *Explain the meaning of the values returned by `w`.*

Plot the links between the polygons.

```{code-cell} python
xy = pt.crds(v)

fig, ax = plt.subplots(figsize=(5, 4))
pt.plot(p, col="lightgray", border="blue", linewidth=2,
        legend=False, ax=ax)
for a, b in w:
    ax.plot([xy[a, 0], xy[b, 0]], [xy[a, 1], xy[b, 1]],
            color="red", lw=2);
```

We can also make a spatial weights matrix, reflecting the intensity
of the geographic relationship between observations (see previous
chapter).

```{code-cell} python
wm = pt.adjacent(p, type="rook", pairs=False).astype(int)
pd.DataFrame(wm, index=range(1, 6), columns=range(1, 6))
```

## Compute Moran's *I*

Moran's index of spatial autocorrelation is

\[
I = \frac{n}{\sum_{i=1}^n (y_i - \bar{y})^2} \,
    \frac{\sum_{i=1}^n \sum_{j=1}^n w_{ij} (y_i - \bar{y})(y_j - \bar{y})}
         {\sum_{i=1}^n \sum_{j=1}^n w_{ij}}
\]

It looks impressive, but it is not much more than an expanded form
of the formula for the correlation coefficient. The main thing that
was added is the spatial weights matrix.

The number of observations:

```{code-cell} python
n = p.nrow()
n
```

Get `y` and `ybar` (the mean of `y`).

```{code-cell} python
y = p["value"].astype(float)
ybar = y.mean()
ybar
```

Now we need

\[
(y_i - \bar{y})(y_j - \bar{y})
\]

for every pair `(i, j)`. We do this in a single broadcast.

```{code-cell} python
dy = y - ybar
pm = np.outer(dy, dy)
pm.round(2)
```

Multiply this matrix with the weights to zero out non-adjacent pairs.

```{code-cell} python
pmw = pm * wm
pd.DataFrame(pmw, index=range(1, 6), columns=range(1, 6)).round(2)
```

Sum the values to obtain
\[\sum_{i=1}^n \sum_{j=1}^n w_{ij}(y_i - \bar{y})(y_j - \bar{y})\]:

```{code-cell} python
spmw = pmw.sum()
spmw
```

Divide by the total of the weights:

```{code-cell} python
smw = wm.sum()
sw = spmw / smw
```

Compute the inverse variance of `y`:

```{code-cell} python
vr = n / np.sum(dy ** 2)
```

The final step:

```{code-cell} python
MI = vr * sw
MI
```

This is a simple (but crude) way to estimate the expected value of
Moran's *I* — the value you would get in the absence of spatial
autocorrelation (if the data were spatially random). The expected
value approaches zero for large *n*, but is not quite zero for small
*n*.

```{code-cell} python
EI = -1 / (n - 1)
EI
```

After doing it "by hand", let's use `tappa.autocor` to compute
Moran's *I* and run a significance test. We first build a queen-style
spatial weights matrix.

```{code-cell} python
ww = pt.adjacent(p, type="queen", pairs=False).astype(int)
ww
```

Now use the `autocor` function (numeric overload).

```{code-cell} python
ac = pt.autocor(y, ww, method="moran")
ac
```

We can test for significance using a Monte Carlo simulation — the
preferred method (in fact, the only good method here). The values
are repeatedly assigned at random to the polygons and Moran's *I* is
computed each time. The observed value is then compared with the
simulated distribution to see how likely it would be under random
assignment.

```{code-cell} python
rng = np.random.default_rng(0)
n_sim = 99
m = np.array([
    pt.autocor(rng.permutation(y), ww, method="moran")
    for _ in range(n_sim)
])
fig, ax = plt.subplots(figsize=(5, 3.5))
ax.hist(m, bins=12, edgecolor="black");
```

```{code-cell} python
pval = (m >= ac).sum() / (n_sim + 1)
pval
```

**Question 2**: *How do you interpret these results (the significance
tests)?*

We can make a *Moran scatter plot* to visualise spatial
autocorrelation. We first compute the average neighbour value for
each location.

```{code-cell} python
neigh_sum   = wm @ y
neigh_count = wm.sum(axis=1)
lagged_y    = neigh_sum / neigh_count

ams = pd.DataFrame({"y": y, "spatially lagged y": lagged_y})
ams
```

Finally, the plot.

```{code-cell} python
slope, intercept = np.polyfit(ams["y"], ams["spatially lagged y"], 1)

fig, ax = plt.subplots(figsize=(5, 4))
ax.scatter(ams["y"], ams["spatially lagged y"], s=80, color="red")
xs = np.linspace(ams["y"].min(), ams["y"].max(), 50)
ax.plot(xs, slope * xs + intercept, lw=2)
ax.axhline(ams["spatially lagged y"].mean(), ls="--", color="black")
ax.axvline(ybar, ls="--", color="black")
ax.set_xlabel("y"); ax.set_ylabel("spatially lagged y");
```

The slope of the regression line:

```{code-cell} python
slope
```

has a similar magnitude as Moran's *I*.

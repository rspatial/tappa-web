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

# The length of a coastline

*How Long Is the Coast of Britain? Statistical Self-Similarity and Fractional
Dimension* is the title of a [famous paper](https://classes.soe.ucsc.edu/ams214/Winter09/foundingpapers/Mandelbrot1967.pdf)
by [Benoît Mandelbrot](https://en.wikipedia.org/wiki/Benoit_Mandelbrot).
Mandelbrot uses data from a paper by
[Lewis Fry Richardson](https://en.wikipedia.org/wiki/Lewis_Fry_Richardson) who
showed that the length of a coastline changes with scale, or, more precisely,
with the length (resolution) of the measuring stick (ruler) used. Mandelbrot
discusses the fractal dimension *D* of such lines. *D* is 1 for a straight
line, and higher for more wrinkled shapes. For the west coast of Britain,
Mandelbrot reports that *D* = 1.25. Here we show how to measure the length of a
coast line with rulers of different length and how to compute a fractal
dimension.

## United Kingdom coastline

First we get a high spatial resolution coastline for the United Kingdom from the
[GADM](http://www.gadm.org) database (the same source used by the *R*
`geodata::world()` function in the original tutorial).

```{code-cell} python
:tags: [frac1]
from pathlib import Path
import urllib.request
import zipfile

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import tappa as pt

DATA = Path("../../data").resolve()
CASES = DATA / "cases"
CASES.mkdir(parents=True, exist_ok=True)

gpkg = CASES / "gadm36_GBR.gpkg"
if not gpkg.exists():
    zip_path = CASES / "gadm36_GBR_gpkg.zip"
    url = "https://geodata.ucdavis.edu/gadm/gadm3.6/gpkg/gadm36_GBR_gpkg.zip"
    print("Downloading UK GADM data …")
    urllib.request.urlretrieve(url, zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(CASES)
    zip_path.unlink(missing_ok=True)
    print("Done.")

uk = pt.vect(str(gpkg), layer="gadm36_GBR_0")
pt.plot(uk);
```

This is a single multi-polygon (one feature) in a longitude/latitude coordinate
reference system.

```{code-cell} python
pt.vect_as_df(uk)
```

## Project to British National Grid

Transform the coordinates to a planar coordinate system. That is not required,
but it speeds up distance computations. We use the
[British National Grid](https://spatialreference.org/ref/epsg/osgb-1936-british-national-grid/)
(EPSG:27700), a Transverse Mercator projection with units in metres.

```{code-cell} python
prj = "epsg:27700"
guk = pt.project(uk, prj)
```

We only want the main island, so we separate (disaggregate) the different
polygons.

```{code-cell} python
duk = pt.disagg(guk)
pt.vect_as_df(duk).head()
```

Now we have hundreds of parts. We want the largest one.

```{code-cell} python
a = pt.expanse(duk)
i = int(np.argmax(a))
a[i] / 1_000_000
b = pt.subset(duk, rows=[i])
```

Britain has an area of about 220,000 km².

```{code-cell} python
:tags: [frac5]
fig, ax = plt.subplots(figsize=(6, 8))
pt.plot(b, ax=ax)
ax.set_axis_off();
```

## Measuring with a ruler

The function below walks around the coast with a ruler (yardstick) of a certain
length. It is a direct port of the *R* function in the original tutorial.

```{code-cell} python
from tappa.distance import distancePoints


def measure_with_ruler(pols, stick_length):
    """Return coordinates where a ruler of *stick_length* (m) touches the coast."""
    if pt.nrow(pols) != 1:
        raise ValueError("measure_with_ruler expects a single polygon")

    g = pt.geom(pols)
    g = g[~np.isnan(g[:, 2])][:, 2:4]  # x, y columns
    nr = len(g)

    pts = [0]
    newpt = 0
    while True:
        p = newpt
        j = (np.arange(p, p + nr) % nr)
        gg = g[j]
        pd = distancePoints(gg[0:1], gg, lonlat=False).ravel()
        past = np.where(pd > stick_length)[0]
        if past.size == 0:
            raise RuntimeError("Ruler is longer than the maximum distance found")
        newpt = int(past[0] + p)
        if newpt >= nr:
            break
        pts.append(newpt)
    pts.append(0)
    return g[pts]
```

Now we call it several times with rulers of different lengths (this can take a
minute or two to run).

```{code-cell} python
y = []
rulers = [25, 50, 100, 150, 200, 250]  # km
for stick in rulers:
    y.append(measure_with_ruler(b, stick * 1000))
```

Object `y` is a list of coordinate arrays containing the locations where each
ruler touched the coast. We plot them on top of the map of Britain.

```{code-cell} python
:tags: [frac15]
fig, axes = plt.subplots(2, 3, figsize=(10, 12))
for ax, pts, stick in zip(axes.ravel(), y, rulers):
    pt.plot(b, ax=ax, facecolor="lightgray", edgecolor="gray", linewidth=2)
    pt.lines(
        pt.vect(pts, crs=pt.crs(b)),
        ax=ax,
        color="red",
        linewidth=3,
    )
    pt.points(
        pt.vect(pts, crs=pt.crs(b)),
        ax=ax,
        color="blue",
        s=64,
    )
    bar_y = [900_000, 900_000 - stick * 1000]
    ax.plot([525_000, 525_000], bar_y, color="black", linewidth=2)
    ax.scatter([525_000, 525_000], bar_y, s=30, color="black", zorder=5)
    ax.text(525_000, np.mean(bar_y), f"{stick} km", ha="center", fontsize=12)
    ax.text(525_000, bar_y[1] - 50_000, f"({len(pts)})", ha="center", fontsize=10)
    ax.set_axis_off()
fig.tight_layout();
```

*The coastline of Britain, measured with rulers of different lengths. The number
of segments is in parentheses.*

## Fractal dimension

Here is the fractal (log-log) plot. The axes use a log scale, but tick labels
show the untransformed values.

```{code-cell} python
:tags: [frac20]
n = [len(pts) for pts in y]
log_r = np.log(rulers)
log_n = np.log(n)
slope, intercept, *_ = stats.linregress(log_r, log_n)

fig, ax = plt.subplots(figsize=(6, 6))
tics = np.array([1, 10, 25, 50, 100, 200, 400])
ax.plot(log_r, log_n, "o", color="red", markersize=10, zorder=3)
ax.plot(log_r, intercept + slope * log_r, color="lightblue", linewidth=3)
ax.set_xlim(np.log(2), np.log(600))
ax.set_ylim(np.log(2), np.log(600))
ax.set_xticks(np.log(tics))
ax.set_xticklabels(tics)
ax.set_yticks(np.log(tics))
ax.set_yticklabels(tics)
ax.set_xlabel("Ruler length (km)")
ax.set_ylabel("Number of segments")
ax.set_xscale("linear")
ax.set_yscale("linear");
```

What does this mean? With very small rulers, from 1 mm to 10 m:

```{code-cell} python
:tags: [fracplot]
small_rulers = [1e-6, 1e-5, 1e-4, 1e-3, 1e-2]  # km
n_pred = np.exp(intercept + slope * np.log(small_rulers))
coast = n_pred * small_rulers

fig, ax = plt.subplots(figsize=(6, 6))
ax.scatter(small_rulers, coast, color="red", s=60)
ax.set_xlabel("Length of ruler")
ax.set_ylabel("Length of coast")
ax.set_xscale("log")
ax.set_yscale("log");
```

As the ruler gets smaller, the coastline gets exponentially longer. As the
ruler approaches zero, the length of the coastline approaches infinity.

The fractal dimension *D* of the coast of Britain is the absolute value of the
slope of the regression line.

```{code-cell} python
print(f"slope = {slope:.4f}")
print(f"fractal dimension D = {-slope:.4f}")
```

Not too far away from Mandelbrot's *D* = 1.25 for the west coast of Britain.

[Further reading](http://www.wahl.org/fe/HTML_version/link/FE4W/c4.htm).

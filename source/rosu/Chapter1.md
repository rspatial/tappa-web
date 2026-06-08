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

This page accompanies Chapter 1 of
[O'Sullivan and Unwin (2010)](https://www.wiley.com/en-us/Geographic+Information+Analysis%2C+2nd+Edition-p-9780470288573).
There is only one numerical example in this chapter, and it is a complicated
one. We reproduce it here anyway — perhaps you can revisit it when you reach
the end of the book (and you will be amazed to see how much you have learned!).

On page 13 the fractal dimension of a part of the New Zealand coastline is
computed. First we get a high-resolution coastline.

```{code-cell} python
:tags: [nzfrac1]
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import tappa as pt
from tappa.distance import distancePoints

DATA = Path("../../data").resolve()
ROSU = DATA / "rosu"

coast = pt.vect(str(ROSU / "nz_coastline.gpkg"))
coast
```

```{code-cell} python
pt.plot(coast, figsize=(6, 8));
```

To speed up distance computations, we transform the CRS from longitude/latitude
to a planar system.

```{code-cell} python
:tags: [crs]
prj = ("+proj=tmerc +lat_0=0 +lon_0=173 +k=0.9996 "
       "+x_0=1600000 +y_0=10000000 +datum=WGS84 +units=m")
mcoast = pt.project(coast, prj)
mcoast
```

## Yardstick function

Argument `x` is an `n × 2` array of x and y coordinates along the coastline.

```{code-cell} python
:tags: [yardfun]
def stickpoints(x, sticklength_km):
    """Indices along *x* where a yardstick of *sticklength_km* touches the coast."""
    sticklength = sticklength_km * 1000.0
    pts = [0]
    offset = 0
    while True:
        pd = distancePoints(x[0:1], x, lonlat=False).ravel()
        past = np.where(pd > sticklength)[0]
        if past.size == 0:
            break
        i = int(past[0])
        offset += i + 1
        pts.append(offset)
        x = x[i + 1:]
        if len(x) < 2:
            break
    return pts
```

Get the x and y coordinates of the line vertices. We reverse the order (to start
at the top rather than at the bottom, as in the *R* example).

```{code-cell} python
:tags: [computen]
g = pt.as_points(mcoast)
xy = pt.geom(g)[:, 2:4]
xy = xy[::-1]

sticks = [50, 25, 10]  # km
y = [stickpoints(xy, s) for s in sticks]
n = [len(idx) for idx in y]
```

Plot the first three panels (Figure 1.1).

```{code-cell} python
:tags: [fracplot1]
fig, axes = plt.subplots(1, 3, figsize=(12, 5))
for ax, stops, stick, count in zip(axes, y, sticks, n):
    pt.plot(mcoast, ax=ax, col="gray")
    pts = xy[stops]
    pt.points(pt.vect(pts, crs=pt.crs(mcoast)), ax=ax, col="red", s=30)
    pt.lines(pt.vect(pts, crs=pt.crs(mcoast)), ax=ax, col="red", lwd=3)
    ax.text(1.715e6, 5.86e6, f"{count} x {stick} = {count * stick} km", fontsize=11)
    ax.set_axis_off()
fig.tight_layout();
```

The fractal (log-log) plot:

```{code-cell} python
:tags: [fracplot2]
fig, ax = plt.subplots(figsize=(6, 6))
ax.scatter(sticks, n, c="red", s=80)
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("stick length")
ax.set_ylabel("number of measures")

slope, intercept, *_ = stats.linregress(np.log(sticks), np.log(n))
xfit = np.array(sticks, dtype=float)
ax.plot(xfit, np.exp(intercept + slope * np.log(xfit)), color="blue", lw=2)
ax.text(6, 220, f"log N = {slope:.3f} log L + {intercept:.3f}")
```

The fractal dimension *D* is the (absolute value of the) slope of the regression
line:

```{code-cell} python
D = -slope
D
```

Pretty close to the 1.44 that OSU found.

**Question 1**: *Compare the results in OSU and computed here for the three
yardsticks. How and why are they different?*

For a more detailed example on the coastline of Britain, see the
[Coastline length](../cases/2-coastline) case study.

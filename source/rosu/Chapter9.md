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

# Fields

## Introduction

This handout accompanies Chapter 9 in
[O'Sullivan and Unwin (2010)](http://www.wiley.com/WileyCDA/WileyTitle/productCd-0470288574.html).

Continuous function from page 246:

```{code-cell} python
def z(x, y):
    return -12 * x**3 + 10 * x**2 * y - 14 * x * y**2 + 25 * y**3 + 50

z(0.5, 0.8)
```

Build a small raster and evaluate the function on every cell:

```{code-cell} python
:tags: [fields5]
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import tappa as pt

r = pt.rast(xmin=0.5, xmax=1.4, ymin=0.6, ymax=1.5, ncol=9, nrow=9, crs="")
xy = pt.xy_from_cell(r, np.arange(pt.ncell(r)))
vals = z(xy[:, 0], xy[:, 1])
zr = pt.set_values(pt.subset(r, [0]), vals.reshape(r.nrow(), r.ncol(), order="F"))
pt.set_names(zr, ["z"])
```

```{code-cell} python
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

fig = plt.figure(figsize=(6, 5))
ax = fig.add_subplot(111, projection="3d")
X, Y = np.meshgrid(np.linspace(0.5, 1.4, 9), np.linspace(0.6, 1.5, 9))
Z = pt.as_matrix(zr)
ax.plot_surface(X, Y, Z, cmap="viridis")
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.set_zlabel("z");
```

## California precipitation

We use the same station data as the spatial analysis tutorials.

```{code-cell} python
:tags: [fields10]
import pandas as pd

DATA = Path("../../data").resolve()
d = pd.read_csv(DATA / "precipitation.csv")
d.head()
```

```{code-cell} python
mnts = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
        "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
d["prec"] = d[mnts].sum(axis=1)

fig, ax = plt.subplots(figsize=(5, 3))
ax.plot(np.sort(d["prec"]), marker="o", lw=0)
ax.set_xlabel("Stations")
ax.set_ylabel("Annual precipitation (mm)");
```

```{code-cell} python
:tags: [fields15]
dsp = pt.vect(d, geom=("LONG", "LAT"), crs="+proj=longlat +datum=NAD83")
CA = pt.vect(str(DATA / "counties.gpkg"))

ax = pt.plot(CA, col="lightgray", lwd=2, border="white", legend=False, figsize=(7, 6))
pt.plot(dsp, "prec", ax=ax, breaks=[0, 200, 300, 500, 1000, 3000],
        col=["yellow", "orange", "blue", "darkblue"], cex=1.5)
pt.lines(CA, ax=ax);
```

Interpolation of these station data is covered in the
[Interpolation](../analysis/4-interpolation) chapter.

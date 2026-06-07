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

# Raster data

## Introduction

The *tappa* package has functions for creating, reading, manipulating and
writing raster data. The package provides, among other things, general raster
data manipulation functions that can easily be used to develop more specific
functions. For example, there are functions to read a chunk of raster values
from a file or to convert cell numbers to coordinates and back. The package
also implements raster algebra and many other functions for raster data
manipulation.

## SpatRaster

A `SpatRaster` represents multi-layer (multi-variable) raster data. A
`SpatRaster` always stores a number of fundamental parameters describing its
geometry. These include the number of columns and rows, the spatial extent and
the coordinate reference system. In addition, a `SpatRaster` can store
information about the file in which the raster cell values are stored. Or, if
there is no such file, a `SpatRaster` can hold the cell values in memory.

Here we create a `SpatRaster` from scratch. Note that in most cases where real
data is analysed, these objects are created from a file.

```{code-cell} python
import numpy as np
import tappa as pt

r = pt.rast(ncols=10, nrows=10, xmin=-150, xmax=-80, ymin=20, ymax=60)
r
```

`SpatRaster` `r` only has the geometry of a raster data set. That is, it knows
about its location, resolution, etc., but there are no values associated with
it. Let's assign some values. In this case we assign a vector of random
numbers with a length that is equal to the number of raster cells.

```{code-cell} python
rng = np.random.default_rng(0)
r = pt.set_values(r, rng.uniform(0, 1, pt.ncell(r)))
r
```

You could also assign cell numbers (in this case overwriting the previous
values):

```{code-cell} python
r = pt.set_values(r, np.arange(1, pt.ncell(r) + 1, dtype=float))
r
```

We can plot this object.

```{code-cell} python
:tags: [plot4-1]
import matplotlib.pyplot as plt

ax = pt.plot(r, figsize=(5, 4))

# add polygon and points
lon = np.array([-116.8, -114.2, -112.9, -111.9, -114.2, -115.4, -117.7])
lat = np.array([41.3, 42.9, 42.4, 39.8, 37.6, 38.3, 37.6])
n = lon.size
geom_arr = np.column_stack([
    np.ones(n, dtype=int),  # id
    np.ones(n, dtype=int),  # part
    lon, lat,
])
pts = pt.vect(np.column_stack([lon, lat]),
              crs="+proj=longlat +datum=WGS84")
pols = pt.vect(geom_arr, type="polygons",
               crs="+proj=longlat +datum=WGS84")

pt.points(pts,  ax=ax, col="red",  cex=2)
pt.polys(pols, ax=ax, border="blue", lwd=2);
```

You can create a multi-layer object using `pt.rast()` with a list of
`SpatRaster` objects, or with the C++ ``c`` method which is exposed in *tappa*
as `SpatRaster.c(...)` (the constructor `pt.rast([r1, r2, r3])` does the same):

```{code-cell} python
:tags: [plot4-2]
r2 = r * r
r3 = pt.sqrt(r)
s = pt.rast([r, r2, r3])
s
```

```{code-cell} python
pt.plot(s, figsize=(8, 6));
```

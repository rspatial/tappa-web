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

# Creating SpatRaster objects

A `SpatRaster` can easily be created from scratch using `pt.rast()`. The default
settings create a global raster data structure with a longitude/latitude
coordinate reference system and 1° × 1° cells. You can change these settings by
providing additional arguments such as `xmin`, `nrow`, `ncol`, and/or `crs`. You
can also change geometry after creating the object. If you set the projection,
this is only to properly define it, not to change it. To transform a
`SpatRaster` to another coordinate reference system (projection) you can use
`pt.project()`.

Here is an example of creating and changing a `SpatRaster` object `x` from
scratch.

```{code-cell} python
:tags: [raster-1a]
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import tappa as pt

DATA = Path("../../data").resolve()
rng = np.random.default_rng(0)

# SpatRaster with default geometry parameters
x = pt.rast()
x
```

With other parameters:

```{code-cell} python
:tags: [raster-1aa]
x = pt.rast(ncols=36, nrows=18, xmin=-1000, xmax=1000, ymin=-100, ymax=900)
pt.res(x)
```

Change the spatial resolution of an existing object. Many *terra* setters that
mutate in place have *tappa* equivalents that return a new raster:

```{code-cell} python
:tags: [raster-1aaa]
ext = pt.ext(x)
x = pt.rast(extent=ext, resolution=100.0)
pt.res(x)
pt.ncol(x)
```

Set the coordinate reference system (CRS) — define the projection:

```{code-cell} python
:tags: [raster-1aaab]
x.set_crs("+proj=utm +zone=48 +datum=WGS84")
x
```

The object `x` created above only consists of a "skeleton": we have defined the
number of rows and columns and where the raster is located in geographic space,
but there are no cell values associated with it. Setting and accessing values is
illustrated below.

```{code-cell} python
:tags: [raster-1b]
r = pt.rast(ncols=10, nrows=10)
pt.ncell(r), pt.has_values(r)

r = pt.set_values(r, np.arange(1, pt.ncell(r) + 1, dtype=float))
r = pt.set_values(r, rng.uniform(0, 1, pt.ncell(r)))

pt.has_values(r), pt.sources(r)
pt.values(r).ravel()[:10]

pt.plot(r, main="Raster with 100 cells", figsize=(5, 3.5));
```

In some cases, for example when you change the number of columns or rows, you
will lose the values associated with the `SpatRaster` if there were any (or the
link to a file if there was one). The same applies, in most cases, if you change
the resolution directly (as this can affect the number of rows or columns).
Values are not lost when changing the extent as this change adjusts the
resolution but does not change the number of rows or columns.

```{code-cell} python
:tags: [raster-1c]
r = pt.rast(ncols=10, nrows=10, xmin=0, xmax=10, ymin=0, ymax=10)
r = pt.set_values(r, np.arange(1, pt.ncell(r) + 1, dtype=float))
pt.has_values(r), pt.res(r), (pt.nrow(r), pt.ncol(r)), r.xmax()

# change the maximum x coordinate of the extent (bounding box)
# — resolution adjusts, nrow/ncol stay the same, values are kept
r = pt.rast(extent=pt.ext(0, 5, 0, 10), nrows=pt.nrow(r), ncols=pt.ncol(r))
r = pt.set_values(r, np.arange(1, pt.ncell(r) + 1, dtype=float))
pt.has_values(r), pt.res(r), (pt.nrow(r), pt.ncol(r))

# changing ncol loses values (rebuild geometry)
e = pt.ext(r)
r2 = pt.rast(ncols=6, nrows=pt.nrow(r), extent=e)
pt.has_values(r2), pt.res(r2), (pt.nrow(r2), pt.ncol(r2)), r2.xmax()
```

You can also create a `SpatRaster` from another object, including another
`SpatRaster`, a list of rasters, or a filename.

It is more common, however, to create a `SpatRaster` object from a file.
*tappa* can use raster files in several formats, including GeoTIFF, ESRI, ENVI,
and ERDAS Imagine. Most formats supported for reading can also be written to.

```{code-cell} python
:tags: [raster-2a]
filename = DATA / "meuse.tif"
r = pt.rast(str(filename))
pt.sources(r), pt.has_values(r)
pt.plot(r, main="SpatRaster from file", figsize=(5, 3.5));
```

Multi-layer objects can be created in memory (from `SpatRaster` objects) or from
files.

```{code-cell} python
:tags: [raster-2b]
r1 = pt.rast(nrows=10, ncols=10)
r2 = pt.rast(nrows=10, ncols=10)
r3 = pt.rast(nrows=10, ncols=10)
r1 = pt.set_values(r1, rng.uniform(0, 1, pt.ncell(r1)))
r2 = pt.set_values(r2, rng.uniform(0, 1, pt.ncell(r2)))
r3 = pt.set_values(r3, rng.uniform(0, 1, pt.ncell(r3)))
```

Combine the three `SpatRaster` objects into a single object with three layers:

```{code-cell} python
:tags: [raster-2bb]
s = pt.rast([r1, r2, r3])
s
pt.nlyr(s)
```

Create a multi-layer `SpatRaster` from file:

```{code-cell} python
:tags: [raster-2bbb]
b = pt.rast(str(DATA / "logo.tif"))
b
pt.nlyr(b)
```

Extract a layer (the second one):

```{code-cell} python
:tags: [raster-2bbbb]
r = pt.subset(b, [1])
```

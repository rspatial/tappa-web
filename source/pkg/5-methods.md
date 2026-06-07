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

# High-level methods

Several "high-level" methods (functions) have been implemented for `SpatRaster`
objects. "High level" refers to methods that you would normally find in a GIS
program that supports raster data. Here we briefly discuss some of these.

The high-level methods have some arguments in common. The first argument is
typically a `SpatRaster` (or `SpatVector`). It is followed by one or more
arguments specific to the method (either additional `SpatRaster` objects or other
arguments), followed by a `filename` argument (or `SpatOptions`) for I/O
control.

The default `filename` is empty. If you do not specify a filename, the default
action for the method is to return a `SpatRaster` that only exists in memory.
However, if the method deems that the resulting raster would be too large to hold
in memory it is written to a temporary file instead.

The `SpatOptions` object (from `pt.spat_options()`) allows for setting
additional arguments that are relevant when writing values to a file: the file
format, datatype (e.g. integer or real values), and whether existing files should
be overwritten.

## Modifying a SpatRaster object

There are several methods that deal with modifying the spatial extent of
`SpatRaster` objects. The `pt.crop()` method lets you take a geographic subset
of a larger raster. You can crop a `SpatRaster` by providing an extent object,
another `SpatRaster`, or a `SpatVector`.

`pt.trim()` crops a `SpatRaster` by removing the outer rows and columns that only
contain `NA` values. In contrast, `pt.extend()` adds new rows and/or columns
with `NA` values.

The `pt.merge()` method lets you merge 2 or more `SpatRaster` objects into a
single new object. The input objects must have the same resolution and origin.
If this is not the case you can first adjust one of the `SpatRaster` objects
with `pt.aggregate()` / `pt.aggregate_disagg()` or `pt.resample()`.

`pt.aggregate()` and `pt.aggregate_disagg()` allow for changing the resolution
(cell size) of a `SpatRaster` object. `pt.resample()` can do either nearest
neighbour assignments (for categorical data) or bilinear interpolation (for
numerical data). Simple linear shifts can be accomplished with `pt.shift()`.
With `pt.project()` you can transform values of a `SpatRaster` to a new object
with a different coordinate reference system.

```{code-cell} python
:tags: [raster-5]
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import tappa as pt

r = pt.rast(ncols=10, nrows=10, xmin=0, xmax=10, ymin=0, ymax=10)
r = pt.set_values(r, np.arange(1, pt.ncell(r) + 1, dtype=float))
ra = pt.aggregate(r, 2)
r1 = pt.crop(r, pt.ext(0, 5, 0, 5))
r2 = pt.crop(r, pt.ext(4, 10, 4, 10))
m = pt.merge([r1, r2], filename="test.tif", overwrite=True)
pt.plot(m, figsize=(6, 4));
```

```{code-cell} python
:tags: [remove-output]
from pathlib import Path
for f in Path(".").glob("test*"):
    f.unlink()
```

`pt.flip()` lets you flip the data in horizontal or vertical direction.
`pt.rotate()` lets you rotate longitude/latitude rasters that have longitudes from
0 to 360 degrees to the standard −180 to 180 degree system. With `pt.trans()`
you can rotate a `SpatRaster` object 90 degrees.

## lapp

The `pt.lapp()` (layer-apply) method can be used as an alternative to the
raster algebra discussed above. With `pt.lapp()` you can combine multiple
`SpatRaster` objects. The related method `pt.mask()` removes all values from one
layer that are `NA` in another layer, and `pt.cover()` combines two layers by
taking the values of the first layer except where these are `NA`.

## app

The `pt.app()` method allows you to do a computation across the layers of a
`SpatRaster` by providing a function (like `numpy.apply_along_axis` on a
matrix). If you supply a `SpatRaster`, another `SpatRaster` is returned.
`pt.tapp()` computes summary-type layers for subsets of a `SpatRaster` (like
`pandas.groupby` on a matrix).

## classify

You can use `pt.classify()` to replace ranges of values with single values, or
`pt.subst()` to substitute (replace) single values with other values.

```{code-cell} python
:tags: [raster-6]
r = pt.rast(ncols=3, nrows=2)
r = pt.set_values(r, np.arange(1, pt.ncell(r) + 1, dtype=float))
pt.values(r).ravel()

s = pt.app(r, lambda x: np.where(np.asarray(x, dtype=float) < 4, np.nan, x))
pt.as_matrix(s)

t = pt.lapp(pt.rast([r, s]), lambda x, y: x / (2 * np.sqrt(y)) + 5)
pt.as_matrix(t)

u = pt.mask(r, t)
pt.as_matrix(u)

v = u == s
pt.as_matrix(v)

w = pt.cover(t, r)
pt.as_matrix(w)

rcl = np.array([[0, 2, 1], [2, 5, 2], [4, 10, 3]])
x = pt.classify(w, rcl)
pt.as_matrix(x)

y = pt.subst(x, [2, 3], [40, 50])
pt.as_matrix(y)
```

## Focal

The `pt.focal()` method uses values in a neighbourhood of cells around a focal
cell, and computes a value that is stored in the focal cell of the output
`SpatRaster`. The neighbourhood is a user-defined matrix of weights and could
approximate any shape by giving some cells zero weight. It is possible to only
compute new values for cells that are `NA` in the input `SpatRaster`.

## Distance

There are a number of distance-related methods. `pt.distance()` computes the
shortest distance to cells that are not `NA`. `pt.distance_points()` computes
the shortest distance to any point in a set of points. `pt.cost_dist()` computes
the distance when following grid cells that can be traversed (e.g. excluding
water bodies). `pt.direction()` computes the direction towards (or from) the
nearest cell that is not `NA`. `pt.adjacent()` determines which cells are
adjacent to other cells.

## Spatial configuration

The `pt.patches()` method identifies groups of cells that are connected.
`pt.boundaries()` identifies edges, that is, transitions between cell values.
`pt.cellSize()` computes the size of each grid cell (for unprojected rasters);
this may be useful to, e.g., compute the area covered by a certain class on a
longitude/latitude raster.

```{code-cell} python
:tags: [raster-7]
rng = np.random.default_rng(0)
r = pt.rast(nrows=45, ncols=90)
r = pt.set_values(r, np.round(rng.uniform(0, 1, pt.ncell(r)) * 3))
a = pt.cellSize(r)
pt.zonal(a, r, "sum")
```

## Predictions

The *terra* package has `predict()` and `interpolate()` methods for model
predictions on (potentially very large) rasters. These high-level wrappers are
not yet available in *tappa*; see the [Spatial prediction](9-predict) chapter
for Python alternatives using *scikit-learn* and *SciPy*.

## Vector to raster conversion

*tappa* supports point, line, and polygon to raster conversion with
`pt.rasterize()`. For vector data, `SpatVector` objects are used; points can
also be represented by a two-column array.

It is also possible to convert the values of a `SpatRaster` to points or
polygons, using `pt.as_points()` and `pt.as_polygons()`. Both methods only
return values for cells that are not `NA`.

## Summarize

When used with a `SpatRaster` object as first argument, summary statistics
functions such as `pt.rast_min()`, `pt.rast_max()` and `pt.rast_mean()` return a
`SpatRaster`. You can use `pt.global_()` if you want a summary for all cells of
a single `SpatRaster` object. You can use `pt.freq()` to make a frequency table,
or to count the number of cells with a specified value. Use `pt.zonal()` to
summarize a `SpatRaster` object using zones defined in another `SpatRaster`, and
`pt.crosstab()` to cross-tabulate two `SpatRaster` objects.

```{code-cell} python
:tags: [raster-10]
rng = np.random.default_rng(0)
r = pt.rast(ncols=36, nrows=18)
r = pt.set_values(r, rng.uniform(0, 1, pt.ncell(r)))
pt.global_(r, "mean")

s = pt.set_values(r.deepcopy(), np.round(rng.uniform(0, 1, pt.ncell(r)) * 5))
pt.zonal(r, s, "mean")
pt.freq(s)
pt.freq(s, value=3)

both = pt.rast([r * 3, s])
pt.crosstab(both).head()
```

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

# Raster data manipulation

## Introduction

In this chapter we cover general aspects of the design of *tappa*, notably the
structure of the main classes and what they represent. The use of the package
is illustrated below. *tappa* has a large number of functions; not all of them
are discussed here, and those that are discussed are mentioned only briefly.
See `help(tappa)` and the [API reference](https://rspatial.org/tappa/api) for
more information.

## Creating SpatRaster objects

A `SpatRaster` can easily be created from scratch using `pt.rast()`. The
default settings will create a global raster data structure with a
longitude/latitude coordinate reference system and 1° × 1° cells. You can
change these settings by providing additional arguments such as `xmin`,
`nrows`, `ncols` and/or `crs`. You can also change these parameters after
creating the object. If you set the projection, this is only to properly
define it, not to change it. To transform a `SpatRaster` to another
coordinate reference system (projection) you can use `pt.project()`.

Here is an example of creating and changing a `SpatRaster` from scratch.

```{code-cell} python
:tags: [raster-1a]
import numpy as np
import tappa as pt

# SpatRaster with the default parameters
x = pt.rast()
x
```

With some other parameters:

```{code-cell} python
:tags: [raster-1b]
x = pt.rast(ncols=36, nrows=18, xmin=-1000, xmax=1000, ymin=-100, ymax=900)
x
```

Resolution:

```{code-cell} python
:tags: [raster-1c]
pt.res(x)
```

Many *terra* setters that mutate in place have *tappa* equivalents that
return a new raster. Resampling the resolution is most cleanly done by
constructing a new raster with the same extent:

```{code-cell} python
ext = pt.ext(x)
x = pt.rast(extent=ext, resolution=100.0)
pt.res(x)
```

Set the coordinate reference system (CRS), i.e. define the projection:

```{code-cell} python
:tags: [raster-1e]
x.set_crs("+proj=utm +zone=48 +datum=WGS84")
x
```

The object `x` created in the examples above only consists of the raster
*geometry*: we have defined the number of rows and columns and where the
raster is located in geographic space, but there are no cell values associated
with it. Setting and accessing values is illustrated below.

First another example empty raster geometry.

```{code-cell} python
:tags: [raster-1h]
r = pt.rast(ncols=10, nrows=10)
pt.ncell(r), pt.has_values(r)
```

Use `set_values()`:

```{code-cell} python
:tags: [raster-1i]
r = pt.set_values(r, np.arange(1, pt.ncell(r) + 1))
```

Another example.

```{code-cell} python
:tags: [raster-1j]
import matplotlib.pyplot as plt

rng = np.random.default_rng(0)
r = pt.set_values(r, rng.uniform(0, 1, pt.ncell(r)))
pt.has_values(r), pt.sources(r)
pt.values(r).ravel()[:10]
pt.plot(r, main="Raster with 100 cells", figsize=(5, 4));
```

While we can create a `SpatRaster` from scratch, it is more common to do so
from a file. *tappa* can read raster files in several formats, including
GeoTIFF, ESRI, ENVI and ERDAS Imagine.

A notable feature of *tappa* (inherited from *terra*) is that it can work
with raster datasets that are stored on disk and are too large to be loaded
into memory (RAM). The package can work with large files because the objects
it creates from these files only contain information about the structure of
the data — number of rows and columns, spatial extent, filename — and do not
attempt to read all the cell values into memory. In computations with these
objects, data is processed in chunks. If no output filename is specified to a
function, and the output raster is too large to keep in memory, the results
are written to a temporary file.

```{code-cell} python
:tags: [raster-2a1]
from pathlib import Path

DATA = Path("../../data").resolve()
filename = DATA / "elev.tif"
filename.name
```

```{code-cell} python
:tags: [raster-2a2]
r = pt.rast(str(filename))
print(pt.sources(r), pt.has_values(r))
pt.plot(r, main="SpatRaster from file", figsize=(5, 4));
```

Multi-layer objects can be created in memory or from files.

Create three identical `SpatRaster` objects:

```{code-cell} python
:tags: [raster-2b1]
r1 = pt.rast(nrows=10, ncols=10)
r2 = pt.rast(nrows=10, ncols=10)
r3 = pt.rast(nrows=10, ncols=10)
r1 = pt.set_values(r1, rng.uniform(0, 1, pt.ncell(r1)))
r2 = pt.set_values(r2, rng.uniform(0, 1, pt.ncell(r2)))
r3 = pt.set_values(r3, rng.uniform(0, 1, pt.ncell(r3)))
```

Combine three `SpatRaster`s into a multi-layer raster. Pass them as a list
to `pt.rast()` (the same constructor used for files):

```{code-cell} python
:tags: [raster-2b2]
s = pt.rast([r1, r2, r3])
pt.nlyr(s)
```

You can also create a multi-layer object from a file:

```{code-cell} python
:tags: [raster-2b5]
filename = DATA / "logo.tif"
b = pt.rast(str(filename))
print(b)
print("nlyr:", pt.nlyr(b))
```

Extract a single layer (the second one in this case):

```{code-cell} python
:tags: [raster-2b6]
r = pt.subset(b, [1])
```

## Raster algebra

Many generic operators have been registered for `SpatRaster` objects so that
raster algebra works as in *R*: `+`, `-`, `*`, `/`, comparisons (`>`, `>=`,
`<`, `==`, `!=`), and helpers like `pt.sqrt()`, `pt.log()`, `pt.rast_abs()`,
`pt.rast_min()`, `pt.rast_max()`, `pt.rast_mean()`, etc. In these
expressions you can mix `SpatRaster` objects with numbers, as long as the
first argument is a `SpatRaster`.

Create an empty `SpatRaster` and assign values to cells:

```{code-cell} python
:tags: [raster-3a1]
r = pt.rast(ncols=10, nrows=10)
r = pt.set_values(r, np.arange(1, pt.ncell(r) + 1))
```

Now some raster algebra:

```{code-cell} python
:tags: [raster-3a2]
s = r + 10
s = pt.sqrt(s)
s = s * r + 5
r = pt.set_values(r, rng.uniform(0, 1, pt.ncell(r)))
r = pt.round_(r)
r = r == 1
```

If you use multiple `SpatRaster` objects (in functions where this is
relevant, such as `pt.rast_min()`), these must have the same resolution and
origin. The origin of a raster is the point closest to (0, 0) that you could
get if you moved from a corner of the raster toward that point in steps of
the x and y resolution. Normally these objects would also have the same
extent, but if they do not, the returned object covers the spatial
intersection of the objects used.

When you use multiple multi-layer objects with different numbers of layers,
the "shorter" objects are recycled. For example, if you multiply a 4-layer
object (a1, a2, a3, a4) with a 2-layer object (b1, b2), the result is a
4-layer object (a1·b1, a2·b2, a3·b1, a4·b2).

```{code-cell} python
:tags: [raster-3c]
r = pt.rast(ncols=5, nrows=5)
r = pt.set_values(r, np.ones(pt.ncell(r)))
s = pt.rast([r, r + 1])
q = pt.rast([r, r + 2, r + 4, r + 6])
x = r + s + q
x
```

Summary functions (`pt.rast_min()`, `pt.rast_max()`, `pt.rast_mean()`,
`pt.rast_sum()`, `pt.rast_median()`, ...) always return a `SpatRaster`.

```{code-cell} python
:tags: [raster-3d]
a = pt.rast_mean(r, s, 10)
b = pt.rast_sum(r, s)
st = pt.rast([r, s, a, b])
sst = pt.rast_sum(st)
sst
```

Use `pt.global_(...)` if you want a single number summarising the cell
values of each layer.

```{code-cell} python
:tags: [raster-3e]
pt.global_(st, "sum")
```

```{code-cell} python
pt.global_(sst, "sum")
```

## High-level functions

Several "high-level" functions have been implemented for `SpatRaster`
objects. The term "high level" refers to functions that you would normally
find in a computer program that supports the analysis of raster data. Here
we briefly discuss some of these functions. All these functions work for
raster datasets that cannot be loaded into memory.

The high-level functions have some arguments in common. The first argument
is typically a `SpatRaster`, followed by one or more arguments specific to
the function (either additional `SpatRaster`s or other arguments), followed
by a `filename` argument (or `SpatOptions`) for I/O control.

The default `filename` is empty. If you do not specify a filename, the
default action is to return a `SpatRaster` that only exists in memory.
However, if the function deems that the resulting raster would be too large
to hold in memory, it is written to a temporary file instead.

### Modifying a SpatRaster object

There are several functions that deal with modifying the spatial extent of
`SpatRaster` objects.

* `pt.crop()` lets you take a geographic subset of a larger raster object.
  You can crop a `SpatRaster` by providing an extent object, another
  `SpatRaster`, or a `SpatVector`.
* `pt.trim()` crops a raster by removing the outer rows and columns that
  only contain `NA` values.
* `pt.extend()` adds new rows and/or columns with `NA` values.
* `pt.merge()` merges 2 or more `SpatRaster` objects into a single new
  one. The input objects must have the same resolution and origin.
* `pt.aggregate()` and `pt.aggregate_disagg()` allow for changing the
  resolution (cell size) of a `SpatRaster` by integer factors.
* `pt.resample()` does either nearest-neighbour assignments (for categorical
  data) or bilinear interpolation (for numerical data).
* `pt.shift()` performs simple linear shifts.
* `pt.project()` (also called `warp` in some contexts) transforms
  values to a new object with a different CRS.

Aggregate and disaggregate:

```{code-cell} python
:tags: [raster-5]
r = pt.rast()
r = pt.set_values(r, np.arange(1, pt.ncell(r) + 1))
ra = pt.aggregate(r, 20)
rd = pt.aggregate_disagg(ra, 20)
```

Crop and merge example:

```{code-cell} python
:tags: [raster-5b]
r1 = pt.crop(r, pt.ext(-50, 0, 0, 30))
r2 = pt.crop(r, pt.ext(-10, 50, -20, 10))
m = pt.merge([r1, r2], filename="test.tif", overwrite=True)
pt.plot(m, figsize=(8, 4));
```

```{code-cell} python
:tags: [remove-output]
import os
for f in Path(".").glob("test*"):
    f.unlink()
```

`pt.flip()` lets you flip the data (reverse order) in horizontal or vertical
direction — typically to correct for a "communication problem" between
different libraries or a misinterpreted file. `pt.rotate()` lets you rotate
longitude/latitude rasters that have longitudes from 0 to 360 degrees (often
used by climatologists) to the standard −180 to 180 degree system. With
`pt.trans()` you can rotate a `SpatRaster` 90 degrees.

### Overlay

`pt.app()` (short for "apply") allows you to do a computation for a single
`SpatRaster` object by providing a function, e.g. `sum`.

`pt.lapp()` (layer-apply) is an alternative to the raster algebra discussed
above.

### Classify

You can use `pt.classify()` to replace ranges of values with single values,
or to substitute (replace) single values with other values.

```{code-cell} python
:tags: [raster-6a]
r = pt.rast(ncols=3, nrows=2)
r = pt.set_values(r, np.arange(1, pt.ncell(r) + 1))
pt.values(r).ravel()
```

Set all values below 4 to `NA` using `pt.app()`:

```{code-cell} python
:tags: [raster-6b]
s = pt.app(r, lambda x: np.where(np.asarray(x, dtype=float) < 4, np.nan, x))
pt.as_matrix(s)
```

Divide the first raster with two times the square root of the second raster
and add five.

```{code-cell} python
:tags: [raster-6c]
rs = pt.rast([r, s])
w = pt.lapp(rs, lambda x, y: x / (2 * np.sqrt(y)) + 5)
pt.as_matrix(w)
```

Remove from `r` all values that are `NA` in `w`.

```{code-cell} python
:tags: [raster-6d]
u = pt.mask(r, w)
pt.as_matrix(u)
```

Identify the cell values in `u` that are the same as in `s`.

```{code-cell} python
:tags: [raster-6e]
v = u == s
pt.as_matrix(v)
```

Replace `NA` values in `w` with values of `r`.

```{code-cell} python
:tags: [raster-6f]
cvr = pt.cover(w, r)
pt.as_matrix(w)
```

Change values between 0 and 2 to 1, between 2 and 5 to 2, between 4 and 10
to 3:

```{code-cell} python
:tags: [raster-6g]
import numpy as np
rcl = np.array([[0, 2, 1], [2, 5, 2], [4, 10, 3]])
x = pt.classify(w, rcl)
pt.as_matrix(x)
```

Substitute 2 with 40 and 3 with 50:

```{code-cell} python
:tags: [raster-6h]
y = pt.subst(x, [2, 3], [40, 50])
pt.as_matrix(y)
```

### Focal methods

The `pt.focal()` method computes new values based on the values in a
neighbourhood of cells around a focal cell, and puts the result in the focal
cell of the output `SpatRaster`. The neighbourhood is a user-defined matrix
of weights and could approximate any shape by giving some cells zero weight.
It is possible to compute new values only for cells that are `NA` in the
input.

### Distance

There are a number of distance-related functions. For example, you can
compute the shortest distance to cells that are not `NA`
(`pt.distance()`), the shortest distance to any point in a set of
points (`pt.distance_points()`), or the cost-distance when traversing cells
(`pt.cost_dist()`). See the *distance* tutorials for more advanced examples.

### Spatial configuration

`pt.patches()` identifies groups of cells that are connected.
`pt.boundaries()` identifies edges, that is, transitions between cell
values. `pt.cellSize()` computes the size of each grid cell (for unprojected
rasters). This may be useful to, e.g., compute the area covered by a
certain class on a longitude/latitude raster.

```{code-cell} python
:tags: [raster-7]
r = pt.rast(nrows=45, ncols=90)
r = pt.set_values(r, np.round(rng.uniform(0, 1, pt.ncell(r)) * 3))
a = pt.cellSize(r)
pt.zonal(a, r, "sum")
```

### Predictions

*tappa* exposes raster prediction via `pt.app()` and `pt.lapp()`. Higher-level
wrappers for fitted *scikit-learn* models can be added on top: feed the
raster cell values into the model and write the predicted values back into a
new `SpatRaster`.

### Vector to raster conversion

*tappa* supports point, line and polygon to raster conversion with
`pt.rasterize()`. For vector data (points, lines, polygons), `SpatVector`
objects are used; points can also be represented by a two-column array.

It is also possible to convert the values of a `SpatRaster` to points or
polygons, using `pt.as_points()` and `pt.as_polygons()`. Both functions only
return values for cells that are not `NA`.

## Summarising functions

When used with a `SpatRaster` object as first argument, normal summary
statistics functions such as `pt.rast_min()`, `pt.rast_max()` and
`pt.rast_mean()` return a `SpatRaster`. Use `pt.global_()` if you want a
summary scalar for all cells of a single layer. Use `pt.freq()` to make a
frequency table or to count the number of cells with a specified value. Use
`pt.zonal()` to summarise a `SpatRaster` using zones (areas with the same
integer number) defined in another `SpatRaster`, and `pt.crosstab()` to
cross-tabulate two `SpatRaster` objects.

```{code-cell} python
:tags: [raster-10a]
r = pt.rast(ncols=36, nrows=18)
r = pt.set_values(r, rng.uniform(0, 1, pt.ncell(r)))
pt.global_(r, "mean")
```

Zonal stats: below `r` has the cells we want to summarise, `s` defines the
zones, and the last argument is the function to summarise the values of `r`
for each zone in `s`.

```{code-cell} python
:tags: [raster-10b]
s = pt.set_values(r.deepcopy(), np.round(rng.uniform(0, 1, pt.ncell(r)) * 5))
pt.zonal(r, s, "mean")
```

Count cells:

```{code-cell} python
:tags: [raster-10c]
pt.freq(s)
```

```{code-cell} python
pt.freq(s, value=3)
```

Cross-tabulate:

```{code-cell} python
:tags: [raster-10d]
both = pt.rast([r * 3, s])
ctb = pt.crosstab(both)
ctb.head() if hasattr(ctb, "head") else ctb[:6]
```

## Helper functions

The cell number is an important concept. Raster data can be thought of as a
matrix, but in a `SpatRaster` it is more commonly treated as a vector. Cells
are numbered from the upper-left cell to the upper-right cell and then
continuing on the left side of the next row, and so on until the last cell
at the lower-right side of the raster (1-based, like *terra*). There are
several helper functions to determine the column or row number from a cell
and vice versa, and to determine the cell number for x, y coordinates and
vice versa.

```{code-cell} python
:tags: [raster-15]
r = pt.rast(ncols=36, nrows=18)
print(pt.ncol(r), pt.nrow(r), pt.ncell(r))
print("row from cell 100:", pt.row_col_from_cell(r, [100])[0])
print("cell from row,col=5,5:", pt.cell_from_row_col(r, 5, 5))
print("xy from cell 100:", pt.xy_from_cell(r, [100]))
print("cell from xy (0,0):", pt.cell_from_xy(r, 0.0, 0.0))
print("col from x=0:", pt.col_from_x(r, 0.0))
print("row from y=0:", pt.row_from_y(r, 0.0))
```

## Accessing cell values

Cell values can be accessed with several methods. Use `pt.values()` to get
all values or a subset such as a single row or a block (rectangle) of cell
values.

```{code-cell} python
:tags: [raster-20]
r = pt.rast(str(DATA / "elev.tif"))
v = pt.values(r)
v[3075:3080]
```

You can also read values using cell numbers or coordinates (xy) using
`pt.extract()` or `pt.extract_xy()`.

```{code-cell} python
:tags: [raster-21]
cells = pt.cell_from_row_col(r, 33, list(range(35, 41)))
cells
```

You can extract values using `SpatVector` objects. The default approach for
extracting raster values with polygons is that a polygon has to cover the
centre of a cell for the cell to be included. However, you can use
`weights=True`, in which case you get, apart from the cell values, the
percentage of each cell covered by the polygon, so you can apply, e.g., a
"50% area covered" threshold or compute an area-weighted average. With
`exact=True` you get the exact fraction of each cell covered by the polygon.

In the case of lines, any cell that is crossed by a line is included. For
lines and points, a cell that is only "touched" is included when it is
below or to the right (or both) of the line segment / point (except for the
bottom row and right-most column).

## Coercion to other classes

You can convert a `SpatRaster` to a *NumPy* array (or matrix) and vice
versa, and to a *pandas* `DataFrame`:

```{code-cell} python
:tags: [raster-120]
r = pt.rast(ncols=36, nrows=18)
r = pt.set_values(r, rng.uniform(0, 1, pt.ncell(r)))
pt.as_array(r).shape
```

```{code-cell} python
pt.as_data_frame(r).head()
```

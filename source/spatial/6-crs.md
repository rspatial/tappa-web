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

# Coordinate Reference Systems

## Introduction

A very important aspect of spatial data is the coordinate reference system
(CRS) that is used. For example, a location of (140, 12) is not meaningful if
you do not know where the origin (0, 0) is and if the x-coordinate is 140
metres, feet, nautical miles, kilometres, or perhaps degrees away from the
x-origin.

## Coordinate Reference Systems (CRS)

### Angular coordinates

The earth has an irregular spheroid-like shape. The natural coordinate
reference system for geographic data is longitude/latitude. This is an
*angular* coordinate reference system. The latitude $\phi$ (phi) of a point
is the angle between the equatorial plane and the line that passes through a
point and the centre of the Earth. Longitude $\lambda$ (lambda) is the angle
from a reference meridian (lines of constant longitude) to a meridian that
passes through the point.

Obviously we cannot actually measure these angles. But we can estimate them.
To do so, you need a model of the shape of the earth. Such a model is called
a "datum". The simplest datums are a spheroid (a sphere that is "flattened"
at the poles and bulges at the equator). More complex datums allow for more
variation in the earth's shape. The most commonly used datum is called WGS84
(World Geodesic System 1984). This is very similar to NAD83 (the North
American Datum of 1983). Other, local, datums exist to more precisely record
locations for a single country or region.

So the basic way to record a location is a coordinate pair in degrees and a
reference datum. Sometimes people say that their coordinates are "in WGS84".
That does not tell us much; they typically mean to say that they are
longitude/latitude relative to the WGS84 datum. Likewise longitude/latitude
coordinates are sometimes referred to as "geographic" coordinates. That is
rather odd; if planar coordinate reference systems (see below) are not
geographic, what are they?

### Projections

A major question in spatial analysis and cartography is how to transform this
three-dimensional angular system to a two-dimensional planar (sometimes called
"Cartesian") system. A planar system is easier to use for certain calculations
and required to make maps (unless you have a 3-d printer). The different types
of planar coordinate reference systems are referred to as "projections".
Examples are *Mercator*, *UTM*, *Robinson*, *Lambert*, *Sinusoidal* and
*Albers*.

There is not one best projection. Some projections can be used for a map of
the whole world; other projections are appropriate for small areas only. One
of the most important characteristics of a map projection is whether it is
"equal area" (the scale of the map is constant) or "conformal" (the shapes
of the geographic features are as they are seen on a globe). No
two-dimensional map projection can be both conformal and equal-area (but they
can be approximately both for smaller areas, e.g. UTM, or Lambert Equal Area
for a larger area), and some are neither.

### Notation

A planar CRS is defined by a projection, datum and a set of parameters. The
parameters determine things like where the centre of the map is. The number
of parameters depends on the projection. It is therefore not trivial to
document a projection used, and several systems exist. Historically, much R
code used the
[PROJ.4](https://proj.org/en/stable/usage/projections.html#proj-4-syntax)
notation. PROJ.4 is the name of a software library that is commonly used for
CRS transformation.

Most commonly used CRSs have been assigned an "EPSG code" (EPSG stands for
European Petroleum Survey Group). This is a unique ID that can be a simple
way to identify a CRS. For example `EPSG:27561` is equivalent to a long
PROJ.4 string for the Lambert Conformal Conic projection used in northern
France. The
[`pyproj`](https://pyproj4.github.io/pyproj/stable/) package and the GDAL
library that *tappa* is built on top of both accept EPSG codes, PROJ.4
strings, or full Well-Known-Text (WKT) descriptions.

Now let's look at an example with a spatial data set in *Python*.

```{code-cell} python
from pathlib import Path
import tappa as pt

DATA = Path("../../data").resolve()
f = DATA / "lux.shp"
p = pt.vect(str(f))
p
```

We can inspect the coordinate reference system like this.

```{code-cell} python
print(pt.crs(p))
```

## Assigning a CRS

Sometimes we have data without a CRS. This can be because the file used was
incomplete, or perhaps because we created the data ourselves. In that case
we can assign the CRS *if we know what it should be*. Here we first remove
the CRS of `pp` and then set it again.

```{code-cell} python
pp = p.deepcopy()
pp.set_crs("")
print(pt.crs(pp))
pp.set_crs("+proj=longlat +datum=WGS84")
print(pt.crs(pp))
```

Note that you should *not* use this approach to change the CRS of a data set
from what it *is* to what you *want it to be*. Assigning a CRS is like
labelling something. You need to provide the label that corresponds to the
item, not what you would like it to be. For example if you label a bicycle,
you can write "bicycle". Perhaps you would prefer a car, and you can label
your bicycle as "car" but that would not do you any good. It is still a
bicycle. You can try to transform your bicycle into a car. That would not be
easy. Transforming spatial data is easier.

## Transforming vector data

We can transform these data to a new data set with another CRS using the
`project()` (also exposed as `v.project(crs)`).

Here we use the Robinson projection. First we need to find the correct
notation:

```{code-cell} python
newcrs = "+proj=robin +datum=WGS84"
```

Now use it:

```{code-cell} python
rob = pt.project(p, newcrs)
rob
```

After the transformation, the units of the geometry are no longer in degrees,
but in metres away from `(longitude=0, latitude=0)`. The spatial extent of
the data is also in these units.

We can backtransform to longitude/latitude:

```{code-cell} python
p2 = pt.project(rob, "+proj=longlat +datum=WGS84")
```

## Transforming raster data

Vector data can be transformed from lon/lat coordinates to planar and back
without loss of precision. This is not the case with raster data. A raster
consists of rectangular cells of the same size (in terms of the units of the
CRS; their actual size may vary). It is not possible to transform cell by
cell. For each new cell, values need to be estimated based on the values in
the overlapping old cells. If the values are categorical data, the "nearest
neighbour" method is commonly used. Otherwise some sort of interpolation is
employed (e.g. "bilinear").

Because projection of rasters affects the cell values, in most cases you will
want to avoid projecting raster data and rather project vector data. But here
is how you can project raster data.

```{code-cell} python
:tags: [prj1]
import numpy as np

r = pt.rast(xmin=-110, xmax=-90, ymin=40, ymax=60, ncols=40, nrows=40)
r = pt.set_values(r, np.arange(1, pt.ncell(r) + 1))
r
```

```{code-cell} python
pt.plot(r, figsize=(5, 4));
```

The simplest approach is to provide a new CRS (the Robinson CRS in this
case):

```{code-cell} python
pr1 = pt.project(r, newcrs)
print(pt.crs(pr1))
pt.plot(pr1, figsize=(5, 4));
```

But that is not a good method. You should ensure that you project to
*exactly* the raster parameters you need (so that the result lines up with
other raster data you are using).

To have this kind of control, provide an existing `SpatRaster` with the
geometry you desire. That is generally the best way to project a raster: by
providing an existing `SpatRaster`, your newly projected data perfectly
aligns with it. In this example we do not have an existing `SpatRaster`
object, so we create one from the result obtained above.

```{code-cell} python
x = pt.rast(pr1)
# set the cell size
pt.res(x)  # current resolution
```

```{code-cell} python
x = pt.rast(pr1)
res = 200000.0
# create new template by setting the resolution
x_extent = pt.ext(x)
x = pt.rast(extent=x_extent, crs=newcrs,
            ncols=int((x_extent.vector[1] - x_extent.vector[0]) / res),
            nrows=int((x_extent.vector[3] - x_extent.vector[2]) / res))
```

Now project, and note the change in the coordinates.

```{code-cell} python
:tags: [prj3]
pr3 = pt.project(r, x)
pr3
pt.plot(pr3, figsize=(5, 4));
```

For raster-based analysis it is often important to use equal-area projections,
particularly when large areas are analysed. This will ensure that the grid
cells are all of the same size, and therefore comparable to each other,
especially when count data are used.

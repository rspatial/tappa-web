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

# Spatial data

## Introduction

Spatial phenomena can generally be thought of as either discrete objects with
clear boundaries or as continuous phenomena that can be observed everywhere but
that do not have natural boundaries. Discrete spatial objects may refer to a
river, road, country, town, or a research site. Examples of continuous
phenomena, or "spatial fields", include elevation, temperature and air
quality.

Spatial objects are usually represented by *vector* data. Such data consists of
a description of the "geometry" or "shape" of the objects, and normally also
includes additional variables. For example, a vector data set may represent the
borders of the countries of the world (geometry) and also store their names and
the size of their population in 2015; or it may have the geometry of the roads
in an area, as well as their type and names. These additional variables are
often referred to as "attributes". Continuous spatial data (fields) are usually
represented with a *raster* data structure. We discuss these two data types in
turn.

## Vector data

The main vector data types are **points**, **lines** and **polygons**. In all
cases the geometry of these data structures consists of sets of coordinate
pairs (x, y). Points are the simplest case. Each point has one coordinate
pair, and *n* associated variables. For example, a point might represent a
place where a rat was trapped, and the attributes could include the date it
was captured, the person who captured it, the species, size and sex, and
information about the habitat. It is also possible to combine several points
into a multi-point structure, with a single attribute record. For example, all
the coffee shops in a town could be considered as a single geometry.

The geometry of **lines** is just a little bit more complex. First note that
in this context the term "line" refers to a set of one or more polylines
(connected series of line segments). For example, in spatial analysis a river
and all its tributaries could be considered as a single "line" (but they
could also be several lines, perhaps one for each tributary). Lines are
represented as ordered sets of coordinates (nodes). The actual line segments
can be computed (and drawn on a map) by connecting the points. Thus, the
representation of a line is very similar to that of a multi-point structure.
The main difference is that for a line the ordering of the points is
important, because we need to know in which order the points should be
connected.

A **network** (e.g. a road or river network), or spatial graph, is a special
type of lines geometry where there is additional information about things like
flow, connectivity, direction and distance.

A **polygon** refers to a set of closed polylines. The geometry is very
similar to that of lines, but to close a polygon the last coordinate pair
coincides with the first pair. A complication with polygons is that they can
have holes (a polygon entirely enclosed by another polygon, that serves to
remove parts of the enclosing polygon — for example to show an island inside a
lake). Also, valid polygons do not self-intersect (but it is OK for a line to
self-cross). Multiple polygons can be considered as a single geometry. For
example, Indonesia consists of many islands. Each island can be represented by
a single polygon, but together they can represent a single (multi-) polygon
representing the entire country.

## Raster data

Raster data is commonly used to represent spatially continuous phenomena such
as elevation. A raster divides the world into a grid of equally sized
rectangles (referred to as cells, or in the context of satellite remote
sensing as pixels) that all have one or more values (or missing values) for
the variables of interest. A raster cell value should normally represent the
average (or majority) value for the area it covers. However, in some cases the
values are estimates for the centre of the cell (in essence becoming a regular
set of points with an attribute).

In contrast to vector data, in raster data the geometry is not explicitly
stored as coordinates. It is implicitly set by knowing the spatial extent and
the number of rows and columns into which the area is divided. From the extent
and number of rows and columns the size of the raster cells (spatial
resolution) can be computed. While raster cells can be thought of as a set of
regular polygons, it would be very inefficient to represent the data that way
as the coordinates of each cell would have to be stored explicitly. Doing so
would also dramatically increase processing time.

Continuous surface data are sometimes stored as triangulated irregular networks
(TINs); these are not discussed here.

## Simple representation of spatial data

The basic data types in *Python* are numbers, strings, booleans (`True` /
`False`) and a few container types like lists, tuples and dictionaries. Numeric
arrays of a single type are represented with `numpy.ndarray`, and tabular data
with `pandas.DataFrame`. We can represent (only very) basic spatial data with
these data types. Let's say we have the location (represented by longitude and
latitude) of ten weather stations (named A to J) and their annual
precipitation.

In the example below we make a very simple map. Note that a *map* is a special
type of plot (like a scatter plot, bar plot, etc.). A map is a plot of
geospatial data that also has labels and other graphical objects such as a
scale bar or legend. The spatial data itself should not be referred to as a
map.

```{code-cell} python
import numpy as np
import matplotlib.pyplot as plt

name = list("ABCDEFGHIJ")
longitude = np.array([-116.7, -120.4, -116.7, -113.5, -115.5,
                      -120.8, -119.5, -113.7, -113.7, -110.7])
latitude = np.array([45.3, 42.6, 38.9, 42.1, 35.7, 38.9,
                     36.2, 39.0, 41.6, 36.9])
stations = np.column_stack([longitude, latitude])

# Simulated rainfall data
rng = np.random.default_rng(0)
precip = np.round((rng.uniform(0, 1, len(latitude)) * 10) ** 3).astype(int)
precip
```

A map of point locations is not that different from a basic x-y scatter plot.
Here we make a plot (a map in this case) that shows the location of the
weather stations, where the size of the dots is proportional to the amount of
precipitation.

```{code-cell} python
:tags: [spatialdata_2]
psize = 1 + precip / 500

fig, ax = plt.subplots(figsize=(6, 6))
ax.scatter(longitude, latitude, s=(psize * 60), c="red")
for x, y, lab in zip(longitude, latitude, name):
    ax.text(x + 0.1, y, lab)
ax.set_title("Precipitation")
ax.set_xlabel("longitude")
ax.set_ylabel("latitude")

# add a legend
breaks = np.array([100, 250, 500, 1000])
legend_psize = 1 + breaks / 500
for s, lab in zip(legend_psize, breaks):
    ax.scatter([], [], s=s * 60, c="red", label=str(lab))
ax.legend(title="precip", loc="upper right");
```

Note that the data are represented by "longitude, latitude", in that order;
do not use "latitude, longitude" because on most maps latitude (north/south)
is used for the vertical axis and longitude (east/west) for the horizontal
axis. This is important to keep in mind, as it is a very common source of
mistakes!

We can add multiple sets of points to the plot, and even draw lines and
polygons:

```{code-cell} python
:tags: [spatialdata_3]
lon = np.array([-116.8, -114.2, -112.9, -111.9, -114.2, -115.4, -117.7])
lat = np.array([41.3, 42.9, 42.4, 39.8, 37.6, 38.3, 37.6])
poly_xy = np.column_stack([lon, lat])

fig, ax = plt.subplots(figsize=(6, 6))
poly = plt.Polygon(poly_xy, closed=True, facecolor="blue",
                   edgecolor="lightblue")
ax.add_patch(poly)
ax.plot(longitude, latitude, color="red", linewidth=3)
ax.scatter(lon, lat, s=80, c="black")
ax.scatter(longitude, latitude, s=psize * 60, c="red")
ax.set_title("Precipitation")
ax.autoscale_view();
```

The above illustrates how plain *NumPy* arrays of coordinates can be used to
draw simple maps. It also shows how points are typically represented by pairs
of numbers, and how a line and a polygon can be represented by a sequence of
these points. Polygons need to be "closed", that is, the first point must
coincide with the last point; *Matplotlib* did that for us automatically.

There are cases where a simple approach like this may suffice, and you may
come across this in older *Python* code. Likewise, raster data could be
represented by a 2D `numpy.ndarray` or higher-rank array. Particularly when
only dealing with point data, such an approach may be practical. For example,
a spatial data set representing points and attributes could be made by
combining geometry and attributes in a single `pandas.DataFrame`:

```{code-cell} python
import pandas as pd

wst = pd.DataFrame({
    "longitude": longitude,
    "latitude": latitude,
    "name": name,
    "precip": precip,
})
wst
```

However, `wst` is just a `DataFrame`; *Python* does not automatically
understand the special meaning of the first two columns, or what coordinate
reference system they use (longitude/latitude, or perhaps UTM zone 17S, or
…?).

Moreover, it is non-trivial to do some basic spatial operations. For example,
the blue polygon drawn on the map above might represent a state, and a next
question might be which of the 10 stations fall within that polygon. And how
about any other operation on spatial data, including reading from and writing
to files? To facilitate such operations a number of *Python* packages have
been developed that define new spatial data types specialised for these
operations.

In these tutorials we use [*tappa*](https://github.com/rspatial/tappa), the
Python port of the *R* `terra` package. *tappa* re-uses the *terra* C++
core, so it preserves *terra*'s API and computational model in Python and
covers both vector (`SpatVector`) and raster (`SpatRaster`) data with one
package.

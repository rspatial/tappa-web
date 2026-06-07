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

# Vector data

## Introduction

The *tappa* package defines a set of *classes* to represent spatial data. A
class defines a particular data type. The `pandas.DataFrame` is an example of
a class. Any particular `DataFrame` you create is an *object* (instantiation)
of that class.

The main reason for defining classes is to create a standard representation of
a particular data type to make it easier to write functions (known as
"methods") for them. *tappa* introduces a number of classes with names that
start with `Spat`, mirroring the *terra* R package. For vector data, the
relevant class is `SpatVector`. These classes represent geometries as well as
attributes (variables) describing the geometries.

It is possible to create `SpatVector` objects from scratch with *Python* code.
This is very useful when creating a small self-contained example to illustrate
something — for example, to ask a question about how to do a particular
operation without needing to give access to the real data you are using
(which is always cumbersome). It is also frequently done when using
coordinates that were obtained with a GPS. But in most other cases, you will
read these from a file or database, see [Chapter 5](5-files.md) for
examples.

To get started, let's make some `SpatVector` objects from scratch anyway,
using the same data as were used in the previous chapter.

## Points

```{code-cell} python
import numpy as np
import tappa as pt

longitude = np.array([-116.7, -120.4, -116.7, -113.5, -115.5,
                      -120.8, -119.5, -113.7, -113.7, -110.7])
latitude = np.array([45.3, 42.6, 38.9, 42.1, 35.7, 38.9,
                     36.2, 39.0, 41.6, 36.9])
lonlat = np.column_stack([longitude, latitude])
```

Now create a `SpatVector` object. First make sure that *tappa* is installed
(`pip install tappa` or use a *conda* environment, see the
[tappa README](https://github.com/rspatial/tappa#readme)).

```{code-cell} python
pts = pt.vect(lonlat)
```

Let's check what kind of object `pts` is.

```{code-cell} python
type(pts)
```

And what is inside it.

```{code-cell} python
pts
```

```{code-cell} python
pt.geom(pts)[:5]
```

So we see that the object has the coordinates we supplied, but also an
`extent`. This spatial extent was computed from the coordinates. There is also
a coordinate reference system ("CRS", discussed in more detail later). We did
not provide the CRS when we created `pts`. That is not good, so let's
recreate the object, this time providing a CRS.

```{code-cell} python
crdref = "+proj=longlat +datum=WGS84"
pts = pt.vect(lonlat, crs=crdref)
pts
```

```{code-cell} python
pt.crs(pts)
```

We can add attributes (variables) to the `SpatVector` object. First we need a
`pandas.DataFrame` with the same number of rows as there are geometries.

```{code-cell} python
import pandas as pd

rng = np.random.default_rng(0)
precipvalue = rng.uniform(0, 100, lonlat.shape[0])
df = pd.DataFrame({"ID": np.arange(1, lonlat.shape[0] + 1),
                   "precip": precipvalue})
df
```

Combine the `SpatVector` with the `DataFrame` (in *tappa* this is done with
the `atts` argument of `vect`, just like in *terra*).

```{code-cell} python
ptv = pt.vect(lonlat, atts=df, crs=crdref)
ptv
```

## Lines and polygons

Making a `SpatVector` of points was easy. Making a `SpatVector` of lines or
polygons is a bit more complex but still relatively straightforward. *tappa*
expects four columns: `id`, `part`, `x`, `y` (just like *terra*).

```{code-cell} python
lon = np.array([-116.8, -114.2, -112.9, -111.9, -114.2, -115.4, -117.7])
lat = np.array([41.3, 42.9, 42.4, 39.8, 37.6, 38.3, 37.6])
n = lon.size
lonlat_lines = np.column_stack([
    np.ones(n, dtype=int),  # id
    np.ones(n, dtype=int),  # part
    lon, lat,
])
lonlat_lines
```

```{code-cell} python
lns = pt.vect(lonlat_lines, type="lines", crs=crdref)
lns
```

```{code-cell} python
pols = pt.vect(lonlat_lines, type="polygons", crs=crdref)
pols
```

Behind the scenes the class deals with the complexity of accommodating for the
possibility of multiple polygons, each consisting of multiple sub-polygons,
some of which may be "holes". You do not need to understand how these
structures are organised. The main take-home message is that a `SpatVector`
stores geometries (coordinates), the name of the coordinate reference system,
and attributes.

We can use *Matplotlib* to make a map. *tappa*'s `plot()` is raster-only,
so for vector layers we use `pt.points()`, `pt.lines()`, and `pt.polys()`
to draw onto a *Matplotlib* `Axes` (the same idiom as in *R*'s `terra`).

```{code-cell} python
:tags: [vectordata-1]
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(5, 5))
pt.polys(pols, ax=ax, col="yellow", border="blue", lwd=3)
pt.points(pts, ax=ax, col="red", cex=2);
```

We'll make more fancy maps [later](9-maps.md).

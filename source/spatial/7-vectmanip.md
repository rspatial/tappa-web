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

# Vector data manipulation

This chapter illustrates some ways in which we can manipulate vector data. We
start with an example `SpatVector` that we read from a shapefile.

```{code-cell} python
:tags: [vec1]
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tappa as pt

DATA = Path("../../data").resolve()
f = DATA / "lux.shp"
p = pt.vect(str(f))
p
```

`pt.plot()` is the entry point for both rasters and vectors. For a
`SpatVector` it picks the right painter from the geometry type and sets the
geographic aspect ratio for you. Pass `y=` to colour features by an
attribute (numeric attributes are binned into 10 equal-interval classes;
non-numeric attributes get one colour per category):

```{code-cell} python
pt.plot(p, y="NAME_2", col="rainbow", edgecolor="black", linewidth=0.5);
```

For pure overlays use `pt.points()`, `pt.lines()`, and `pt.polys()` — they
mirror the R `terra` functions of the same name and accept R-style aliases
like `col`, `border`, `lwd`, `lty`, `cex`, and `pch`.

## Basics

### Geometry and attributes

To extract the attributes (DataFrame) from a `SpatVector`, use:

```{code-cell} python
d = pt.vect_as_df(p)
d.head()
```

You can also extract the geometry as a numpy array (this is rarely needed):

```{code-cell} python
g = pt.geom(p)
g[:6]
```

Or as "well-known text":

```{code-cell} python
gw = pt.geom(p, wkt=True)
gw[0][:50]
```

### Variables

You can extract a variable as you would do with a `DataFrame`:

```{code-cell} python
d["NAME_2"].tolist()
```

To subset a `SpatVector` to one or more variables, use `subset()` (the
positional-indexing equivalent of *terra*'s `p[, "NAME_2"]`):

```{code-cell} python
p_sub = pt.subset(p, rows=None, cols=["NAME_2"])
p_sub
```

You can add a new variable to a `SpatVector` like you would with a
`DataFrame` — first pull the attribute table, modify, and assign it back:

```{code-cell} python
rng = np.random.default_rng(0)
df = pt.vect_as_df(p).copy()
df["lets"] = rng.choice(list("abcdefghijklmnopqrstuvwxyz"), size=len(df))
p = pt.set_values(p, df)
p
```

To get the number of geometries you can use ``len(p)`` or ``pt.nrow(p)``.
You can also do `pt.perim(p)` to get the "length" of the spatial objects
(zero for points, the length of the lines, or the perimeter of the polygons).

```{code-cell} python
pt.perim(p)[:5]
```

To get rid of a variable, drop it from the attribute DataFrame and reassign:

```{code-cell} python
df = pt.vect_as_df(p).drop(columns=["lets"])
p = pt.set_values(p, df)
```

### Merge

To add attributes to a `SpatVector` that already has attributes you can join
on the side of the attribute table and write it back:

```{code-cell} python
dfr = pd.DataFrame({
    "District": pt.vect_as_df(p)["NAME_1"].values,
    "Canton":   pt.vect_as_df(p)["NAME_2"].values,
    "Value":    rng.integers(100, 1001, size=len(p)),
})
dfr = dfr.sort_values("Canton").reset_index(drop=True)

merged = pt.vect_as_df(p).merge(
    dfr, left_on=["NAME_1", "NAME_2"], right_on=["District", "Canton"],
    how="left").drop(columns=["District", "Canton"])
pm = pt.deepcopy(p)
pt.set_values(pm, merged)
pm
```

### Records

Selecting rows (records).

```{code-cell} python
:tags: [recs]
mask = pt.vect_as_df(p)["NAME_1"] == "Grevenmacher"
i = np.flatnonzero(mask.to_numpy())
g = pt.subset(p, rows=i.tolist())
g
```

```{admonition} TODO
:class: warning

Interactive selection (*terra*'s `sel()` and `click()`) is not yet ported
to *tappa*. For now, use *Matplotlib* event callbacks if you need
one-off interactive selection inside a notebook.
```

## Append and aggregate

### Append

More example data. Object `z` consists of four polygons; `z2` is one of these
four polygons.

```{code-cell} python
:tags: [zzz]
z = pt.rast(p)
# 2x2 layout
z_extent = pt.ext(z).vector
z = pt.rast(xmin=z_extent[0], xmax=z_extent[1],
            ymin=z_extent[2], ymax=z_extent[3], ncols=2, nrows=2,
            crs=pt.crs(p))
z = pt.set_values(z, np.arange(1, pt.ncell(z) + 1))
pt.set_names(z, ["Zone"])
zv = pt.as_polygons(z)   # SpatRaster -> SpatVector polygons
zv
```

```{code-cell} python
z2 = pt.subset(zv, rows=[1])
fig, ax = plt.subplots(figsize=(5, 5))
pt.polys(p,  ax=ax, edgecolor="black", facecolor="none", linewidth=1)
pt.polys(zv, ax=ax, edgecolor="blue",  facecolor="none", linewidth=5)
pt.polys(z2, ax=ax, edgecolor="red",   facecolor="red",  linewidth=2);
```

To append `SpatVector` objects of the same (vector) type you can use `rbind`
on their attribute frames combined with `pt.merge()`:

```{code-cell} python
b = pt.merge([p, zv])
pt.vect_as_df(b).head()
```

```{code-cell} python
pt.vect_as_df(b).tail()
```

### Aggregate

It is common to aggregate ("dissolve") polygons that have the same value for
an attribute of interest. In this case, if we do not care about the
second-level subdivisions of Luxembourg, we could aggregate by the first
level subdivisions.

```{code-cell} python
:tags: [agg]
pa = pt.aggregate(p, by="NAME_1")
za = pt.aggregate(zv)

fig, ax = plt.subplots(figsize=(5, 5))
pt.polys(za, ax=ax, edgecolor="lightgray", facecolor="lightgray", linewidth=5)
pt.polys(pa, ax=ax, edgecolor="white",     facecolor="none",      linewidth=3);
```

It is also possible to aggregate polygons without dissolving the borders:

```{code-cell} python
:tags: [aggnodis]
zag = pt.aggregate(zv, dissolve=False)
zag
```

This is a structure that is similar to what you may get for an archipelago:
multiple polygons represented as one entity (one row). Use `disagg` to
split these up into their parts.

```{code-cell} python
zd = pt.disagg(zag)
zd
```

## Overlay

There are many different ways to "overlay" vector data. Here are some
examples.

### Erase

Erase a part of a `SpatVector`:

```{code-cell} python
:tags: [raser]
e = pt.erase(p, z2)
fig, ax = plt.subplots(figsize=(5, 5))
pt.polys(e, ax=ax, edgecolor="black", facecolor="none", linewidth=1);
```

### Intersect

Intersect `SpatVector` objects:

```{code-cell} python
:tags: [int]
i = pt.intersect(p, z2)
fig, ax = plt.subplots(figsize=(5, 5))
pt.polys(i, ax=ax, edgecolor="black", facecolor="none", linewidth=1);
```

You can also `intersect` or `crop` with a `SpatExtent` (rectangle).
The difference between intersect and crop is that with crop the geometry of
the second argument is not added to the output.

```{code-cell} python
:tags: [intext]
e = pt.ext(6, 6.4, 49.7, 50)
pe = pt.crop(p, e)

fig, ax = plt.subplots(figsize=(5, 5))
pt.polys(p, ax=ax, edgecolor="black", facecolor="none", linewidth=0.5)
xmin, xmax, ymin, ymax = e.vector
ax.add_patch(plt.Rectangle((xmin, ymin),
                           xmax - xmin,
                           ymax - ymin,
                           edgecolor="red", facecolor="none", linewidth=3))
pt.polys(pe, ax=ax, edgecolor="blue", facecolor="lightblue", linewidth=2);
```

### Union

Get the union of two `SpatVector` objects.

```{code-cell} python
u = pt.union(p, zv)
u
```

Note that there are many more polygons now: one for each unique combination
of polygons (and attributes in this case).

```{code-cell} python
:tags: [unionplot]
rng = np.random.default_rng(5)
fig, ax = plt.subplots(figsize=(5, 5))
pt.polys(u, ax=ax, edgecolor="black", facecolor="none", linewidth=0.4);
```

### Cover

`cover` is a combination of `intersect` and `union`. The
former returns new (intersected) geometries with the attributes of both input
datasets; the latter appends geometries and attributes. `cover` returns
the intersection and appends the other geometries and attributes of both
datasets.

```{code-cell} python
:tags: [cov]
cov = pt.cover(p, pt.subset(zv, rows=[0, 3]))
cov
fig, ax = plt.subplots(figsize=(5, 5))
pt.polys(cov, ax=ax, edgecolor="black", facecolor="none", linewidth=0.5);
```

### Difference

The symmetrical difference of two `SpatVector` objects:

```{code-cell} python
:tags: [dif]
dif = pt.symdif(zv, p)
dif
fig, ax = plt.subplots(figsize=(5, 5))
pt.polys(dif, ax=ax, edgecolor="black", facecolor="none", linewidth=0.4);
```

## Spatial queries

We can query polygons with points ("point-in-polygon query").

```{code-cell} python
:tags: [pts]
pts_xy = np.array([[6.0, 50.0], [6.1, 49.9], [5.9, 49.8],
                   [5.7, 49.7], [6.4, 49.5]])
spts = pt.vect(pts_xy, crs=pt.crs(p))

fig, ax = plt.subplots(figsize=(5, 5))
pt.polys(zv, ax=ax, edgecolor="blue", facecolor="lightblue", linewidth=2)
pt.points(spts, ax=ax, color="lightgray", s=240)
for k, (x, y) in enumerate(pts_xy, start=1):
    ax.text(x + 0.02, y + 0.02, str(k), color="red", fontsize=12,
            fontweight="bold")
pt.polys(p, ax=ax, edgecolor="blue", facecolor="none", linewidth=2);
```

`extract` is used for queries between `SpatVector` and `SpatRaster` objects,
and also for queries between `SpatVector`s. Tappa's :func:`pt.extract` takes
the source (raster *or* polygons) first, then the query locations:

```{code-cell} python
pt.extract(p, spts)
```

```{code-cell} python
pt.extract(zv, spts)
```

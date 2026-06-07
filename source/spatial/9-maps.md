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

# Maps

You can make a map with `pt.plot(x)` for either a `SpatRaster` or a
`SpatVector`. The vector path picks the right painter from the geometry
type (points, lines, polygons), sets a geographic aspect ratio, and accepts
`y=` to colour features by an attribute. For overlays use `pt.points()`,
`pt.lines()`, and `pt.polys()`.

```{admonition} TODO
:class: warning

Interactive zoom / select / click helpers (the R `terra` `zoom()`, `sel()`
and `click()` functions) are not yet ported to *tappa*. For now, use
*Matplotlib* event handlers inside a notebook.
```

```{code-cell} python
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import tappa as pt

DATA = Path("../../data").resolve()
```

## SpatVector

Example data:

```{code-cell} python
:tags: [vect_1]
p = pt.vect(str(DATA / "lux.shp"))
```

If you plot a `SpatVector` without further arguments you get default
fill / outline and no legend.

```{code-cell} python
:tags: [maps_1]
pt.plot(p, figsize=(5, 5));
```

To colour features by an attribute pass `y=`:

```{code-cell} python
:tags: [maps_2]
pt.plot(p, y="NAME_2", col="hsv", figsize=(5, 5),
        edgecolor="black", linewidth=0.3);
```

You can request maps for multiple variables by drawing two subplots and
targeting each with `ax=`:

```{code-cell} python
:tags: [maps_4a]
fig, axes = plt.subplots(1, 2, figsize=(10, 5))
pt.plot(p, y="NAME_1", col="hsv", ax=axes[0],
        edgecolor="black", linewidth=0.3, main="NAME_1")
pt.plot(p, y="NAME_2", col="hsv", ax=axes[1],
        edgecolor="black", linewidth=0.3, main="NAME_2")
fig.tight_layout();
```

Below we make two maps "by hand", adjusting spacing, placing legends inside
the map area, and using non-rotated y-axis tick labels:

```{code-cell} python
:tags: [maps_4b]
fig, axes = plt.subplots(1, 2, figsize=(10, 5))
for ax, field, title in zip(axes, ["NAME_1", "NAME_2"], ["District", "Canton"]):
    pt.plot(p, y=field, col="hsv", ax=ax,
            edgecolor="black", linewidth=0.3, main="")
    ax.set_title(title)
    ax.tick_params(axis="y", labelrotation=0)
    leg = ax.legend(loc="upper right", fontsize=8, frameon=True)
    leg.set_title(field)
fig.subplots_adjust(wspace=0.15);
```

More customisation: choose which axes to draw, add a title to the legend, and
put a box around it.

```{code-cell} python
:tags: [maps_5]
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
for ax, field, title in zip(axes, ["NAME_1", "NAME_2"], ["District", "Canton"]):
    pt.plot(p, y=field, col="hsv", ax=ax, axes=False, legend=False,
            edgecolor="black", linewidth=0.3, main="")
    ax.set_xticks([5, 7])
    ax.set_yticks([49, 51])
    ax.tick_params(axis="y", labelrotation=0)
    leg = ax.legend(loc="upper right", fontsize=7, title=title, frameon=True)
fig.subplots_adjust(wspace=0.1);
```

We can combine multiple `SpatVector` layers — *Matplotlib* draws in z-order:

```{code-cell} python
:tags: [maps_6]
d = pt.aggregate(p, by="NAME_1")
ax = pt.plot(p, col="lightblue", edgecolor="red",
             linewidth=2, linestyle=":", figsize=(5, 5), legend=False)
pt.polys(d, ax=ax, edgecolor="black", facecolor="none", linewidth=5)
pt.polys(d, ax=ax, edgecolor="white", facecolor="none", linewidth=1)
pt.text(p, "NAME_2", ax=ax, cex=0.6, halo=True);
```

## SpatRaster

Example data:

```{code-cell} python
:tags: [maps_10]
f = DATA / "elev.tif"
r = pt.rast(str(f))
```

The default display of a single-layer `SpatRaster` always shows a colour
bar.

```{code-cell} python
:tags: [maps_11]
pt.plot(r, figsize=(5, 4));
```

After plotting a `SpatRaster` you can add vector spatial data (points,
lines, polygons) by drawing on the same `Axes`:

```{code-cell} python
:tags: [maps_12]
ax = pt.plot(r, figsize=(5, 4))
pt.polys(p, ax=ax, edgecolor="black", facecolor="none", linewidth=2)

np.random.seed(12)
v = pt.spat_sample(r, 20, method="random", na_rm=True, asPoints=True)
pt.points(v, ax=ax, col="red", cex=2);
```

Or use a different legend type:

```{code-cell} python
:tags: [maps_13]
pt.plot(r, type="interval", figsize=(5, 4));
```

If there are only a few values, the default is to show "classes":

```{code-cell} python
:tags: [maps_14]
rr = pt.round_(r / 100)
pt.plot(rr, figsize=(5, 4));
```

If the raster is categorical you get the category labels in the legend.

Make a categorical (factor) raster:

```{code-cell} python
:tags: [maps_15]
import pandas as pd

x = pt.classify(r, np.array([140, 300, 400, 550]))
levels_df = pd.DataFrame({"id": [0, 1, 2],
                          "elevation": ["low", "intermediate", "high"]})
x = pt.set_levels(x, levels_df)
print("is factor:", pt.is_factor(x))
print(x)

pt.plot(x, col=["green", "blue", "lightgray"], figsize=(8, 4));
```

When `pt.plot()` is used with a multi-layer object, all layers are plotted
(up to 16 by default), unless the layers desired are indicated with an
additional argument:

```{code-cell} python
:tags: [maps_16]
b = pt.rast([r, pt.sqrt(r)])
b = pt.set_names(b, ["elevation", "sqrt(elevation)"])
pt.plot(b, figsize=(8, 5));
```

It often makes sense to combine three layers into a single image by
assigning each one to a colour channel (red, green and blue). Most
multispectral satellite sensors record more than three bands and the
choice of which bands to map to which channel determines what features
stand out in the image.

`sent2_L2A_2024-08-24.tif` is a low-resolution Sentinel-2 L2A composite
over Luxembourg taken on 2024-08-24. It contains four bands: blue (B02),
green (B03), red (B04) and near-infrared (B08).

```{code-cell} python
:tags: [maps_20]
s2 = pt.rast(str(DATA / "sent2_L2A_2024-08-24.tif"))
print(s2)
```

A *true colour* (or "natural colour") composite maps the visible-light
bands to the corresponding screen channels: B04 → red, B03 → green,
B02 → blue. Sentinel-2 surface reflectance is stored as integers scaled
by 10 000, but a 2–98% linear stretch removes the need to know the
exact scale.

```{code-cell} python
:tags: [maps_21]
pt.plot_rgb(s2, red=2, green=1, blue=0, stretch="lin", figsize=(6, 5));
```

A *false colour* composite shifts the near-infrared band into the red
channel (B08 → red, B04 → green, B03 → blue). Healthy vegetation
reflects strongly in NIR and so appears bright red, which makes
agriculture, forests and water bodies very easy to tell apart.

```{code-cell} python
:tags: [maps_22]
pt.plot_rgb(s2, red=3, green=2, blue=1, stretch="lin", figsize=(6, 5));
```

You can also use a number of other plotting functions with `SpatRaster`s,
including histograms (`matplotlib.pyplot.hist(pt.values(r).ravel())`) and
contour plots (`matplotlib.pyplot.contour`).

## Basemaps

The R tutorial uses `maptiles::get_tiles()`. In Python you can add a web-tile
basemap with the *contextily* package (internet access required during the
notebook build):

```{code-cell} python
:tags: [maps_basemap]
try:
    import contextily as cx
except ImportError:
    print("Install contextily to run this cell: pip install contextily")
else:
    ax = pt.plot(p, figsize=(6, 6), legend=False)
    cx.add_basemap(ax, crs=pt.crs(p), source=cx.providers.OpenStreetMap.Mapnik)
    pt.polys(p, ax=ax, facecolor="none", edgecolor="blue", linewidth=2);
```

```{admonition} Note
:class: note

A native `tappa` tile fetcher (e.g. `pt.maptiles()`) is not implemented yet.
For production maps, *contextily* or *folium* are the usual Python choices.
```

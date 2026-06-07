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

# Exploration

In this chapter we describe how to explore satellite remote sensing data with
*Python* and *tappa*, and how to use them to make maps.

We primarily use a spatial subset of a Landsat 8 scene collected on June 14,
2017. The subset covers the area between
[Concord and Stockton](https://www.google.com/maps/@37.940913,-121.7143556,55474m/data=!3m1!1e3),
California, USA.

All Landsat scenes have a unique product ID and metadata. For example, the
product identifier used here is `LC08_044034_20170614`: OLI/TIRS on Landsat 8,
WRS path 44, row 34, acquired 2017-06-14. Landsat scenes are commonly delivered
as separate files per band, combined into a single zip archive.

Download the data first (see [Chapter 1](1-introduction) if you have not already
done so).

```{code-cell} python
from pathlib import Path
import urllib.request
import zipfile
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tappa as pt

DATA = Path("../../data").resolve()
RS = DATA / "rs"
if not (RS / "LC08_044034_20170614_B2.tif").exists():
    urllib.request.urlretrieve(
        "https://geodata.ucdavis.edu/rspatial/rs.zip", RS / "rs.zip")
    with zipfile.ZipFile(RS / "rs.zip") as zf:
        zf.extractall(DATA)
```

## Image properties

Create `SpatRaster` objects for single Landsat layers (bands):

```{code-cell} python
b2 = pt.rast(str(RS / "LC08_044034_20170614_B2.tif"))   # Blue
b3 = pt.rast(str(RS / "LC08_044034_20170614_B3.tif"))   # Green
b4 = pt.rast(str(RS / "LC08_044034_20170614_B4.tif"))   # Red
b5 = pt.rast(str(RS / "LC08_044034_20170614_B5.tif"))   # NIR
b2
```

## Image information and statistics

```{code-cell} python
print("CRS:", pt.crs(b2))
print("ncell:", pt.ncell(b2), "dim:", b2.nrow(), b2.ncol())
print("res:", pt.res(b2))
print("nlyr:", pt.nlyr(b2))
print("same extent:", pt.ext(b2).vector == pt.ext(b3).vector)
print("same resolution:", pt.res(b2) == pt.res(b3))
```

Combine single-layer rasters into a multi-band image:

```{code-cell} python
s = pt.rast([b5, b4, b3])
s
```

Or stack from filenames:

```{code-cell} python
filenames = [str(RS / f"LC08_044034_20170614_B{i}.tif") for i in range(1, 12)]
landsat = pt.rast(filenames)
landsat
```

The 11 layers represent: Ultra Blue, Blue, Green, Red, NIR, SWIR1, SWIR2,
Panchromatic, Cirrus, TIRS1, TIRS2.

## Single band and composite maps

```{code-cell} python
:tags: [rs2multi]
fig, axes = plt.subplots(2, 2, figsize=(9, 7))
for ax, band, title in zip(axes.flat, [b2, b3, b4, b5],
                           ["Blue", "Green", "Red", "NIR"]):
    pt.plot(band, ax=ax, col="gray", main=title)
plt.tight_layout();
```

True-colour composite (bands 4, 3, 2 = red, green, blue):

```{code-cell} python
:tags: [truecolor]
landsat_rgb = pt.rast([b4, b3, b2])
pt.plot_rgb(landsat_rgb, stretch="lin", figsize=(7, 6));
```

False-colour composite (NIR, red, green):

```{code-cell} python
:tags: [rs2plotrgb]
landsat_fcc = pt.rast([b5, b4, b3])
pt.plot_rgb(landsat_fcc, stretch="lin", figsize=(7, 6));
```

**Question 1**: *Use `pt.plot_rgb()` with the 11-layer `landsat` object to
create true- and false-colour composites (remember the band positions).*

## Subset and rename bands

```{code-cell} python
landsatsub1 = pt.subset(landsat, list(range(3)))   # first 3 bands (0-based)
landsatsub2 = pt.subset(landsat, list(range(3)))
print(pt.nlyr(landsat), pt.nlyr(landsatsub1), pt.nlyr(landsatsub2))
```

Keep the first seven bands and set descriptive names:

```{code-cell} python
landsat = pt.subset(landsat, list(range(7)))
pt.set_names(landsat, ["ultra-blue", "blue", "green", "red",
                       "NIR", "SWIR1", "SWIR2"])
print(landsat.names)
```

## Spatial subset or crop

```{code-cell} python
:tags: [crop]
print(pt.ext(landsat))
e = pt.ext(624387, 635752, 4200047, 4210939)
landsatcrop = pt.crop(landsat, e)
landsatcrop
```

**Question 2**: *Use `landsatcrop` to plot true- and false-colour composites.*

## Saving results to disk

```{code-cell} python
pt.write(landsatcrop, str(RS / "cropped-landsat.tif"), overwrite=True)
```

## Relation between bands

Sample cell values and plot band relationships:

```{code-cell} python
:tags: [rs2pairs1]
samp = pt.spat_sample(landsatcrop, 3000, method="random")
bands = [c for c in samp.columns if c not in ("cell", "x", "y")]
plt.figure(figsize=(5, 5))
plt.scatter(samp[bands[0]], samp[bands[1]], s=2, alpha=0.3)
plt.xlabel("Band 1"); plt.ylabel("Band 2")
plt.title("Ultra-blue versus Blue");
```

```{code-cell} python
:tags: [rs2pairs2]
plt.figure(figsize=(5, 5))
plt.scatter(samp[bands[3]], samp[bands[4]], s=2, alpha=0.3)
plt.xlabel("Band 4"); plt.ylabel("Band 5")
plt.title("Red versus NIR");
```

## Extract cell values

```{code-cell} python
import geopandas as gpd
from shapely.geometry import Point

def sample_polygons(gpkg, n, seed=0):
    """Random points inside polygons (spat_sample is raster-only for now)."""
    gdf = gpd.read_file(gpkg)
    rng = np.random.default_rng(seed)
    pts, classes = [], []
    bounds = gdf.total_bounds
    while len(pts) < n:
        x, y = rng.uniform(bounds[0], bounds[2]), rng.uniform(bounds[1], bounds[3])
        p = Point(x, y)
        for _, row in gdf.iterrows():
            if row.geometry.contains(p):
                pts.append((x, y))
                classes.append(row["class"])
                break
    v = pt.vect(np.array(pts), crs=str(gdf.crs))
    return pt.set_values(v, pd.DataFrame({"class": classes}))

ptsamp = sample_polygons(RS / "lcsamples.gpkg", 50, seed=555)
df = pt.extract(landsat, ptsamp)
df.head()
```

## Spectral profiles

```{code-cell} python
pts_df = pt.vect_as_df(ptsamp)
df["class"] = pts_df["class"].values
band_cols = [c for c in df.columns if c not in ("ID", "class", "cell")]
ms = df.groupby("class")[band_cols].mean()
ms
```

```{code-cell} python
:tags: [rs2spect]
mycolor = ["darkred", "yellow", "burlywood", "cyan", "blue"]
x = np.arange(1, len(band_cols) + 1)

fig, ax = plt.subplots(figsize=(6, 4))
for (cls, row), col in zip(ms.iterrows(), mycolor):
    ax.plot(x, row.values, lw=3, color=col, label=cls)
ax.set_xlabel("Bands"); ax.set_ylabel("Reflectance")
ax.set_ylim(0, 0.6)
ax.set_title("Spectral Signatures", fontweight="bold")
ax.legend(loc="upper left");
```

The spectral signatures show how different surface features reflect energy
across wavelengths. Water has relatively low reflection in all bands; built,
fallow, and open areas reflect more in longer wavelengths.

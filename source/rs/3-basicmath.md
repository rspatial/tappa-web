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

# Basic mathematical operations

The *tappa* package supports many mathematical operations. Math operations are
generally performed per pixel (grid cell). First we combine bands with basic
arithmetic to calculate vegetation indices such as
[NDVI](http://phenology.cr.usgs.gov/ndvi_foundation.php).

We use the same Landsat data as in Chapter 2.

```{code-cell} python
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import tappa as pt

DATA = Path("../../data").resolve()
RS = DATA / "rs"
rfiles = [str(RS / f"LC08_044034_20170614_B{i}.tif") for i in range(1, 12)]
landsat = pt.rast(rfiles)
pt.set_names(landsat, [f"B{i}" for i in range(1, 12)])
landsat_rgb = pt.subset(landsat, [3, 2, 1])   # R,G,B = bands 4,3,2
landsat_fcc = pt.subset(landsat, [4, 3, 2])   # NIR,R,G = bands 5,4,3
```

## Vegetation indices

A general ratio-based vegetation index function:

```{code-cell} python
:tags: [rs3vi]
def vi(img, k, i):
    """Band indices are 0-based layer positions."""
    bk = pt.subset(img, [k])
    bi = pt.subset(img, [i])
    return (bk - bi) / (bk + bi)
```

```{code-cell} python
:tags: [rs3ndvi]
# Landsat: NIR = layer 4, red = layer 3 (0-based)
ndvi = vi(landsat, 4, 3)
pt.plot(ndvi, col=plt.cm.terrain(np.linspace(1, 0, 10)),
        main="NDVI", figsize=(6, 5));
```

The same result can be obtained with band arithmetic on subset layers (as in the
`vi()` helper above). The `lapp()` function requires raster values in memory;
for large file-backed images, prefer layer-wise expressions as shown here.

**Question 1**: *Adapt the code to compute indices that highlight water and
built-up areas (use the spectral profile plots or
[this reference](https://www.harrisgeospatial.com/docs/BackgroundOtherIndices.htm)).*

## Histogram

```{code-cell} python
:tags: [rs2hist]
vals = pt.values(ndvi).ravel()
vals = vals[np.isfinite(vals)]
plt.hist(vals, bins=30, color="wheat", range=(-0.5, 1))
plt.xlabel("NDVI"); plt.ylabel("Frequency")
plt.title("NDVI values");
```

**Question 2**: *Make histograms of the vegetation indices from Question 1.*

## Thresholding

Cells with NDVI > 0.4 are likely vegetation. Mask values below 0.4:

```{code-cell} python
:tags: [rs3veg1]
veg = pt.clamp(ndvi, lower=0.4, values=False)
pt.plot(veg, main="Vegetation", figsize=(6, 5));
```

Map the peak between 0.25 and 0.3 in the NDVI histogram:

```{code-cell} python
:tags: [rs3land]
rcl = [[-np.inf, 0.25, np.nan],
       [0.25, 0.30, 1],
       [0.30, np.inf, np.nan]]
land = pt.classify(ndvi, rcl)
pt.plot(land, main="What is it?", figsize=(6, 5));
```

Overlay on the RGB composite:

```{code-cell} python
:tags: [rs3rgb1]
ax = pt.plot_rgb(landsat_rgb, stretch="lin", figsize=(6, 5))
pt.polys(pt.as_polygons(land), ax=ax, facecolor="none",
         edgecolor="yellow", linewidth=1);
```

Create classes for different vegetation intensity:

```{code-cell} python
:tags: [rs3veg2]
vegc = pt.classify(ndvi, [0.25, 0.4, 0.5, 1.0])
pt.plot(vegc, col=plt.cm.terrain(np.linspace(1, 0, 4)),
        main="NDVI based thresholding", figsize=(6, 5));
```

**Question 3**: *Can you find water using thresholding of NDVI or other
indices?*

## Principal component analysis

```{code-cell} python
:tags: [rs3pca1]
np.random.seed(1)
sr = pt.spat_sample(landsat, 10000)
bands = [c for c in sr.columns if c not in ("cell", "x", "y")]
plt.scatter(sr[bands[4]], sr[bands[3]], s=1, alpha=0.2)
plt.xlabel("NIR"); plt.ylabel("Red")
plt.title("NIR-Red plot");
```

```{code-cell} python
:tags: [rs3pca2]
band_cols = [c for c in sr.columns if c not in ("cell", "x", "y")]  # all bands
X = sr[band_cols].to_numpy()
pca = PCA().fit(X)
print("Explained variance ratio:", pca.explained_variance_ratio_.round(3))
plt.plot(np.cumsum(pca.explained_variance_ratio_), "o-")
plt.xlabel("Component"); plt.ylabel("Cumulative variance")
plt.title("Scree plot");
```

Apply the first two principal components to the full image:

```{code-cell} python
:tags: [rs3pca2b]
flat = pt.values(landsat)
nrow, ncol = landsat.nrow(), landsat.ncol()
pc = pca.transform(flat)[:, :2]
pci = pt.rast([
    pt.set_values(pt.subset(landsat, [0]), pc[:, 0].reshape(nrow, ncol, order="F")),
    pt.set_values(pt.subset(landsat, [0]), pc[:, 1].reshape(nrow, ncol, order="F")),
])
pt.set_names(pci, ["PC1", "PC2"])
pt.plot(pci, figsize=(10, 4));
```

Threshold the second component:

```{code-cell} python
:tags: [rs3rgb2]
rcl = [[-np.inf, -3, np.nan], [-3, -2, 0], [-2, -1, 1], [-1, 0, 2],
       [0, 1, 3], [1, 2, 4], [2, 6, 5], [6, np.inf, np.nan]]
pc_class = pt.classify(pt.subset(pci, [1]), rcl)

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
pt.plot_rgb(landsat_fcc, stretch="lin", ax=axes[0], main="False Color")
pt.plot(pc_class, ax=axes[1], main="PCA")
plt.tight_layout();
```

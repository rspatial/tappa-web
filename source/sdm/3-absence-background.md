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

# Absence and background points

Some SDM algorithms (Bioclim, Domain) use only presence data. Other methods use
absence or background data. Logistic regression is the classical approach for
presence/absence data. With presence-only data you can substitute background
points for absences when fitting methods that require both classes.

The `terra` / *tappa* function `spat_sample` draws random points from a study
area. Use a raster mask to exclude `NA` cells (for example, ocean). You can
restrict the area further by cropping to an extent.

```{code-cell} python
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tappa as pt

DATA = Path("../../data").resolve()
SDM = DATA / "sdm"

r = pt.rast([str(SDM / "bio.tif"), str(SDM / "biome.tif")])

np.random.seed(1963)
bg = pt.spat_sample(r, 5000, "random", na_rm=True, asPoints=True)
```

```{code-cell} python
:tags: [sdm15]
ax = pt.plot(r, 0, figsize=(9, 6))
pt.points(bg, ax=ax, s=4);
```

Limit sampling to a sub-region:

```{code-cell} python
e = pt.ext(-80, -53, -39, -22)
r_sub = pt.crop(r, e)
bg2 = pt.spat_sample(r_sub, 500, "random", na_rm=True, asPoints=True)

ax = pt.plot(r, 0, figsize=(9, 6))
pt.lines(pt.as_polygons(e), ax=ax, col="red", lwd=2)
pt.points(bg2, ax=ax, s=8);
```

## Pseudo-absence from buffered presence

VanDerWal *et al.* (2009) sampled within a radius of presence points. Below we
use the cleaned *Solanum acaule* data with 50 km buffers.

```{code-cell} python
ac_df = pd.read_csv(SDM / "acaule_clean.csv")
ac = pt.vect(ac_df, geom=("lon", "lat"), crs="+proj=longlat +datum=WGS84")

x = pt.buffer(ac, width=50_000)
pol = pt.aggregate(x)
```

```{code-cell} python
mask = pt.rasterize(pol, pt.subset(r, [0]), background=np.nan)
cell_ids = np.flatnonzero(np.isfinite(pt.values(mask).ravel()))
rng = np.random.default_rng(999)
chosen = rng.choice(cell_ids, size=min(500, len(cell_ids)), replace=False)
xy = pt.xy_from_cell(r, chosen)
samp1 = pt.vect(xy, crs=pt.crs(r))
```

```{code-cell} python
:tags: [sdm20]
ax = pt.plot(pol, figsize=(9, 6))
pt.points(samp1, ax=ax, marker="+", s=12)
pt.points(pt.vect(xy, crs=pt.crs(r)), ax=ax, s=20, col="blue");
```

Cell centers need not fall inside the circles. Keep only points inside the
buffer polygons:

```{code-cell} python
spxy = pt.vect(xy, crs=pt.crs(r))
xy_inside = pt.intersect(spxy, x)
```

Alternative via rasterization:

```{code-cell} python
m = pt.crop(pt.subset(r, [0]), pt.ext(x))
m2 = pt.rasterize(x, m, background=np.nan)
flag = np.isfinite(pt.values(m2).ravel()).astype(float)
m2 = pt.set_values(m2, flag.reshape(m2.nrow(), m2.ncol(), order="F"))

ax = pt.plot(m2, figsize=(9, 6))
pt.lines(x, ax=ax, col="black");
```

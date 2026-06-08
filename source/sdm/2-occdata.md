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

# Data preparation

## Species occurrence data

Importing occurrence data into *Python* is easy. But collecting, georeferencing,
and cross-checking coordinate data is tedious. When you are dealing with species
with few and uncertain records, your focus probably ought to be on improving the
quality of the occurrence data (Lobo, 2008).

## Importing occurrence data

In most cases you will have a file with point locality data representing the
known distribution of a species.

```{code-cell} python
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tappa as pt

DATA = Path("../../data").resolve()
SDM = DATA / "sdm"

bradypus = pd.read_csv(SDM / "bradypus.csv")
bradypus.head()
```

Coordinates should be organized with longitude first and latitude second. The
*Bradypus* file keeps only those two columns:

```{code-cell} python
bradypus = bradypus.iloc[:, 1:3]
bradypus.head()
```

Many occurrence records come from the
[Global Biodiversity Information Facility (GBIF)](http://www.gbif.org/). The
*R* tutorial downloads *Solanum acaule* records with `geodata::sp_occurrence`;
here we use a saved extract shipped with the tutorial data.

```{code-cell} python
acaule = pd.read_csv(SDM / "acaule.csv", encoding="latin-1")
acaule.shape
```

Select records that have longitude and latitude:

```{code-cell} python
acgeo = acaule.dropna(subset=["lon", "lat"]).copy()
acgeo.shape
acgeo.iloc[:5, [0, 1, 2, 3, 4, 6, 7, 8, 9]]
```

Map the occurrence localities:

```{code-cell} python
wrld = pt.vect(str(SDM / "world.gpkg"))
fig, ax = plt.subplots(figsize=(9, 5))
pt.plot(wrld, ax=ax, col="lightyellow", border="lightgray", legend=False)
ax.set_xlim(-110, 90)
ax.set_ylim(-80, 40)
ax.scatter(acgeo["lon"], acgeo["lat"], c="red", s=8)
ax.set_axis_off();
```

## Data cleaning

`Solanum acaule` occurs in the high Andes of southern Peru, Bolivia and
northern Argentina. Some records map in the ocean south of Pakistan — a common
mistake: missing minus signs. Other errors include duplicated records and
longitude values of zero.

Inspect the Pakistan records:

```{code-cell} python
bad_idx = acgeo.index[(acgeo["lon"] > 60) & (acgeo["lat"] > 20)]
acgeo.loc[bad_idx[:2], acaule.columns[:10]]
```

Remove duplicate rows (same coordinates):

```{code-cell} python
lonzero = acgeo.loc[acgeo["lon"] == 0]
dups = lonzero.duplicated(subset=lonzero.columns[:10])
lonzero = lonzero.loc[dups]

dups2 = acgeo.duplicated(subset=["lon", "lat"])
sum(dups2)
acg = acgeo.loc[~dups2].copy()
```

Repatriate records near Pakistan to Argentina, and keep Andean records:

```{code-cell} python
i = (acg["lon"] > 0) & (acg["lat"] > 0)
acg.loc[i, "lon"] = -acg.loc[i, "lon"]
acg.loc[i, "lat"] = -acg.loc[i, "lat"]
acg = acg.loc[(acg["lon"] < -60) & (acg["lat"] > -50)].copy()
acg.shape
```

## Cross-checking

Cross-check coordinates against country polygons (Hijmans *et al.*, 1999).

```{code-cell} python
acv = pt.vect(acg, geom=("lon", "lat"), crs="+proj=longlat +datum=WGS84")
ovr = pt.extract(wrld, acv)
ovr.head()
```

```{code-cell} python
cntr = ovr["NAME_0"]
j = np.where(cntr.to_numpy() != acg["country"].to_numpy())[0]
m = pd.DataFrame({"polygons": cntr.iloc[j].to_numpy(),
                  "acaule": acg["country"].iloc[j].to_numpy()})
m
```

```{code-cell} python
fig, ax = plt.subplots(figsize=(7, 6))
pt.points(acv, ax=ax, s=6, col="gray")
pt.lines(wrld, ax=ax, col="blue", lwd=2)
pt.points(pt.subset(acv, rows=j.tolist()), ax=ax, col="red", s=40);
```

## Georeferencing

Records with locality descriptions but no coordinates can be georeferenced
manually or with web services. The *R* tutorial demonstrates `predicts::geocode`
(Google API); that step is not reproduced here.

```{code-cell} python
georef = acaule.loc[
    (acaule["lon"].isna() | acaule["lat"].isna()) & acaule["locality"].notna()
]
georef.shape
georef.iloc[:3, :13]
```

## Sampling bias

Sampling bias is frequently present in occurrence records (Hijmans *et al.*,
2001). One approach is to subsample to at most one record per grid cell using
`grid_sample`:

```{code-cell} python
:tags: [sdm100]
r = pt.rast(acv, resolution=1)
r = pt.extend(r, 1, snap="out")

# Thin to at most one record per grid cell (saved result below).
acsel_df = pd.read_csv(SDM / "acaule_clean.csv")
acsel = pt.vect(acsel_df, geom=("lon", "lat"), crs=pt.crs(acv))

p = pt.as_polygons(r, aggregate=False)
fig, ax = plt.subplots(figsize=(7, 6))
pt.plot(p, ax=ax, col="none", border="gray", legend=False)
pt.points(acv, ax=ax, s=8, col="black")
pt.points(acsel, ax=ax, s=30, col="red", marker="x");
```

Use `grid_sample` for the same thinning step; the `chess` argument selects
white or black checkerboard cells for train/test splitting.

```{code-cell} python
acsel_df.head()
```

In a real research project you would spend much more time on data cleaning,
partly with *Python*, but also with other programs and manual inspection.

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

# Environmental data

## Raster data

In species distribution modeling, predictor variables are organized as raster
layers. Layers should share extent, resolution, origin, and CRS. Use functions
such as `crop`, `extend`, `aggregate`, `resample`, and `project` to prepare
data — see [Raster manipulation](../spatial/8-rastermanip).

```{code-cell} python
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pandas.plotting import scatter_matrix
import tappa as pt

DATA = Path("../../data").resolve()
SDM = DATA / "sdm"

predictors = pt.rast(str(SDM / "bio.tif"))
predictors
pt.names(predictors)
```

```{code-cell} python
:tags: [sdm22]
pt.plot(predictors, figsize=(10, 8));
```

Plot one layer with country boundaries and *Bradypus* occurrence points:

```{code-cell} python
wrld = pt.vect(str(SDM / "world.gpkg"))
bradypus = pd.read_csv(SDM / "bradypus.csv").iloc[:, 1:3]

ax = pt.plot(predictors, 0, figsize=(9, 5))
pt.lines(wrld, ax=ax, col="gray")
pt.points(pt.vect(bradypus.to_numpy(), crs=pt.crs(predictors)),
          ax=ax, col="blue", s=12);
```

The example data are bioclimatic variables from
[WorldClim](http://www.worldclim.org) (Hijmans *et al.*, 2004). You can download
more recent versions with the *R* `geodata` package or from the WorldClim website.

## Extracting values from rasters

Extract predictor values at presence and background locations and combine them
into one table. Column `pb` is 1 for presence and 0 for background.

```{code-cell} python
:tags: [sdm24]
bp = pt.vect(bradypus.to_numpy(), crs=pt.crs(predictors))
presvals = pt.extract(predictors, bp, ID=False)
presvals = presvals.drop(columns=["ID"], errors="ignore")

np.random.seed(0)
backgr = pt.spat_sample(predictors, 500, "random", na_rm=True, cells=False, xy=False)
absvals = backgr[[c for c in backgr.columns if c.startswith("bio")]]

pb = np.concatenate([np.ones(len(presvals)), np.zeros(len(absvals))])
sdmdata = pd.DataFrame(
    np.column_stack([pb, np.vstack([presvals.to_numpy(), absvals.to_numpy()])]),
    columns=["pb"] + list(presvals.columns),
)
sdmdata.head()
sdmdata.tail()
sdmdata.describe()
```

```{code-cell} python
scatter_matrix(sdmdata.iloc[:, 1:5], figsize=(6, 6), alpha=0.4, s=8);
```

The same table is saved for the modeling chapter:

```{code-cell} python
sdmdata = pd.read_csv(SDM / "sdmdata.csv")
presvals = pd.read_csv(SDM / "presvals.csv")
sdmdata.head()
```

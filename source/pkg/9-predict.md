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

# Spatial prediction

This chapter shows some examples for making spatial predictions with different
types of models. The *terra* package provides `predict()` and `interpolate()`
methods that apply a fitted model to every raster cell. Those high-level
wrappers are **not yet available** in *tappa*; here we use the same idea
manually: extract training values, fit a model in *scikit-learn* or *SciPy*,
then apply it to all cells with `pt.values()` and `pt.set_values()`.

For fuller geostatistical examples (kriging, IDW with *gstat*), see the
[Interpolation](../analysis/4-interpolation) chapter.

```{code-cell} python
:tags: [exa]
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from scipy.interpolate import griddata
import tappa as pt

DATA = Path("../../data").resolve()

def predict_raster(model, src, proba=False):
    """Apply a fitted sklearn model to all cells of a multi-layer raster."""
    arr = pt.values(src, mat=True)
    valid = np.all(np.isfinite(arr), axis=1)
    if proba:
        out = np.full((arr.shape[0], len(model.classes_)), np.nan)
        out[valid] = model.predict_proba(arr[valid])
        layers = []
        for i, cls in enumerate(model.classes_):
            layer = out[:, i].reshape(src.nrow(), src.ncol(), order="F")
            layers.append(pt.set_values(pt.subset(src, [0]), layer))
        return pt.rast(layers)
    out = np.full(arr.shape[0], np.nan, dtype=float)
    out[valid] = model.predict(arr[valid])
    return pt.set_values(pt.deepcopy(pt.subset(src, [0])),
                         out.astype(np.float32))


logo = pt.rast(str(DATA / "logo.tif"))
logo = pt.set_names(logo, ["red", "green", "blue"])

p = np.array([48, 48, 48, 53, 50, 46, 54, 70, 84, 85, 74, 84, 95, 85,
              66, 42, 26,  4, 19, 17,  7, 14, 26, 29, 39, 45, 51, 56, 46,
              38, 31, 22, 34, 60, 70, 73, 63, 46, 43, 28], dtype=float).reshape(-1, 2)
a = np.array([22, 33, 64, 85, 92, 94, 59, 27, 30, 64, 60, 33, 31,  9,
              99, 67, 15,  5,  4, 30,  8, 37, 42, 27, 19, 69, 60, 73,  3,
               5, 21, 37, 52, 70, 74,  9, 13,  4, 17, 47], dtype=float).reshape(-1, 2)

xy = np.vstack([
    np.column_stack([np.ones(len(p)), p]),
    np.column_stack([np.zeros(len(a)), a]),
])

e = pt.extract(logo, xy[:, 1:3], ID=False)
v = e.copy()
v.insert(0, "pa", xy[:, 0])
v = v.dropna()
```

## Predict

### GLM

A generalised linear model (here, ordinary least squares on a 0/1 response):

```{code-cell} python
:tags: [glm]
model = LinearRegression().fit(v.drop(columns="pa"), v["pa"])
r1 = predict_raster(model, logo)

ax = pt.plot(r1, figsize=(5, 4))
pt.points(pt.vect(p, crs=pt.crs(logo)), ax=ax, col="blue", s=15)
pt.points(pt.vect(a, crs=pt.crs(logo)), ax=ax, col="red", s=15);

# logistic regression
logit = LogisticRegression().fit(v.drop(columns="pa"), v["pa"].astype(int))
r1log = predict_raster(logit, logo)

r4 = predict_raster(logit, logo, proba=True)
pt.plot(r4, figsize=(8, 3));
```

### Random Forest

```{code-cell} python
:tags: [rf]
vv = v.copy()
vv["pa"] = vv["pa"].astype(int)
rfmod = RandomForestClassifier(n_estimators=100, random_state=1).fit(
    vv.drop(columns="pa"), vv["pa"])
r3 = predict_raster(rfmod, logo)
r4 = predict_raster(rfmod, logo, proba=True)
pt.plot(r4, figsize=(8, 3));
```

### k-nearest neighbours

With a kNN model we apply the same `predict_raster()` helper. In *terra* you
could alternatively use `app()` with a custom prediction function:

```{code-cell} python
:tags: [knn]
knn = KNeighborsClassifier(3).fit(v.drop(columns="pa"), v["pa"].astype(int))
k = predict_raster(knn, logo)
pt.plot(k, figsize=(5, 4));
```

## Interpolate

### Interpolation with x and y only

```{code-cell} python
:tags: [tps]
r = pt.rast(str(DATA / "meuse.tif"))
ra = pt.aggregate(r, 10)
cells = np.arange(pt.ncell(ra))
xy = pt.xy_from_cell(ra, cells)
vals = pt.values(ra).ravel()
valid = np.isfinite(vals)

target = pt.xy_from_cell(r, np.arange(pt.ncell(r)))
pred = griddata(xy[valid], vals[valid], target, method="cubic")
p = pt.set_values(pt.subset(r, [0]),
                  pred.reshape(r.nrow(), r.ncol(), order="F"))
p = pt.mask(p, r)
pt.plot(p, figsize=(5, 4));
```

For inverse-distance weighting, ordinary kriging, and universal kriging with
the Meuse data set, see [Interpolation](../analysis/4-interpolation). Those
examples use *SciPy* and manual raster prediction rather than a single
`interpolate()` call.

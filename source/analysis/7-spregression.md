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

# Spatial regression models

## Introduction

This chapter deals with the problem of inference in regression
models with spatial data. Such inference can be suspect because,
nearby things tend to be similar, and it may not be fair to assume
that nearby cases are independent of each other (they may be
pseudo-replicates). Therefore these models need to be diagnosed
before reporting them — particularly, by evaluating the residuals
for spatial autocorrelation.

If the residuals are spatially auto-correlated, the model is
mis-specified. We can try to improve it by adding (or removing)
important variables. If that is not possible, we can formulate a
regression model that controls for spatial autocorrelation. Below we
fit a *spatial lag* and a *spatial error* model.

## Reading & aggregating data

We use California house-price data from the 2000 Census.

```{code-cell} python
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tappa as pt

DATA = Path("../../data").resolve()
h = pt.vect(str(DATA / "houses2000.gpkg"))
print(h)
```

The dataset has 29 attributes describing each Census tract. We
aggregate to the county level.

```{code-cell} python
hdf = pt.vect_as_df(h)
print(hdf.shape)
hdf.head(2)
```

```{code-cell} python
hh = pt.aggregate(h, by="County")
print("counties:", hh.nrow())
```

Now compute the county-level attribute aggregates.

```{code-cell} python
sum_cols = ["nhousingUn", "recHouses", "nMobileHom", "nBadPlumbi",
            "nBadKitche", "Population", "Males", "Females", "Under5",
            "White", "Black", "AmericanIn", "Asian", "Hispanic",
            "PopInHouse", "nHousehold", "Families"]

d1 = hdf[["County"] + sum_cols].groupby("County").sum().reset_index()

mean_cols = ["houseValue", "yearBuilt", "nRooms", "nBedrooms",
             "medHHinc", "MedianAge", "householdS", "familySize"]
weights = hdf["nHousehold"].fillna(0)
d2_in = hdf[mean_cols].mul(weights, axis=0)
d2_in["County"] = hdf["County"]
d2_in["hh"]     = weights
d2_sum = d2_in.groupby("County").sum().reset_index()
for c in mean_cols:
    d2_sum[c] = d2_sum[c] / d2_sum["hh"]
d2_sum = d2_sum.drop(columns=["hh"])

d12 = d1.merge(d2_sum, on="County")
print(d12.shape)
d12.head(2)
```

Merge the aggregated attributes onto the dissolved county polygons.

```{code-cell} python
hh_df = pt.vect_as_df(hh)[["County"]].reset_index().rename(
    columns={"index": "_row"})
joined = hh_df.merge(d12, on="County", how="left")
joined = joined.sort_values("_row").reset_index(drop=True).drop(
    columns=["_row"])

from tappa._helpers import _makeSpatDF
hh.set_df(_makeSpatDF(joined))
print("hh:", hh.nrow(), "x", joined.shape[1])
```

Maps of house value and median household income. The SpatVector
plotter automatically bins numeric attributes into 10 equal-interval
classes.

```{code-cell} python
fig, axes = plt.subplots(1, 2, figsize=(12, 6))
pt.plot(h, "houseValue", border=None, ax=axes[0], legend=False)
pt.lines(hh, ax=axes[0], color="white")
axes[0].set_title("house value")

pt.plot(h, "medHHinc", border=None, ax=axes[1], legend=False)
pt.lines(hh, ax=axes[1], color="white")
axes[1].set_title("median household income");
```

## Basic OLS model

We compute some new variables and fit a simple OLS model with
`statsmodels`.

```{code-cell} python
import statsmodels.api as sm

hd = pt.vect_as_df(hh).copy()
hd["fBadP"] = np.maximum(hd["nBadPlumbi"], hd["nBadKitche"]) / \
              hd["nhousingUn"]
hd["fWhite"] = hd["White"] / hd["Population"]
hd["age"] = 2000 - hd["yearBuilt"]

X = sm.add_constant(hd[["age", "nBedrooms"]].astype(float))
y = hd["houseValue"].astype(float)
m1 = sm.OLS(y, X, missing="drop").fit()
print(m1.summary().tables[1])
print(f"R²={m1.rsquared:.4f}  adj-R²={m1.rsquared_adj:.4f}")
```

So the simple model: every additional bedroom adds about
\$192K to the value, and 100 years of age adds another \$1.27M.

**Question 1**: *Predict the price of a 1-year-old house with three
bedrooms.*

Visualise the residuals.

```{code-cell} python
hd["residuals"] = m1.resid
hh.set_df(_makeSpatDF(hd))

pt.plot(hh, "residuals", figsize=(6, 7));
```

Test for spatial autocorrelation in the residuals.

```{code-cell} python
W = pt.adjacent(hh, type="rook", pairs=False).astype(int)
res = hd["residuals"].to_numpy()
mask = ~np.isnan(res) & (W.sum(axis=1) > 0)
moran_obs = float(pt.autocor(res[mask], W[mask][:, mask],
                             method="moran"))
print("Moran's I (residuals):", round(moran_obs, 4))
```

Monte-Carlo significance test.

```{code-cell} python
rng = np.random.default_rng(0)
n_sim = 999
m_sim = np.array([
    pt.autocor(rng.permutation(res[mask]), W[mask][:, mask],
               method="moran")
    for _ in range(n_sim)
])
pval = (np.abs(m_sim) >= abs(moran_obs)).sum() / (n_sim + 1)
print("p-value:", round(pval, 4))
```

There is clear spatial autocorrelation: our OLS model cannot be
trusted. Let's try SAR models.

## Building a spatial weights object

`spreg` and `libpysal` use a `W` object. We can construct one from
the adjacency matrix.

```{code-cell} python
from libpysal.weights import W as PysalW

mask_idx = np.where(mask)[0]
neigh = {int(i): np.where(W[i])[0].tolist() for i in mask_idx}
weights = {int(i): [1.0] * len(neigh[int(i)]) for i in mask_idx}
w = PysalW(neighbors=neigh, weights=weights, silence_warnings=True)
w.transform = "r"
print("W:", w.n, "units, mean #neighbours",
      round(w.mean_neighbors, 2))
```

## Spatial lag model

Spatial lag — `y = ρ W y + Xβ + ε`.

```{code-cell} python
from spreg import GM_Lag

X_arr = hd.loc[mask, ["age", "nBedrooms"]].astype(float).to_numpy()
y_arr = hd.loc[mask, "houseValue"].astype(float).to_numpy().reshape(-1, 1)

m_lag = GM_Lag(y_arr, X_arr, w=w, name_y="houseValue",
               name_x=["age", "nBedrooms"])
print(m_lag.summary)
```

Check residual autocorrelation.

```{code-cell} python
res_lag = m_lag.u.flatten()
moran_lag = float(pt.autocor(res_lag, W[mask][:, mask],
                             method="moran"))
print("Moran's I (lag-model residuals):", round(moran_lag, 4))
```

Map them.

```{code-cell} python
res_full = np.full(hh.nrow(), np.nan)
res_full[mask] = res_lag
hd2 = hd.copy()
hd2["residuals"] = res_full
hh.set_df(_makeSpatDF(hd2))

pt.plot(hh, "residuals", figsize=(6, 7));
```

## Spatial error model

Spatial error — `y = Xβ + u, u = λ W u + ε`.

```{code-cell} python
from spreg import GM_Error

m_err = GM_Error(y_arr, X_arr, w=w, name_y="houseValue",
                 name_x=["age", "nBedrooms"])
print(m_err.summary)
```

```{code-cell} python
res_err = m_err.u.flatten()
moran_err = float(pt.autocor(res_err, W[mask][:, mask],
                             method="moran"))
print("Moran's I (error-model residuals):", round(moran_err, 4))
```

Map.

```{code-cell} python
res_full = np.full(hh.nrow(), np.nan)
res_full[mask] = res_err
hd2 = hd.copy()
hd2["residuals"] = res_full
hh.set_df(_makeSpatDF(hd2))

pt.plot(hh, "residuals", figsize=(6, 7));
```

## Questions

**Question 2**: *The last two maps still seem to show a lot of
spatial autocorrelation. But the tests give a much smaller value of
Moran's I. Why?*

**Question 3**: *Variable selection — perhaps the most important
aspect of modelling. Try expanding the model with more variables
(income, white-fraction, ...) and re-running the diagnostics.*

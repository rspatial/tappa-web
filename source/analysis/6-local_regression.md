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

# Local regression

Regression models are typically *global*: all data are used
simultaneously to fit a single model. In some cases it can make
sense to fit more flexible *local* models. Such models exist in a
general regression framework (e.g. generalized additive models),
where "local" refers to the values of the predictor variables. In a
spatial context "local" refers to *location*. Rather than fitting a
single regression model, it is possible to fit several models, one
for each location (out of possibly very many) locations. This
technique is sometimes called *geographically weighted regression*
(GWR). GWR is a data-exploration technique that allows us to
understand changes in the importance of variables over space.

There are two examples here. A short one with California precipitation
data, and a more elaborate one with house-price data.

## California precipitation

```{code-cell} python
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tappa as pt

DATA = Path("../../data").resolve()
counties = pt.vect(str(DATA / "counties.gpkg"))
p = pd.read_csv(DATA / "precipitation.csv")
p.head()
```

```{code-cell} python
ax = pt.plot(counties, col="lightgray", legend=False, figsize=(5, 6))
ax.scatter(p["LONG"], p["LAT"], color="red", s=8);
```

Compute annual precipitation.

```{code-cell} python
mnts = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
        "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
p["pan"] = p[mnts].sum(axis=1)
```

A simple global regression of annual precipitation on altitude.

```{code-cell} python
from sklearn.linear_model import LinearRegression

X = p[["ALT"]].to_numpy()
y = p["pan"].to_numpy()
m = LinearRegression().fit(X, y)
print("intercept:", round(float(m.intercept_), 2),
      " ALT slope:", round(float(m.coef_[0]), 4))
```

Project to Teale Albers.

```{code-cell} python
alb = ("+proj=aea +lat_1=34 +lat_2=40.5 +lat_0=0 +lon_0=-120 "
       "+x_0=0 +y_0=-4000000 +datum=WGS84 +units=m")
sp   = pt.vect(p, geom=("LONG", "LAT"),
               crs="+proj=longlat +datum=WGS84")
spt  = sp.project(alb)
ctst = counties.project(alb)
```

### Home-brew GWR with a Gaussian kernel

For each fit-point we compute Gaussian-kernel-weighted least squares
of `pan ~ ALT`. Bandwidth selection is done by leave-one-out
cross-validation (golden-section search).

```{code-cell} python
xy_pts = pt.crds(spt)


def gwr_fit_one(target, src_xy, X, y, bw):
    d2 = ((src_xy - target) ** 2).sum(axis=1)
    w  = np.exp(-0.5 * d2 / bw ** 2)
    Xw = np.column_stack([np.ones_like(y), X])
    WX = Xw * w[:, None]
    XtWX = Xw.T @ WX
    XtWy = WX.T @ y
    try:
        beta = np.linalg.solve(XtWX, XtWy)
    except np.linalg.LinAlgError:
        return np.full(Xw.shape[1], np.nan)
    return beta


def gwr_loocv(bw, src_xy, X, y):
    err = 0.0
    n = len(y)
    Xw = np.column_stack([np.ones_like(y), X])
    for i in range(n):
        m = np.ones(n, dtype=bool); m[i] = False
        beta = gwr_fit_one(src_xy[i], src_xy[m], X[m], y[m], bw)
        if np.isnan(beta).any():
            err += (y[i] - y.mean()) ** 2
        else:
            yhat = Xw[i] @ beta
            err += (y[i] - yhat) ** 2
    return err


from scipy.optimize import minimize_scalar
opt = minimize_scalar(gwr_loocv, bounds=(10_000, 800_000),
                      method="bounded",
                      args=(xy_pts, p["ALT"].to_numpy(), y),
                      options={"xatol": 1000})
bw = opt.x
print(f"optimal bandwidth: {bw / 1000:.1f} km, CV score: {opt.fun:.0f}")
```

Build a regular grid of fit-points covering the counties.

```{code-cell} python
r  = pt.rast(ctst, resolution=10000)
ca = pt.rasterize(ctst, r)
fit_xy = pt.crds(pt.asPoints(ca))
print("fit points:", fit_xy.shape)
```

Run the GWR.

```{code-cell} python
betas = np.array([
    gwr_fit_one(xy0, xy_pts, p["ALT"].to_numpy(), y, bw)
    for xy0 in fit_xy
])
intercept_v = betas[:, 0]
slope_v     = betas[:, 1]
```

Reconnect the results to the raster.

```{code-cell} python
intercept_r = pt.deepcopy(ca)
slope_r     = pt.deepcopy(ca)
mask = ~np.isnan(pt.values(ca, mat=False))
icp = np.full(int(pt.ncell(ca)), np.nan, dtype=np.float32)
slp = np.full(int(pt.ncell(ca)), np.nan, dtype=np.float32)
icp[mask] = intercept_v.astype(np.float32)
slp[mask] = slope_v.astype(np.float32)

intercept_r = pt.setValues(intercept_r, icp)
slope_r     = pt.setValues(slope_r, slp)
s = pt.rast([intercept_r, slope_r])
s = pt.setNamesRast(s, ["intercept", "slope"])
pt.plot(s, figsize=(8, 4));
```

## California house-price data

We use 1990 census house-price data
([Pace & Barry 1997](https://doi.org/10.1016/S0167-7152(96)00140-X)).

```{code-cell} python
houses = pd.read_csv(DATA / "houses1990.csv")
print(houses.shape)
houses.head()
```

Each record represents a census *block group*. Make a SpatVector of
the centroids and assign the same CRS as the counties.

```{code-cell} python
hvect = pt.vect(houses, geom=("longitude", "latitude"))
hvect.set_crs(counties.get_crs("wkt"))
```

Spatial query — point-in-polygon.

```{code-cell} python
cnty = pt.extract(counties, hvect)
cnty.head()
```

Combine the extracted county data with the original house data.

```{code-cell} python
hd = pd.concat([houses.reset_index(drop=True),
                cnty.reset_index(drop=True)], axis=1)
hd = hd.loc[:, ~hd.columns.duplicated()]
hd.head(2)
```

### Summarise

Population by county.

```{code-cell} python
totpop = hd.groupby("NAME")["population"].sum()
totpop.head()
```

Approximate median household income by county.

```{code-cell} python
hd["suminc"] = hd["income"] * hd["households"]
csum = hd.groupby("NAME").agg({"suminc": "sum",
                                "households": "sum"}).reset_index()
csum["income"] = 10_000 * csum["suminc"] / csum["households"]
csum = csum.sort_values("income").reset_index(drop=True)
csum.head()
```

```{code-cell} python
csum.tail()
```

### Regression

Add some new variables.

```{code-cell} python
hd["roomhead"]    = hd["rooms"]    / hd["population"]
hd["bedroomhead"] = hd["bedrooms"] / hd["population"]
hd["hhsize"]      = hd["population"] / hd["households"]
```

Ordinary least-squares regression with `statsmodels`.

```{code-cell} python
import statsmodels.formula.api as smf

m = smf.ols(
    "houseValue ~ income + houseAge + roomhead + bedroomhead + population",
    data=hd,
).fit()
print(m.summary().tables[1])
```

## Geographically weighted regression

### By county

We fit one OLS model per county.

```{code-cell} python
hd2 = hd.dropna(subset=["NAME"]).copy()


def regfun(df):
    if len(df) < 8:
        return None
    return smf.ols(
        "houseValue ~ income + houseAge + roomhead + bedroomhead + population",
        data=df,
    ).fit().params


res = {n: regfun(g) for n, g in hd2.groupby("NAME")}
res = {k: v for k, v in res.items() if v is not None}
resdf = pd.DataFrame(res).T
resdf.head()
```

A dot-chart of the *income* coefficient.

```{code-cell} python
inc = resdf["income"].sort_values()
fig, ax = plt.subplots(figsize=(5, 10))
ax.scatter(inc.values, range(len(inc)), s=10)
ax.set_yticks(range(len(inc)))
ax.set_yticklabels(inc.index, fontsize=7);
```

There is clearly variation in the coefficient β for income. Map the
results.

```{code-cell} python
dcounties = pt.aggregateVect(counties, by="NAME")
print("counties:", counties.nrow(), " dissolved:", dcounties.nrow())
```

Merge the county geometry with the regression-coefficient data
frame.

```{code-cell} python
cnty_df = pt.vectAsDF(dcounties).reset_index().rename(
    columns={"index": "_row"})
joined = cnty_df.merge(resdf.reset_index().rename(
    columns={"index": "NAME"}), on="NAME", how="left")
joined = joined.sort_values("_row").reset_index(drop=True)

cnres = pt.deepcopy(dcounties)
new_attrs = joined.drop(columns=["_row"])
from tappa._helpers import _makeSpatDF
cnres.set_df(_makeSpatDF(new_attrs))

pt.plot(cnres, "income", figsize=(5, 6));
```

Is there spatial autocorrelation in the coefficients?

```{code-cell} python
lw = pt.adjacent(cnres, type="rook", pairs=False).astype(int)
inc_vals = pt.vectAsDF(cnres)["income"].to_numpy()
mask = ~np.isnan(inc_vals)
print("Moran's I (income):",
      round(float(pt.autocor(inc_vals[mask], lw[mask][:, mask],
                             method="moran")), 4))

age_vals = pt.vectAsDF(cnres)["houseAge"].to_numpy()
mask = ~np.isnan(age_vals)
print("Moran's I (houseAge):",
      round(float(pt.autocor(age_vals[mask], lw[mask][:, mask],
                             method="moran")), 4))
```

### By grid cell

An alternative is to fit a separate regression for each grid cell,
using all observations within a fixed radius. Let us use Teale-Albers
and 50 km cells.

```{code-cell} python
TA = ("+proj=aea +lat_1=34 +lat_2=40.5 +lat_0=0 +lon_0=-120 "
      "+x_0=0 +y_0=-4000000 +datum=WGS84 +units=m")
countiesTA = counties.project(TA)
r = pt.rast(countiesTA, resolution=50000)
xy = pt.xyFromCell(r, np.arange(pt.ncell(r)))
```

```{code-cell} python
housesTA = hvect.project(TA)
crds = pt.crds(housesTA)
```

Run a regression in a 50 km neighbourhood of each cell that has at
least 50 observations.

```{code-cell} python
from scipy.spatial import cKDTree

tree = cKDTree(crds)
income_grid = np.full(int(pt.ncell(r)), np.nan, dtype=float)

for i, target in enumerate(xy):
    idx = tree.query_ball_point(target, r=50_000)
    if len(idx) < 50:
        continue
    sub = hd.iloc[idx]
    try:
        beta = smf.ols(
            "houseValue ~ income + houseAge + roomhead + bedroomhead + "
            "population",
            data=sub,
        ).fit().params
        income_grid[i] = float(beta["income"])
    except Exception:                                      # noqa: BLE001
        pass
```

```{code-cell} python
rinc = pt.setValues(pt.deepcopy(r), income_grid.astype(np.float32))
ax = pt.plot(rinc, figsize=(6, 6))
pt.lines(countiesTA, ax=ax);
```

Spatial autocorrelation of the income coefficient.

```{code-cell} python
print("Moran's I (income coefficient):",
      round(float(pt.autocor(rinc, method="moran")), 4))
```

So that was a lot of "home-brew GWR".

**Question 1**: *Comment on the strengths and weaknesses of the
approaches above.*

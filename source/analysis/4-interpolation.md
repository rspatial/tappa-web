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

# Interpolation

## Introduction

Almost any geographic variable of interest has spatial autocorrelation
(see [the previous chapter](3-spauto)). That can be a problem in
statistical tests, but it is a very useful feature when we want to
predict values at locations where no measurements have been made; we
can generally safely assume that values at nearby locations will be
similar. There are several spatial interpolation techniques. We show
some of them in this chapter.

## Temperature in California

We will be working with temperature data for California, USA. The
data are CSVs that ship with this book.

```{code-cell} python
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tappa as pt

DATA = Path("../../data").resolve()

d = pd.read_csv(DATA / "precipitation.csv")
d.head()
```

Compute annual precipitation.

```{code-cell} python
mnts = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
        "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
d["prec"] = d[mnts].sum(axis=1)

fig, ax = plt.subplots(figsize=(5, 3.5))
ax.plot(np.sort(d["prec"]), marker="o", lw=0)
ax.set_xlabel("Stations"); ax.set_ylabel("Annual precipitation (mm)");
```

Now make a quick map.

```{code-cell} python
dsp = pt.vect(d, geom=("LONG", "LAT"), crs="+proj=longlat +datum=NAD83")
CA  = pt.vect(str(DATA / "counties.gpkg"))

ax = pt.plot(CA, col="lightgray", lwd=2, border="darkgray",
             legend=False, figsize=(6, 6))
pt.plot(dsp, "prec", ax=ax, cex=1.5)
pt.lines(CA, ax=ax);
```

Transform longitude/latitude to planar coordinates, using the
commonly used coordinate reference system for California ("Teale
Albers") to assure that our interpolation results will align with
other data sets we have.

```{code-cell} python
TA = ("+proj=aea +lat_1=34 +lat_2=40.5 +lat_0=0 +lon_0=-120 "
      "+x_0=0 +y_0=-4000000 +datum=WGS84 +units=m")
dta  = dsp.project(TA)
cata = CA.project(TA)
```

### Null model

We are going to interpolate (estimate for unsampled locations) the
precipitation values. The simplest way would be to take the mean of
all observations. We can consider that a "Null-model" that we can
compare other approaches to. We'll use the Root Mean Square Error
(RMSE) as evaluation statistic.

```{code-cell} python
def rmse(observed, predicted):
    obs = np.asarray(observed, dtype=float)
    pre = np.asarray(predicted, dtype=float)
    m = ~(np.isnan(obs) | np.isnan(pre))
    return float(np.sqrt(np.mean((pre[m] - obs[m]) ** 2)))


prec = d["prec"].to_numpy()
null_rmse = rmse(prec, np.full_like(prec, prec.mean()))
null_rmse
```

So 435 mm is our target. Can we do better (have a smaller RMSE)?

### Proximity polygons

Proximity polygons can be used to interpolate categorical variables.
Another term for this is "nearest neighbour" interpolation.

```{code-cell} python
v = pt.voronoi(dta)
ax = pt.plot(v, legend=False, figsize=(5, 5))
pt.points(dta, ax=ax);
```

Let's cut out what is not California, and map precipitation.

```{code-cell} python
vca = v.crop(cata)
pt.plot(vca, "prec", figsize=(5, 5));
```

Now we can `rasterize` the results like this.

```{code-cell} python
r  = pt.rast(vca, resolution=10000)
vr = pt.rasterize(vca, r, field="prec")
pt.plot(vr, figsize=(5, 5));
```

And use 5-fold cross-validation to evaluate this model.

```{code-cell} python
rng = np.random.default_rng(5132015)
kf = rng.integers(0, 5, size=dta.nrow())

rmses = []
for k in range(5):
    test  = dta[kf == k]
    train = dta[kf != k]
    vk    = pt.voronoi(train)
    p     = pt.extract(vk, test)
    rmses.append(rmse(pt.vectAsDF(test)["prec"], p["prec"]))

rmses = np.array(rmses)
print("rmse per fold:", rmses.round(2))
print("mean rmse:", rmses.mean().round(2))
print("relative perf:", round(1 - rmses.mean() / null_rmse, 3))
```

**Question 1**: *Describe what each step in the code chunk above does
(that is, how does cross-validation work?)*

**Question 2**: *How does the proximity-polygon approach compare to
the NULL model?*

**Question 3**: *You would not typically use proximity polygons for
rainfall data. For what kind of data might you use them?*

### Nearest neighbour interpolation

Here we do nearest neighbour interpolation considering multiple (5)
neighbours and weighting them equally.

We use `scipy.spatial.cKDTree` to find the *k* nearest neighbours and
take an unweighted average. We compute predictions at every cell
centre of `r`.

```{code-cell} python
from scipy.spatial import cKDTree

xy = pt.crds(dta)
y  = pt.vectAsDF(dta)["prec"].to_numpy()
tree = cKDTree(xy)


def knn_predict(target_xy, k, idp=0.0):
    """k nearest neighbours; idp=0 -> unweighted, else 1/d^idp weights."""
    dist, idx = tree.query(target_xy, k=k)
    if k == 1:
        return y[idx]
    if idp == 0.0:
        return y[idx].mean(axis=1)
    w = 1.0 / np.maximum(dist, 1e-12) ** idp
    return (w * y[idx]).sum(axis=1) / w.sum(axis=1)


cell_xy = pt.xyFromCell(r, np.arange(pt.ncell(r)))
nn_vals = knn_predict(cell_xy, k=5, idp=0.0)
nn = pt.setValues(pt.deepcopy(r), nn_vals.astype(np.float32))
nnmsk = pt.mask(nn, vr)
pt.plot(nnmsk, figsize=(5, 5));
```

Cross-validate. We can re-fit a tree on training data inside the loop.

```{code-cell} python
rmsenn = []
for k in range(5):
    test_xy  = xy[kf == k]
    train_xy = xy[kf != k]
    test_y   = y [kf == k]
    train_y  = y [kf != k]
    tk = cKDTree(train_xy)
    _, ix = tk.query(test_xy, k=5)
    pred = train_y[ix].mean(axis=1)
    rmsenn.append(rmse(test_y, pred))

rmsenn = np.array(rmsenn)
print("rmse per fold:", rmsenn.round(2))
print("mean rmse:", rmsenn.mean().round(2))
print("relative perf:", round(1 - rmsenn.mean() / null_rmse, 3))
```

### Inverse distance weighted

A more commonly used method is "inverse distance weighted"
interpolation. The only difference with the nearest neighbour
approach is that points further away get less weight in predicting a
value at a location.

```{code-cell} python
idw_vals = knn_predict(cell_xy, k=len(y), idp=2.0)
idwr = pt.setValues(pt.deepcopy(r), idw_vals.astype(np.float32))
idwr = pt.mask(idwr, vr)
pt.plot(idwr, figsize=(5, 5));
```

**Question 4**: *IDW generated rasters tend to have a noticeable
artefact. What is that and what causes that?*

Cross-validate.

```{code-cell} python
rmseidw = []
for k in range(5):
    test_xy  = xy[kf == k]
    train_xy = xy[kf != k]
    test_y   = y [kf == k]
    train_y  = y [kf != k]
    tk = cKDTree(train_xy)
    dist, ix = tk.query(test_xy, k=len(train_y))
    w = 1.0 / np.maximum(dist, 1e-12) ** 2
    pred = (w * train_y[ix]).sum(axis=1) / w.sum(axis=1)
    rmseidw.append(rmse(test_y, pred))

rmseidw = np.array(rmseidw)
print("mean rmse:", rmseidw.mean().round(2))
print("relative perf:", round(1 - rmseidw.mean() / null_rmse, 3))
```

**Question 5**: *What happens to IDW if you use* `k=1`*and* `idp=1`*?
Why? Illustrate with a map.*

## California air-pollution data

We use the California air-pollution data to illustrate geostatistical
(kriging) interpolation.

### Data preparation

We use the airqual dataset to interpolate ozone levels for
California (averages for 1980-2009). Use the variable `OZDLYAV`
(unit is parts per billion).

To get easier numbers to read, multiply `OZDLYAV` by 1000.

```{code-cell} python
aq = pd.read_csv(DATA / "airqual.csv")
aq = aq.dropna(subset=["OZDLYAV", "LONGITUDE", "LATITUDE"]).copy()
aq["OZDLYAV"] = aq["OZDLYAV"] * 1000
aq_v = pt.vect(aq, geom=("LONGITUDE", "LATITUDE"),
               crs="+proj=longlat +datum=WGS84")
```

Project to Teale Albers in km (kriging often works better in km).

```{code-cell} python
TAkm = ("+proj=aea +lat_1=34 +lat_2=40.5 +lat_0=0 +lon_0=-120 "
        "+x_0=0 +y_0=-4000000 +datum=WGS84 +units=km")
aq_v = aq_v.project(TAkm)
ca   = CA.project(TAkm)

xy_aq = pt.crds(aq_v)
oz    = pt.vectAsDF(aq_v)["OZDLYAV"].to_numpy()
xy_aq.shape, oz.shape
```

Create a template `SpatRaster` to interpolate to.

```{code-cell} python
r = pt.rast(ca, resolution=10)  # 10 km
r
```

### Fit a variogram

Use `pykrige` to fit a variogram and run ordinary kriging.

```{code-cell} python
from pykrige.ok import OrdinaryKriging

OK = OrdinaryKriging(
    xy_aq[:, 0], xy_aq[:, 1], oz,
    variogram_model="exponential",
    nlags=20, verbose=False, enable_plotting=False,
)
print("variogram parameters:", OK.variogram_model_parameters)
```

Plot the empirical and modelled variogram.

```{code-cell} python
lags  = OK.lags
gam   = OK.semivariance
model = OK.variogram_function(OK.variogram_model_parameters, lags)

fig, ax = plt.subplots(figsize=(5, 3.5))
ax.scatter(lags, gam, color="red", s=20, label="empirical")
ax.plot(lags, model, color="blue", lw=2, label="exponential")
ax.set_xlabel("Distance (km)"); ax.set_ylabel("Semivariance");
ax.legend();
```

### Ordinary kriging

Predict on the raster grid.

```{code-cell} python
cell_xy = pt.xyFromCell(r, np.arange(pt.ncell(r)))
pred, var = OK.execute("points", cell_xy[:, 0], cell_xy[:, 1])

ok_pred = pt.setValues(pt.deepcopy(r), np.asarray(pred,
                       dtype=np.float32))
ok_var  = pt.setValues(pt.deepcopy(r), np.asarray(var,
                       dtype=np.float32))
ok = pt.rast([ok_pred, ok_var])
ok = pt.setNamesRast(ok, ["prediction", "variance"])
ok = pt.mask(ok, ca)
pt.plot(ok, figsize=(8, 4));
```

### Compare with other methods

IDW (using all neighbours, power 2):

```{code-cell} python
tree = cKDTree(xy_aq)


def idw_grid(target_xy, src_xy, src_y, k=None, idp=2.0):
    if k is None:
        k = len(src_y)
    tk = cKDTree(src_xy)
    dist, ix = tk.query(target_xy, k=k)
    w = 1.0 / np.maximum(dist, 1e-12) ** idp
    return (w * src_y[ix]).sum(axis=1) / w.sum(axis=1)


idw_pred = idw_grid(cell_xy, xy_aq, oz, idp=2.0)
idp = pt.setValues(pt.deepcopy(r), idw_pred.astype(np.float32))
idp = pt.mask(idp, ca)
pt.plot(idp, figsize=(5, 5));
```

A thin-plate spline using `scipy.interpolate.RBFInterpolator`:

```{code-cell} python
from scipy.interpolate import RBFInterpolator

tps_model = RBFInterpolator(xy_aq, oz, kernel="thin_plate_spline",
                            smoothing=0.0)
tps_pred  = tps_model(cell_xy)
tps = pt.setValues(pt.deepcopy(r), tps_pred.astype(np.float32))
tps = pt.mask(tps, ca)
pt.plot(tps, figsize=(5, 5));
```

### Cross-validation

Cross-validate the three methods (IDW, ordinary kriging, TPS) and
build an RMSE-weighted ensemble.

```{code-cell} python
rng = np.random.default_rng(20150518)
k_idx = rng.integers(0, 5, size=len(oz))

idwrmse  = np.zeros(5)
krigrmse = np.zeros(5)
tpsrmse  = np.zeros(5)
ensrmse  = np.zeros(5)

for i in range(5):
    train_m = k_idx != i
    test_m  = k_idx == i
    Xt = xy_aq[test_m];  yt = oz[test_m]
    Xtr = xy_aq[train_m]; ytr = oz[train_m]

    p1 = idw_grid(Xt, Xtr, ytr, idp=2.0)
    idwrmse[i] = rmse(yt, p1)

    OKi = OrdinaryKriging(
        Xtr[:, 0], Xtr[:, 1], ytr,
        variogram_model="exponential", nlags=20, verbose=False,
        enable_plotting=False,
    )
    p2, _ = OKi.execute("points", Xt[:, 0], Xt[:, 1])
    p2 = np.asarray(p2)
    krigrmse[i] = rmse(yt, p2)

    tps_i = RBFInterpolator(Xtr, ytr, kernel="thin_plate_spline",
                            smoothing=0.0)
    p3 = tps_i(Xt)
    tpsrmse[i] = rmse(yt, p3)

    w  = np.array([idwrmse[i], krigrmse[i], tpsrmse[i]])
    ww = w / w.sum()
    ensemble = ww[0] * p1 + ww[1] * p2 + ww[2] * p3
    ensrmse[i] = rmse(yt, ensemble)

rms = pd.Series(
    {"IDW": idwrmse.mean(),
     "OK":  krigrmse.mean(),
     "TPS": tpsrmse.mean(),
     "ENS": ensrmse.mean()}
).round(3)
rms
```

**Question 6**: *Which method performed best?*

We can use the RMSE values to make a weighted ensemble. We use the
normalized difference between a model's RMSE and the NULL model as
weights.

```{code-cell} python
nullrmse = rmse(oz, np.full_like(oz, oz.mean()))
w  = nullrmse - np.array([rms["IDW"], rms["OK"], rms["TPS"]])
ww = w / w.sum()
print("weights:", ww.round(3), "sum:", ww.sum())

ens = ww[0] * pt.values(idp) + \
      ww[1] * pt.values(ok)[:, 0:1] + \
      ww[2] * pt.values(tps)
```

And compare maps.

```{code-cell} python
ens_r = pt.setValues(pt.deepcopy(r), ens.reshape(-1).astype(np.float32))
s = pt.rast([idp, pt.subsetRast(ok, [0]), tps, ens_r])
s = pt.setNamesRast(s, ["IDW", "OK", "TPS", "Ensemble"])
s = pt.mask(s, ca)
pt.plot(s, figsize=(8, 6));
```

**Question 7**: *Show where the largest difference exists between
IDW and OK.*

**Question 8**: *Show the 95% confidence interval of the OK
prediction.*

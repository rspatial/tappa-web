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

# Spatial distribution models

This chapter shows how you can use a Random Forest model to make
spatial predictions. This approach is widely used, for example to
classify remote sensing data into different land cover classes. Here
our objective is to predict the entire range of a species based on a
set of locations where it has been observed. As an example, we use
the hominid species *Imaginus magnapedum* (also known under the
vernacular names of "bigfoot" and "sasquatch"). This species is
believed to occur in the United States, but it is so hard to find by
scientists that its very existence is commonly denied by the
mainstream media — despite the many reports on Twitter! For more
information about this controversy, see the article by Lozier,
Aniello and Hickerson:
[Predicting the distribution of Sasquatch in western North America:
anything goes with ecological niche
modelling](http://onlinelibrary.wiley.com/doi/10.1111/j.1365-2699.2009.02152.x/abstract).

We will use "citizen-science" data to find out:

- What the complete range of the species might be.
- How good (general) our model is by predicting the range of the
  Eastern sub-species, with data from the Western sub-species.

In this context this type of analysis is often referred to as
*species distribution modelling* or *ecological niche modelling*.

## Data

### Observations

We get a data set of reported Bigfoot observations.

```{code-cell} python
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tappa as pt

DATA = Path("../../data").resolve()
bf = pd.read_csv(DATA / "bigfoot.csv")
print(bf.shape)
bf.head()
```

It is always good to first plot the locations to see what we are
dealing with.

```{code-cell} python
bnds = pt.vect(str(DATA / "north_america.gpkg"))

fig, ax = plt.subplots(figsize=(7, 5))
pt.plot(bnds, col="lightgray", border="black", legend=False, ax=ax)
ax.scatter(bf["lon"], bf["lat"], color="red", s=4);
```

So they are in Canada and in the United States, but no reports from
Mexico, so far.

### Predictor variables

Here, as is common in species distribution modelling, we use climate
data as predictor variables. Specifically we use the *bioclimatic
variables* (see [worldclim](https://www.worldclim.org/data/bioclim.html)).
For this book we ship a 10' resolution sub-set already cropped to
North America (~5 MB).

```{code-cell} python
wc = pt.rast(str(DATA / "wc_na.tif"))
wc = pt.set_names(wc, [f"bio_{i + 1}" for i in range(wc.nlyr())])
print(wc)
pt.plot(pt.subset(wc, [0, 11]), nc=2, figsize=(8, 4));
```

Now extract climate data for the locations of our observations.

```{code-cell} python
xy = bf[["lon", "lat"]].to_numpy()
bf_pts = pt.vect(xy, crs="+proj=longlat +datum=WGS84")
bfc = pt.extract(wc, bf_pts)
bfc = bfc.dropna()
print(bfc.shape)
bfc.head(3)
```

Drop the ID column.

```{code-cell} python
bfc_vars = bfc.drop(columns=["ID"])
```

Plot the species' distribution in a part of the *environmental*
space — temperature vs rainfall:

```{code-cell} python
fig, ax = plt.subplots(figsize=(5, 4))
ax.scatter(bfc_vars["bio_1"], bfc_vars["bio_12"], color="red", s=8)
ax.set_xlabel("Annual mean temperature (°C)")
ax.set_ylabel("Annual precipitation (mm)");
```

### Background data

We do not have a systematic survey, only presence locations. The
common approach is to compare the predictor values at presence
locations to those at random *background* locations.

```{code-cell} python
ext_bf = pt.ext(bf_pts) + 1
print(ext_bf)

wc_w = pt.crop(wc, ext_bf)
np.random.seed(0)
bg = pt.spat_sample(wc_w, 5000, method="random",
                    na_rm=True, asPoints=False, xy=True)
bg = bg.dropna()
print(bg.shape)
bg.head(3)
```

Plot of the random background points.

```{code-cell} python
fig, ax = plt.subplots(figsize=(7, 5))
pt.plot(bnds, col="lightgray", border="black", legend=False, ax=ax)
ax.scatter(bg["x"], bg["y"], color="black", s=2);
```

Drop the coordinate columns.

```{code-cell} python
bg_vars = bg.drop(columns=["x", "y"])
bg_vars.columns = bfc_vars.columns
```

Compare the climate of presence and background points.

```{code-cell} python
fig, ax = plt.subplots(figsize=(5, 4))
ax.scatter(bg_vars["bio_1"], bg_vars["bio_12"],
           color="black", s=8, label="background")
ax.scatter(bfc_vars["bio_1"], bfc_vars["bio_12"],
           color="red", s=8, marker="+", label="observed")
ax.set_xlabel("Annual mean temperature (°C)")
ax.set_ylabel("Annual precipitation (mm)")
ax.legend();
```

Bigfoot is widespread but not common in cold areas, nor in hot and
dry areas.

### East vs West

I split the data into East (lon > -102) and West (lon ≤ -102) — there
might be two sub-species. We focus on the western one.

```{code-cell} python
mask_west = bf["lon"].to_numpy() <= -102
mask_east = ~mask_west

bf_idx = bfc.index.to_numpy()
i_west = np.intersect1d(bf_idx, np.where(mask_west)[0])
i_east = np.intersect1d(bf_idx, np.where(mask_east)[0])

bfw = bfc_vars.loc[i_west].reset_index(drop=True)
bfe = bfc_vars.loc[i_east].reset_index(drop=True)
print("west:", bfw.shape, " east:", bfe.shape)
```

Combine presences (`pa=1`) with background (`pa=0`).

```{code-cell} python
def pa_frame(pres, bg):
    out = pd.concat([
        pd.concat([pd.Series(1, index=pres.index, name="pa"), pres],
                  axis=1),
        pd.concat([pd.Series(0, index=bg.index,   name="pa"), bg],
                  axis=1),
    ], axis=0, ignore_index=True)
    return out.dropna()


dw = pa_frame(bfw, bg_vars)
de = pa_frame(bfe, bg_vars)
print("dw:", dw.shape, " de:", de.shape)
```

## Fit a model

### CART

```{code-cell} python
from sklearn.tree import DecisionTreeRegressor, plot_tree

X_dw = dw.drop(columns=["pa"]).to_numpy()
y_dw = dw["pa"].to_numpy()

cart = DecisionTreeRegressor(min_samples_leaf=200, random_state=0)
cart.fit(X_dw, y_dw)
print("depth:", cart.get_depth(), " leaves:", cart.get_n_leaves())
```

Plot the tree (truncated to a small depth so it fits the page).

```{code-cell} python
fig, ax = plt.subplots(figsize=(10, 5))
plot_tree(cart, feature_names=dw.columns[1:].tolist(),
          ax=ax, filled=True, rounded=True, max_depth=3,
          fontsize=8);
```

**Question 1**: *What are the environmental conditions that Bigfoot
appears to enjoy most?*

Now use the model to show how attractive the climate is for this
species across all of North America.

```{code-cell} python
def predict_raster(model, src):
    arr = pt.values(src, mat=True)              # (ncell, nlyr)
    valid = ~np.isnan(arr).any(axis=1)
    out = np.full(arr.shape[0], np.nan, dtype=float)
    out[valid] = model.predict(arr[valid])
    return pt.set_values(pt.deepcopy(pt.subset(src, [0])),
                        out.astype(np.float32))


x = predict_raster(cart, wc)
pt.plot(x, figsize=(7, 5));
```

### Random Forest

CART suffers from high variance. Random Forest does not have that
problem as much. We do both regression and classification.

Hold out 20% of the western data for validation.

```{code-cell} python
rng = np.random.default_rng(123)
i_test = rng.choice(len(dw), size=int(0.2 * len(dw)), replace=False)
mask = np.zeros(len(dw), dtype=bool)
mask[i_test] = True
test  = dw.iloc[mask].reset_index(drop=True)
train = dw.iloc[~mask].reset_index(drop=True)
```

Classification model:

```{code-cell} python
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

X_tr = train.drop(columns=["pa"]).to_numpy()
y_tr = train["pa"].to_numpy().astype(int)
X_te = test.drop(columns=["pa"]).to_numpy()
y_te = test["pa"].to_numpy().astype(int)

crf = RandomForestClassifier(n_estimators=500, oob_score=True,
                             random_state=0, n_jobs=-1)
crf.fit(X_tr, y_tr)
print("OOB score:", round(crf.oob_score_, 4))
print("OOB error:", round(1 - crf.oob_score_, 4))
```

The variable importance plot shows which variables matter most.

```{code-cell} python
imp = pd.Series(crf.feature_importances_, index=dw.columns[1:])
imp.sort_values().plot(kind="barh", figsize=(5, 6));
```

Regression model.

```{code-cell} python
rrf = RandomForestRegressor(n_estimators=250, max_features=12,
                            random_state=0, n_jobs=-1)
rrf.fit(X_tr, y_tr.astype(float))
rrf
```

**Question 2**: *Why do we use both classification and regression?
What's the difference here?*

## Predict

### Regression

```{code-cell} python
rp = predict_raster(rrf, wc)
pt.plot(rp, figsize=(7, 5));
```

Threshold the regression to find a presence/absence map. We use ROC
analysis on the held-out test set.

```{code-cell} python
from sklearn.metrics import roc_curve, roc_auc_score

p_test = rrf.predict(X_te)
fpr, tpr, thr = roc_curve(y_te, p_test)
auc = roc_auc_score(y_te, p_test)
print("AUC:", round(auc, 3))

j = np.argmax(tpr - fpr)
threshold = thr[j]
print("max(sens+spec) threshold:", round(threshold, 3))
```

ROC plot.

```{code-cell} python
fig, ax = plt.subplots(figsize=(5, 4))
ax.plot(fpr, tpr, lw=2)
ax.plot([0, 1], [0, 1], color="black", ls="--")
ax.scatter(fpr[j], tpr[j], color="red", s=80, zorder=5,
           label=f"thr={threshold:.2f}")
ax.set_xlabel("False positive rate")
ax.set_ylabel("True positive rate")
ax.legend();
```

Score-distribution plots.

```{code-cell} python
fig, axes = plt.subplots(1, 2, figsize=(8, 4))
axes[0].boxplot([p_test[y_te == 1], p_test[y_te == 0]],
                tick_labels=["presence", "background"])
axes[0].set_ylabel("predicted probability")

axes[1].hist(p_test[y_te == 0], bins=30, alpha=0.5,
             label="background", density=True)
axes[1].hist(p_test[y_te == 1], bins=30, alpha=0.5,
             label="presence", density=True)
axes[1].set_xlabel("predicted probability")
axes[1].legend();
```

Map of predicted presence/absence.

```{code-cell} python
pa_map = rp > threshold
pt.plot(pa_map, figsize=(7, 5));
```

### Classification

We can also use the classification Random Forest model directly.

```{code-cell} python
def predict_proba_raster(model, src, target_class=1):
    arr = pt.values(src, mat=True)
    valid = ~np.isnan(arr).any(axis=1)
    out = np.full(arr.shape[0], np.nan, dtype=float)
    proba = model.predict_proba(arr[valid])
    classes = list(model.classes_)
    if target_class in classes:
        out[valid] = proba[:, classes.index(target_class)]
    return pt.set_values(pt.deepcopy(pt.subset(src, [0])),
                        out.astype(np.float32))


rc2 = predict_proba_raster(crf, wc, target_class=1)
pt.plot(rc2, figsize=(7, 5));
```

## Extrapolation

Can our western-trained model predict the eastern range?

```{code-cell} python
X_e = de.drop(columns=["pa"]).to_numpy()
y_e = de["pa"].to_numpy().astype(int)
p_e = rrf.predict(X_e)
auc_e = roc_auc_score(y_e, p_e)
print("AUC east:", round(auc_e, 3))
```

By this measure, it is a *terrible* model. The model is good in
predicting the range of the West but cannot extrapolate at all to the
East.

```{code-cell} python
ax = pt.plot(rp, figsize=(7, 5))
ax.scatter(bf["lon"], bf["lat"], color="black", s=2);
```

**Question 3**: *Why would the model not extrapolate well?*

## Further reading

More on
[Species distribution modelling with R](https://rspatial.org/sdm/).

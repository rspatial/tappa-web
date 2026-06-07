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

# Supervised Classification

Here we explore supervised classification for land use / land cover (LULC)
mapping. We use Classification and Regression Trees (CART) from
`scikit-learn` as an analogue of R's `rpart` package.

In supervised classification we have prior knowledge of land-cover types from
field work, reference data, or visual interpretation. Training sites provide
spectral signatures used to fit the classifier.

Steps:

- Create sample sites
- Extract reflectance values at sample locations
- Train the classifier
- Classify the Landsat image
- Evaluate accuracy

```{code-cell} python
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.tree import DecisionTreeClassifier, plot_tree
import tappa as pt

DATA = Path("../../data").resolve()
RS = DATA / "rs"


def predict_raster_proba(r, model):
    """Apply a fitted sklearn classifier; return per-class probability layers."""
    flat = pt.values(r)
    nrow, ncol = r.nrow(), r.ncol()
    valid = np.all(np.isfinite(flat), axis=1)
    proba = np.full((flat.shape[0], len(model.classes_)), np.nan)
    proba[valid] = model.predict_proba(flat[valid])
    layers = []
    for i, cls in enumerate(model.classes_):
        layer = proba[:, i].reshape(nrow, ncol, order="F")
        layers.append(pt.set_values(pt.subset(r, [0]), layer))
    out = pt.rast(layers)
    pt.set_names(out, [str(c) for c in model.classes_])
    return out
```

## Landsat data to classify

```{code-cell} python
:tags: [landsat]
raslist = [str(RS / f"LC08_044034_20170614_B{i}.tif") for i in range(2, 8)]
landsat = pt.rast(raslist)
pt.set_names(landsat, ["blue", "green", "red", "NIR", "SWIR1", "SWIR2"])
landsat
```

## Reference data

```{code-cell} python
:tags: [samples]
samp = pt.vect(str(RS / "lcsamples.gpkg"))
ax = pt.plot(samp, y="class", col="Set1", figsize=(6, 5))
pt.text(samp, "class", ax=ax, cex=0.7);
```

```{code-cell} python
:tags: [sample-points]
import geopandas as gpd
from shapely.geometry import Point

def sample_polygons(gpkg, n, seed=0):
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

ptsamp = sample_polygons(RS / "lcsamples.gpkg", 200, seed=1)
pt.plot(ptsamp, y="class", col="Set1", figsize=(6, 5));
```

Alternatively, sample from NLCD 2011:

```{code-cell} python
:tags: [nlcd]
nlcd = pt.rast(str(RS / "nlcd-L1.tif"))
pt.set_names(nlcd, ["nlcd2001", "nlcd2011"])
nlcd2011 = pt.subset(nlcd, [1])

nlcdclass = ["Water", "Developed", "Barren", "Forest",
             "Shrubland", "Herbaceous", "Cultivated", "Wetlands"]
levels_df = pd.DataFrame({"id": [1, 2, 3, 4, 5, 7, 8, 9],
                          "names": nlcdclass})
nlcd2011 = pt.set_levels(nlcd2011, levels_df)
classcolor = ["#5475A8", "#B50000", "#D2CDC0", "#38814E",
              "#AF963C", "#D1D182", "#FBF65D", "#C8E6F8"]

ax = pt.plot(nlcd2011, col=classcolor, figsize=(6, 5))
ptlonlat = pt.project(ptsamp, pt.crs(nlcd2011))
pt.points(ptlonlat, ax=ax, color="black", s=8);
```

```{code-cell} python
samp2011 = pt.spat_sample(nlcd2011, size=200, method="regular")
samp2011.value_counts().head()
```

## Extract reflectance values for training sites

```{code-cell} python
:tags: [extractvalues]
df = pt.extract(landsat, ptsamp, ID=False)
pts_df = pt.vect_as_df(ptsamp)
sampdata = pd.DataFrame({"class": pts_df["class"].values})
sampdata = pd.concat([sampdata, df], axis=1)
sampdata.head()
```

## Train the classifier

```{code-cell} python
:tags: [cart-train]
feature_cols = [c for c in sampdata.columns if c != "class"]
X = sampdata[feature_cols].to_numpy()
y = sampdata["class"].to_numpy()

cartmodel = DecisionTreeClassifier(min_samples_split=5, random_state=0)
cartmodel.fit(X, y)
cartmodel
```

```{code-cell} python
:tags: [cart-plot]
fig, ax = plt.subplots(figsize=(8, 6))
plot_tree(cartmodel, feature_names=feature_cols, class_names=cartmodel.classes_,
          filled=True, ax=ax, fontsize=8);
plt.tight_layout();
```

## Classify

Layer names in the prediction raster must match the training features.

```{code-cell} python
:tags: [prediction]
classified = predict_raster_proba(landsat, cartmodel)
classified
pt.plot(classified, figsize=(10, 4));
```

Pick the class with highest probability per cell:

```{code-cell} python
:tags: [combine-results1]
proba = np.stack([pt.values(pt.subset(classified, [i])).reshape(
    classified.nrow(), classified.ncol(), order="F")
    for i in range(pt.nlyr(classified))])
winner = np.nanargmax(proba, axis=0) + 1
lulc = pt.set_values(pt.subset(classified, [0]), winner.astype(float))
lulc
```

```{code-cell} python
:tags: [combine-results2]
cls = ["built", "cropland", "fallow", "open", "water"]
levels_df = pd.DataFrame({"id": list(range(1, 6)), "names": cls})
lulc = pt.set_levels(lulc, levels_df)
mycolor = ["darkred", "yellow", "burlywood", "cyan", "blue"]
pt.plot(lulc, col=mycolor, figsize=(7, 6));
```

## Model evaluation

Five-fold cross-validation:

```{code-cell} python
:tags: [kfold-setup]
np.random.seed(99)
k = 5
j = np.random.randint(1, k + 1, size=len(sampdata))
pd.Series(j).value_counts().sort_index()
```

```{code-cell} python
:tags: [k-fold]
rows = []
for fold in range(1, k + 1):
    train = sampdata[j != fold]
    test = sampdata[j == fold]
    cart = DecisionTreeClassifier(min_samples_split=5, random_state=0)
    cart.fit(train[feature_cols], train["class"])
    pred = cart.predict(test[feature_cols])
    rows.append(pd.DataFrame({"observed": test["class"].values,
                              "predicted": pred}))
y = pd.concat(rows, ignore_index=True)
```

```{code-cell} python
:tags: [confusion-matrix]
conmat = pd.crosstab(y["observed"], y["predicted"])
conmat
```

**Question 1**: *Comment on mis-classification between classes.*

**Question 2**: *How could you improve accuracy?*

Overall accuracy and kappa:

```{code-cell} python
:tags: [overallaccuracy]
n = conmat.to_numpy().sum()
diag = np.diag(conmat.to_numpy())
OA = diag.sum() / n
print("Overall accuracy:", round(OA, 3))
```

```{code-cell} python
:tags: [kappa]
cm = conmat.to_numpy().astype(float)
rowsums = cm.sum(axis=1) / n
colsums = cm.sum(axis=0) / n
exp_acc = (rowsums * colsums).sum()
kappa = (OA - exp_acc) / (1 - exp_acc)
print("Kappa:", round(kappa, 3))
```

Producer and user accuracy:

```{code-cell} python
:tags: [user-producer]
PA = diag / cm.sum(axis=0)
UA = diag / cm.sum(axis=1)
pd.DataFrame({"producerAccuracy": PA, "userAccuracy": UA},
             index=conmat.index)
```

**Question 3**: *Repeat the classification with
`sklearn.ensemble.RandomForestClassifier`.*

**Question 4**: *Plot CART and Random Forest results side-by-side.*

**Question 5 (optional)**: *Repeat for other years (e.g.
`centralvalley-2001LE7.tif`) using NLCD 2001.*

**Question 6 (optional)**: *Investigate the effect of training sample size
(100, 50, 25 per class).*

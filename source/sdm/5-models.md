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

# Model fitting, prediction, and evaluation

The original *R* tutorial uses the `predicts` package for profile methods and
evaluation. Here we use *statsmodels* for logistic regression, a small Bioclim
helper, and *scikit-learn* for ROC/AUC. Raster prediction follows the pattern
from [Spatial prediction](../pkg/9-predict).

```{code-cell} python
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.metrics import roc_auc_score
import tappa as pt

DATA = Path("../../data").resolve()
SDM = DATA / "sdm"

sdmdata = pd.read_csv(SDM / "sdmdata.csv")
presvals = pd.read_csv(SDM / "presvals.csv")
predictors = pt.rast(str(SDM / "bio.tif"))


class BioclimEnvelope:
    """Simple Bioclim envelope on environmental quantiles."""

    def __init__(self, df, cols=None, pct=(5, 95)):
        self.cols = list(cols or df.columns)
        qlo, qhi = pct[0] / 100, pct[1] / 100
        self.lo = df[self.cols].quantile(qlo)
        self.hi = df[self.cols].quantile(qhi)

    def predict(self, df):
        score = np.ones(len(df), dtype=float)
        for c in self.cols:
            vals = df[c].to_numpy(dtype=float)
            score *= (vals >= self.lo[c]) & (vals <= self.hi[c])
        return score


def pa_evaluate(p, a):
    """Presence-absence evaluation with AUC (like predicts::pa_evaluate)."""
    p = np.asarray(p, dtype=float)
    a = np.asarray(a, dtype=float)
    y = np.concatenate([np.ones(len(p)), np.zeros(len(a))])
    scores = np.concatenate([p, a])
    return {"AUC": float(roc_auc_score(y, scores))}


def predict_raster(model, src, cols, bioclim=False):
    """Apply a fitted model to all cells of a multi-layer raster."""
    arr = pt.values(src, mat=True)
    df = pd.DataFrame(arr[:, : len(cols)], columns=cols)
    valid = np.all(np.isfinite(df.to_numpy()), axis=1)
    out = np.full(arr.shape[0], np.nan, dtype=float)
    if bioclim:
        out[valid] = model.predict(df.loc[valid])
    else:
        out[valid] = model.predict(df.loc[valid])
    layer = out.reshape(src.nrow(), src.ncol(), order="F")
    return pt.set_values(pt.subset(src, [0]), layer)


def partial_response(model, template_row, var, n=50, bioclim=False):
    xs = np.linspace(template_row[var] * 0.9, template_row[var] * 1.1, n)
    rows = []
    for x in xs:
        row = template_row.copy()
        row[var] = x
        rows.append(row)
    df = pd.DataFrame(rows)
    ys = model.predict(df)
    return xs, ys
```

## Model fitting

```{code-cell} python
:tags: [sdm25]
m1 = smf.glm("pb ~ bio1 + bio5 + bio12", data=sdmdata,
             family=sm.families.Binomial()).fit()
m1.summary()

predictors_cols = [c for c in sdmdata.columns if c != "pb"]
formula = "pb ~ " + " + ".join(predictors_cols)
m2 = smf.glm(formula, data=sdmdata, family=sm.families.Binomial()).fit()
m2
```

Bioclim envelope using presence values only:

```{code-cell} python
:tags: [sdm26]
bc = BioclimEnvelope(presvals, cols=["bio1", "bio5", "bio12"])
bc.lo, bc.hi
```

## Model prediction

```{code-cell} python
:tags: [sdm27a]
pd_ = pd.DataFrame({
    "bio1": [40, 150, 200],
    "bio5": [60, 115, 290],
    "bio12": [600, 1600, 1700],
})
m1.predict(pd_)
```

```{code-cell} python
:tags: [sdm27b]
med = presvals.median()
xs, ys = partial_response(bc, med, "bio1", bioclim=True)
fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(xs, ys)
ax.set_xlabel("bio1")
ax.set_ylabel("suitability");
```

Raster prediction:

```{code-cell} python
:tags: [sdm27c]
p = predict_raster(m1, predictors, ["bio1", "bio5", "bio12"])
pt.plot(p, figsize=(9, 5));
```

## Model evaluation

Illustration with random normal scores:

```{code-cell} python
:tags: [sdm28]
np.random.seed(1)
p = np.random.normal(0.7, 0.3, 50)
a = np.random.normal(0.4, 0.4, 50)

fig, axes = plt.subplots(1, 2, figsize=(8, 3.5))
axes[0].plot(np.sort(p), "o", color="red", label="presence")
axes[0].plot(np.sort(a), "o", color="blue", label="absence")
axes[0].legend()
axes[1].boxplot([a, p], labels=["absence", "presence"]);
```

```{code-cell} python
:tags: [sdm29]
group = np.concatenate([np.ones(len(p)), np.zeros(len(a))])
comb = np.concatenate([p, a])
np.corrcoef(comb, group)[0, 1]
pa_evaluate(p, a)
```

Train/test split with Bioclim:

```{code-cell} python
:tags: [sdm41]
rng = np.random.default_rng(1)
samp = rng.choice(len(sdmdata), size=int(0.75 * len(sdmdata)), replace=False)
train = sdmdata.iloc[samp]
train_pres = train.loc[train["pb"] == 1, presvals.columns]
test = sdmdata.drop(index=samp)

bc = BioclimEnvelope(train_pres, cols=presvals.columns.tolist())
ptest = bc.predict(test.loc[test["pb"] == 1, presvals.columns])
atest = bc.predict(test.loc[test["pb"] == 0, presvals.columns])
pa_evaluate(ptest, atest)
```

## k-fold cross-validation

```{code-cell} python
:tags: [sdm42]
pres = sdmdata.loc[sdmdata["pb"] == 1, presvals.columns]
back = sdmdata.loc[sdmdata["pb"] == 0, presvals.columns]

k = 5
groups = np.arange(len(pres)) % k
rng = np.random.default_rng(2)
rng.shuffle(groups)
groups[:10], pd.Series(groups).value_counts()
```

```{code-cell} python
:tags: [sdm44]
aucs = []
for i in range(k):
    train = pres.loc[groups != i]
    test = pres.loc[groups == i]
    bc = BioclimEnvelope(train, cols=presvals.columns.tolist())
    p = bc.predict(test)
    a = bc.predict(back)
    aucs.append(pa_evaluate(p, a)["AUC"])
np.mean(aucs)
```

## Spatial sorting bias

The *R* tutorial demonstrates point-wise distance sampling with `dismo::ssb` and
`dismo::pwd_sample` to reduce spatial sorting bias (Hijmans, 2012). Those
functions are not yet ported to *tappa*; use the original *R* `dismo` package
for that workflow, or subsample background points with `grid_sample` as in the
[occurrence data](2-occdata) chapter.

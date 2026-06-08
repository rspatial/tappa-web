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

# Local statistics

## Introduction

This handout accompanies Chapter 8 in
[O'Sullivan and Unwin (2010)](http://www.wiley.com/WileyCDA/WileyTitle/productCd-0470288574.html).

## LISA

We compute some measures of local spatial autocorrelation on the Auckland
tuberculosis data.

```{code-cell} python
:tags: [loca1]
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import tappa as pt

DATA = Path("../../data").resolve()
ROSU = DATA / "rosu"

auck = pt.vect(str(ROSU / "auctb.gpkg"))
auck
```

Build a rook contiguity weight matrix:

```{code-cell} python
:tags: [locasp]
w = pt.adjacent(auck, type="rook", pairs=False, symmetrical=True)
w.shape
```

Compute Getis *G~i~*:

```{code-cell} python
:tags: [loca2]
tb = pt.vect_as_df(auck)["TB"].to_numpy(dtype=float)
Gi = pt.autocor(tb, w, method="gi")
Gi[:6]
```

```{code-cell} python
:tags: [loca3]
auck["Gi"] = Gi
grays = list(reversed([plt.cm.gray(v) for v in np.linspace(0, 1, 6)]))
pt.plot(auck, "Gi", col=grays, figsize=(6, 5));
```

*G~i~*\* (include the focal area in the computation):

```{code-cell} python
:tags: [loca4]
wstar = w.copy()
np.fill_diagonal(wstar, 1.0)
Gistar = pt.autocor(tb, wstar, method="gi*")
auck["Gistar"] = Gistar
pt.plot(auck, "Gistar", main="Gi*", col=grays, figsize=(6, 5));
```

Local average (spatially lagged mean):

```{code-cell} python
:tags: [loca6]
loc_mean = pt.autocor(tb, w, method="mean")
auck["loc_mean"] = loc_mean
pt.plot(auck, "loc_mean", main="Local mean", col=grays, figsize=(6, 5));
```

Local Moran's *I~i~*:

```{code-cell} python
:tags: [loca8]
Ii = pt.autocor(tb, w, method="locmor")
auck["Ii"] = Ii
pt.plot(auck, "Ii", main="Local Moran", col=grays, figsize=(6, 5));
```

Disease density is often more appropriate than raw counts:

```{code-cell} python
area = pt.expanse(auck)
auck["TBdens"] = 10000 * tb / area
```

## Geographically weighted regression

The *R* chapter uses the `spgwr` package. A fuller *tappa* example with
California precipitation is in the
[Local regression](../analysis/6-local_regression) chapter of the spatial
analysis tutorials.

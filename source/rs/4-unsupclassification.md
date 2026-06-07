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

# Unsupervised Classification

In this chapter we explore unsupervised classification. We use the k-means
algorithm to illustrate the general principle.

We follow the [NLCD 2011](https://www.mrlc.gov/nlcd2011.php) classification
scheme for a subset of the Central Valley, using a cloud-free
[Landsat 5](https://landsat.gsfc.nasa.gov/landsat-5/) composite with six bands.

```{code-cell} python
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import tappa as pt

DATA = Path("../../data").resolve()
RS = DATA / "rs"

landsat5 = pt.rast(str(RS / "centralvalley-2011LT5.tif"))
pt.set_names(landsat5, ["blue", "green", "red", "NIR", "SWIR1", "SWIR2"])
landsat5
```

**Question 1**: *Make a 3-band false-colour composite of `landsat5`.*

In unsupervised classification we use reflectance data without labelled
response pixels. The algorithm groups pixels with similar spectral
characteristics.

```{code-cell} python
nir = pt.subset(landsat5, [3])   # NIR band
red = pt.subset(landsat5, [2])   # red band
ndvi = (nir - red) / (nir + red)
```

## k-means classification

```{code-cell} python
:tags: [kmeans]
e = pt.ext(-121.807, -121.725, 38.004, 38.072)
ndvi = pt.crop(ndvi, e)
ndvi
```

```{code-cell} python
vals = pt.values(ndvi).ravel()
cells = np.arange(pt.ncell(ndvi))
nr = pd.DataFrame({"cell": cells, "ndvi": vals})
nr = nr[np.isfinite(nr["ndvi"])]
nr.head()
```

```{code-cell} python
:tags: [kmeansobject]
np.random.seed(99)
km = KMeans(n_clusters=10, max_iter=500, n_init=5, algorithm="lloyd")
km.fit(nr[["ndvi"]])
print("Cluster labels:", np.unique(km.labels_))
```

```{code-cell} python
:tags: [kmeansraster]
knr = pt.deepcopy(ndvi)
flat = pt.values(knr).ravel()
flat[np.isfinite(flat)] = km.labels_ + 1   # 1-based cluster IDs
knr = pt.set_values(knr, flat)
knr
```

```{code-cell} python
:tags: [kmeansplot]
mycolor = ["#fef65b", "#ff0000", "#daa520", "#0000ff", "#0000ff",
           "#00ff00", "#cbbeb5", "#c3ff5b", "#ff7373", "#00ff00"]

fig, axes = plt.subplots(1, 2, figsize=(9, 4))
pt.plot(ndvi, col=plt.cm.terrain(np.linspace(1, 0, 10)),
        ax=axes[0], main="Landsat-NDVI")
pt.plot(knr, ax=axes[1], main="Unsupervised classification",
        col=mycolor, type="classes");
plt.tight_layout();
```

**Question 2**: *Plot a true-colour image of `landsat5` for extent `e` next to
the k-means result and assign land-cover labels to clusters by visual
inspection (e.g. clusters 4 and 5 are water).*

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

# Raster algebra

Many operators and functions allow for simple and elegant raster algebra on
`SpatRaster` objects, including the normal algebraic operators such as `+`, `-`,
`*`, `/`, logical operators such as `>`, `>=`, `<`, `==`, `!=`, and functions
such as `pt.rast_abs()`, `pt.round_()`, `pt.sqrt()`, `pt.log()`, `pt.exp()`,
`pt.cos()`, `pt.rast_min()`, `pt.rast_max()`, `pt.rast_sum()`, and
`pt.rast_mean()`. In these expressions you can mix `SpatRaster` objects with
numbers, as long as the first argument is a `SpatRaster`.

```{code-cell} python
:tags: [raster-3a]
import numpy as np
import tappa as pt

rng = np.random.default_rng(0)

r = pt.rast(ncols=10, nrows=10)
r = pt.set_values(r, np.arange(1, pt.ncell(r) + 1, dtype=float))
s = r + 10
s = pt.sqrt(s)
s = s * r + 5
r = pt.set_values(r, rng.uniform(0, 1, pt.ncell(r)))
r = pt.round_(r)
r = r == 1
```

Boolean indexing to replace values (like R `s[r] <- -0.5`) is not yet supported
in *tappa*; use `pt.ifel()` or `pt.classify()` instead.

If you use multiple `SpatRaster` objects (in functions where this is relevant,
such as `pt.rast_min()`), these must have the same resolution and origin. The
origin of a `SpatRaster` object is the point closest to (0, 0) that you could
get if you moved from a corner of a `SpatRaster` object towards that point in
steps of the x and y resolution. Normally these objects would also have the same
extent, but if they do not, the returned object covers the spatial intersection
of the objects used.

When you use multiple multi-layer objects with different numbers of layers, the
"shorter" objects are recycled. For example, if you multiply a 4-layer object
(a1, a2, a3, a4) with a 2-layer object (b1, b2), the result is a four-layer
object (a1·b1, a2·b2, a3·b1, a4·b2).

```{code-cell} python
:tags: [raster-3c]
r = pt.rast(ncols=5, nrows=5)
r = pt.set_values(r, np.ones(pt.ncell(r)))
s = pt.rast([r, r + 1])
q = pt.rast([r, r + 2, r + 4, r + 6])
x = r + s + q
x
```

Summary functions (`pt.rast_min()`, `pt.rast_max()`, `pt.rast_mean()`,
`pt.rast_prod()`, `pt.rast_sum()`, `pt.rast_median()`, …) always return a
`SpatRaster` object. Perhaps this is not obvious when using functions like
`pt.rast_min()`, `pt.rast_sum()` or `pt.rast_mean()`.

```{code-cell} python
:tags: [raster-3d]
a = pt.rast_mean(r, s, 10)
b = pt.rast_sum(r, s)
st = pt.rast([r, s, a, b])
sst = pt.rast_sum(st)
sst
```

Use `pt.global_()` if instead of a `SpatRaster` you want a single number
summarising the cell values of each layer.

```{code-cell} python
:tags: [raster-3e]
pt.global_(st, "sum")
pt.global_(sst, "sum")
```

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

# Fundamentals

## Processes and patterns

This page accompanies Chapter 4 of
[O'Sullivan and Unwin (2010)](https://www.wiley.com/en-us/Geographic+Information+Analysis%2C+2nd+Edition-p-9780470288573),
translating the examples to *Python* with *tappa*.

```{code-cell} python
:tags: [imports]
from pathlib import Path
import math

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import binom, poisson
import tappa as pt

DATA = Path("../../data").resolve()
ROSU = DATA / "rosu"
```

Create values for the deterministic process:

\[
z = 2x + 3y
\]

```{code-cell} python
:tags: [detproc_numpy]
x = np.arange(8)
y = np.arange(8)
xx, yy = np.meshgrid(x, y)
xy = np.column_stack([xx.ravel(), yy.ravel()])
z = 2 * xy[:, 0] + 3 * xy[:, 1]
zm = z.reshape(8, 8)
xy[:5], z[:5]
```

The same calculation with a function:

```{code-cell} python
def detproc(x_vals, y_vals):
    return 2 * x_vals + 3 * y_vals


z2 = detproc(xy[:, 0], xy[:, 1]).reshape(8, 8)
np.allclose(zm, z2)
```

Plot values and contours (similar to OSU Figure 4.2).

```{code-cell} python
:tags: [p4-1]
fig, ax = plt.subplots(figsize=(6, 6))
ax.set_xlim(-0.5, 7.5)
ax.set_ylim(-0.5, 7.5)
for xi, yi, zi in zip(xy[:, 0], xy[:, 1], z):
    ax.text(xi, yi, f"{int(zi)}", ha="center", va="center")
cs = ax.contour(xx, yy, zm, colors="gray", linestyles="--")
ax.clabel(cs, fmt="%d")
ax.set_aspect("equal")
ax.set_xlabel("x")
ax.set_ylabel("y");
```

Now use raster objects and `pt.init()` for x/y coordinates.

```{code-cell} python
:tags: [p4-2]
r = pt.rast(extent=pt.ext(0, 7, 0, 7), ncols=8, nrows=8)
X = pt.init(r, "x")
Y = pt.init(r, "y")

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
pt.plot(X, ax=axes[0], main="x")
pt.plot(Y, ax=axes[1], main="y")
plt.tight_layout()
```

```{code-cell} python
Z = 2 * X + 3 * Y
pt.global_(Z, "range")
```

```{code-cell} python
:tags: [p4-3]
z_arr = np.asarray(pt.values(Z, mat=False)).reshape(Z.nrow(), Z.ncol(), order="F")
xg, yg = np.meshgrid(np.arange(Z.ncol()), np.arange(Z.nrow()))

fig, ax = plt.subplots(figsize=(6, 5))
im = ax.imshow(z_arr, origin="lower", cmap="viridis")
for j in range(z_arr.shape[0]):
    for i in range(z_arr.shape[1]):
        ax.text(i, j, f"{z_arr[j, i]:.0f}", ha="center", va="center", color="white", fontsize=8)
ax.contour(xg, yg, z_arr, colors="red", linewidths=1.6)
fig.colorbar(im, ax=ax, shrink=0.8)
ax.set_title("Deterministic process")
ax.set_xlabel("column")
ax.set_ylabel("row");
```

## Add stochasticity

Add a random term \(r \in \{-1, 1\}\):

\[
z = 2x + 3y + r
\]

```{code-cell} python
:tags: [p4-4]
rng = np.random.default_rng(987)
s = rng.choice(np.array([-1, 1]), size=pt.ncell(r), replace=True)
R = pt.set_values(pt.deepcopy(r), s)
pt.plot(R, figsize=(6, 5));
```

```{code-cell} python
:tags: [p4-5]
Zs = 2 * X + 3 * Y + R
zs_arr = np.asarray(pt.values(Zs, mat=False)).reshape(Zs.nrow(), Zs.ncol(), order="F")
xg, yg = np.meshgrid(np.arange(Zs.ncol()), np.arange(Zs.nrow()))

fig, ax = plt.subplots(figsize=(6, 5))
im = ax.imshow(zs_arr, origin="lower", cmap="viridis")
for j in range(zs_arr.shape[0]):
    for i in range(zs_arr.shape[1]):
        ax.text(i, j, f"{zs_arr[j, i]:.0f}", ha="center", va="center", color="white", fontsize=8)
ax.contour(xg, yg, zs_arr, colors="red", linewidths=1.6)
fig.colorbar(im, ax=ax, shrink=0.8)
ax.set_title("Deterministic + stochastic process")
ax.set_xlabel("column")
ax.set_ylabel("row");
```

```{code-cell} python
def make_pattern(base_raster, xr, yr, rng_obj):
    s = rng_obj.choice(np.array([-1, 1]), size=pt.ncell(base_raster), replace=True)
    sr = pt.set_values(pt.deepcopy(base_raster), s)
    return 2 * xr + 3 * yr + sr
```

```{code-cell} python
:tags: [p4-6]
rng = np.random.default_rng(777)
fig, axes = plt.subplots(2, 2, figsize=(9, 8))
for ax in axes.ravel():
    pattern = make_pattern(r, X, Y, rng)
    arr = np.asarray(pt.values(pattern, mat=False)).reshape(pattern.nrow(), pattern.ncol(), order="F")
    xg, yg = np.meshgrid(np.arange(pattern.ncol()), np.arange(pattern.nrow()))
    ax.imshow(arr, origin="lower", cmap="viridis")
    ax.contour(xg, yg, arr, colors="red", linewidths=1.2)
    ax.set_xticks([])
    ax.set_yticks([])
plt.tight_layout()
```

## Complete spatial randomness (CSR)

```{code-cell} python
:tags: [p4-7]
def csr(n, rmax=99, rng_obj=None):
    rng_obj = np.random.default_rng() if rng_obj is None else rng_obj
    x = rng_obj.uniform(0, rmax, n)
    y = rng_obj.uniform(0, rmax, n)
    return np.column_stack([x, y])
```

```{code-cell} python
:tags: [p4-8]
rng = np.random.default_rng(0)
fig, axes = plt.subplots(2, 2, figsize=(7, 7))
for ax in axes.ravel():
    pts = csr(50, rng_obj=rng)
    ax.scatter(pts[:, 0], pts[:, 1], s=20)
    ax.set_xlim(0, 99)
    ax.set_ylim(0, 99)
    ax.set_aspect("equal")
plt.tight_layout()
```

## Predicting patterns

Recreate Table 4.1 with a binomial model.

```{code-cell} python
events = np.arange(0, 11)
combinations = np.array([math.comb(10, k) for k in events], dtype=float)
prob1 = (1 / 8) ** events
prob2 = (7 / 8) ** (10 - events)
Pk = combinations * prob1 * prob2
tbl = pd.DataFrame(
    {
        "events": events,
        "combinations": combinations.astype(int),
        "prob1": prob1,
        "prob2": prob2,
        "Pk": Pk,
    }
)
tbl.round(8)
```

```{code-cell} python
Pk.sum()
```

```{code-cell} python
b = binom.pmf(np.arange(11), n=10, p=1 / 8)
np.round(b, 8)
```

Generate random points and 10x10 quadrats.

```{code-cell} python
rng = np.random.default_rng(1234)
xy_pts = np.column_stack([rng.uniform(0, 99, 50), rng.uniform(0, 99, 50)])
vxy = pt.vect(xy_pts)
vxy_df = pd.DataFrame({"v": np.ones(vxy.nrow(), dtype=int)})
vxy = pt.set_values(vxy, vxy_df)

rq = pt.rast(extent=pt.ext(0, 99, 0, 99), ncols=10, nrows=10)
quads = pt.as_polygons(rq)
```

```{code-cell} python
:tags: [p4-9]
ax = pt.plot(quads, border="gray", legend=False, figsize=(6, 5))
pt.points(vxy, ax=ax, col="red", pch=20);
```

Count points by quadrat.

```{code-cell} python
:tags: [p4-10]
p = pt.rasterize(vxy, rq, field="v", fun="count", background=0)
ax = pt.plot(p, figsize=(6, 5))
pt.lines(quads, ax=ax, col="gray")
pt.points(vxy, ax=ax, col="black", pch=20, s=10);
```

```{code-cell} python
:tags: [p4-12]
f = pt.freq(p)
f
```

```{code-cell} python
freq_df = f.copy()
freq_df.head()
```

Expected frequencies from the binomial distribution:

```{code-cell} python
:tags: [p4-13]
n = np.arange(0, 9)
prob = 1 / pt.ncell(rq)
size = 50
expected = binom.pmf(n, n=size, p=prob)

fig, ax = plt.subplots(figsize=(5, 4))
ax.plot(n, expected, marker="x", color="blue", linestyle="none", markersize=10)
ax.set_xlabel("k")
ax.set_ylabel("P(k)");
```

```{code-cell} python
:tags: [p4-15]
obs = freq_df["count"].to_numpy() / freq_df["count"].sum()
exp = expected[: len(obs)]
kvals = np.arange(len(obs))

w = 0.4
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.bar(kvals - w / 2, obs, width=w, color="red", label="Observed")
ax.bar(kvals + w / 2, exp, width=w, color="blue", label="Expected")
ax.set_xlabel("k")
ax.set_ylabel("Relative frequency")
ax.legend();
```

Poisson approximation:

```{code-cell} python
:tags: [p4-16]
poisexp = poisson.pmf(np.arange(0, 9), mu=50 / 100)
fig, ax = plt.subplots(figsize=(5, 4))
ax.scatter(expected[:9], poisexp, s=50)
ax.plot([0, max(expected[:9])], [0, max(expected[:9])], color="gray")
ax.set_xlabel("Binomial expectation")
ax.set_ylabel("Poisson expectation");
```

## Random lines

```{code-cell} python
:tags: [p4-rlines1]
def random_line_in_rectangle(xmn=0.0, xmx=0.8, ymn=0.0, ymx=0.6, return_xy=False, rng_obj=None):
    rng_obj = np.random.default_rng() if rng_obj is None else rng_obj
    x = rng_obj.uniform(xmn, xmx)
    y = rng_obj.uniform(ymn, ymx)
    angle = rng_obj.uniform(0, 360)

    if np.isclose(angle, 90.0):
        if return_xy:
            return np.array([[x, ymn], [x, y], [x, ymx]])
        return ymx - ymn

    tang = np.tan(np.deg2rad(angle))
    x1 = max(xmn, min(xmx, x - y / tang))
    x2 = max(xmn, min(xmx, x + (ymx - y) / tang))
    y1 = max(ymn, min(ymx, y - (x - x1) * tang))
    y2 = max(ymn, min(ymx, y + (x2 - x) * tang))

    if return_xy:
        return np.array([[x1, y1], [x, y], [x2, y2]])
    return float(np.hypot(x2 - x1, y2 - y1))
```

```{code-cell} python
:tags: [p4-rlines2]
rng = np.random.default_rng(999)
fig, ax = plt.subplots(figsize=(6, 4.5))
ax.set_xlim(0, 0.8)
ax.set_ylim(0, 0.6)
for i in range(4):
    xy_line = random_line_in_rectangle(return_xy=True, rng_obj=rng)
    ax.plot(xy_line[:, 0], xy_line[:, 1], lw=2)
ax.set_aspect("equal");
```

```{code-cell} python
:tags: [p4-rlines3]
rng = np.random.default_rng(999)
lengths = np.array([random_line_in_rectangle(rng_obj=rng) for _ in range(10_000)])
fig, ax = plt.subplots(figsize=(6, 4))
ax.hist(lengths, bins=np.arange(0, 1.01, 0.01), density=True)
ax.set_xlabel("Line length")
ax.set_ylabel("Density");
```

## Sitting comfortably?

```{code-cell} python
:tags: [p4-seats]
rng = np.random.default_rng(0)
x = np.array([abs(np.diff(rng.choice(np.arange(1, 5), size=2, replace=False))[0]) for _ in range(10_000)])
np.mean(x == 2)
```

## Random areas

Random chessboard:

```{code-cell} python
:tags: [p4-19]
rchess = pt.rast(extent=pt.ext(0, 1, 0, 1), ncols=8, nrows=8)
rchess_pol = pt.as_polygons(rchess)


def chess(r0, rng_obj):
    vals = rng_obj.choice(np.array([-1, 1]), size=pt.ncell(r0), replace=True)
    return pt.set_values(pt.deepcopy(r0), vals)
```

```{code-cell} python
:tags: [p4-20]
rng = np.random.default_rng(0)
fig, axes = plt.subplots(2, 2, figsize=(7, 7))
for ax in axes.ravel():
    board = chess(rchess, rng)
    pt.plot(board, ax=ax, col=["black", "white"], legend=False)
    pt.lines(rchess_pol, ax=ax, col="gray")
plt.tight_layout()
```

Random field:

```{code-cell} python
:tags: [p4-21]
rf = pt.rast(extent=pt.ext(0, 1, 0, 1), ncols=20, nrows=20)
rng = np.random.default_rng(42)
rf = pt.set_values(rf, rng.normal(0, 2, pt.ncell(rf)))
rf_arr = np.asarray(pt.values(rf, mat=False)).reshape(rf.nrow(), rf.ncol(), order="F")
xg, yg = np.meshgrid(np.arange(rf.ncol()), np.arange(rf.nrow()))

fig, ax = plt.subplots(figsize=(6, 5))
im = ax.imshow(rf_arr, origin="lower", cmap="viridis")
ax.contour(xg, yg, rf_arr, colors="black", linewidths=0.8)
fig.colorbar(im, ax=ax, shrink=0.8);
```

Focal smoothing to add autocorrelation:

```{code-cell} python
:tags: [p4-22]
w = np.full((3, 3), 1 / 9, dtype=float)
ra = pt.focal(rf, w=w, fun="mean", na_rm=True)
ra = pt.focal(ra, w=w, fun="mean", na_rm=True)
pt.plot(ra, figsize=(6, 5));
```

## Questions

1. *Use these examples to write a script for the "thought exercise to fix ideas" (OSU p.98). Use a function to generate random numbers and avoid explicit loops where possible.*
2. *Rewrite the CSR example with a normal distribution instead of uniform, and compare generated vs expected patterns.*
3. *How could you test whether a real chessboard-like pattern is generated by an independent random process?*
4. *Can you explain the shape of the random line-length distribution in a rectangle?*

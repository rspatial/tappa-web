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

# Parallelization

## Introduction

Many computations on `SpatRaster` (and to a lesser extent `SpatVector`) objects
are slow because of the large (file) size of the raster. The computations are
also embarrassingly parallel: the same operation is applied to many cells, many
features, or many tiles, and the work for each piece is independent. There are
several ways to take advantage of multiple cores when working with *tappa*, and
the right one depends on (a) the nature of the operation, (b) whether you are on
a single computer or on a cluster, and (c) whether the data are in memory, in a
single file, or scattered across many files.

In some cases parallelization is essential and easy — for example when processing
many files on a cluster, or for tasks that are repeated often enough that the
setup cost is amortised. In other cases the gain is marginal and not worth the
effort, because setting up a parallel workflow can take a while, introduce subtle
errors, and complicate debugging. It pays to first time a single-threaded run,
estimate the best-case speed-up, and only then decide whether to parallelize.

This chapter discusses the available approaches and their trade-offs for
parallelization support in *tappa*.

## The constraint: terra objects hold a C++ pointer

`SpatRaster`, `SpatVector`, `SpatRasterDataset`, and related classes are *thin*
Python objects: each holds a pointer to an underlying C++ object that lives in
the memory of the process that created it. As a consequence, these objects
**cannot be pickled** or sent to worker processes with `multiprocessing` /
`concurrent.futures` directly. After pickling, the pointer would be invalid in the
worker's memory.

If you try, the worker either errors out or returns nonsense:

```python
# do not run this — it will fail
import tappa as pt
from multiprocessing import Pool

r = pt.rast("elev.tif")
with Pool(2) as pool:
    pool.map(lambda i: pt.global_(r, "mean"), range(2))
```

This is not a show stopper. The next sections describe strategies to work around
this limitation.

## Strategy 1 — pass filenames, open them on the worker

When the data live in a file (GeoTIFF, NetCDF, …) the cheapest "serialization"
is the filename. Each worker creates its own `SpatRaster` from the file(s) it
gets. Only the grid cells that are actually needed by a worker are read from
disk.

```python
from concurrent.futures import ProcessPoolExecutor
import tappa as pt

fname = "elev.tif"

def worker_mean(_i, f):
    r = pt.rast(f)
    return pt.global_(r, "mean")

with ProcessPoolExecutor(max_workers=4) as ex:
    results = list(ex.map(worker_mean, range(4), [fname] * 4))
```

This pattern is clearly better whenever:

- the dataset is too large to comfortably fit in worker memory,
- you have many files (one per worker, or one per task), or
- you are on an HPC cluster where all nodes can see the same shared file system.

In *terra* for *R*, `wrap()` / `unwrap()` provide another serialization path.
Those functions are **not yet available** in *tappa*.

## Strategy 2 — partition by tiles

*tappa* facilitates this approach with `pt.tile_apply()`.

In its simplest form:

```{code-cell} python
:tags: [tile-apply]
from pathlib import Path
import tappa as pt

DATA = Path("../../data").resolve()
r = pt.rast(str(DATA / "elev.tif"))
out = pt.tile_apply(r, lambda x: x * 2)
out
pt.global_(r * 2, "range")
```

splits `r` into a small number of tiles, applies `fun` to each (with a read
window set under the hood, so no values are copied), writes every per-tile
result to a temporary GeoTIFF, and returns a `SpatRaster` backed by a VRT that
stitches those files together. No cell values cross the worker boundary; the
parent process only sees filenames.

You can pass `cores=` to run tiles in parallel, and `buffer=` for neighbourhood
operations like `pt.focal()` so that cells near tile edges see the correct
neighbours:

```python
out = pt.tile_apply(
    r,
    lambda x: pt.focal(x, w=11, fun="mean"),
    buffer=5,
    cores=4,
)
```

Pass `filename=` to materialise the assembled raster on disk in one step.

## Strategy 3 — exchange raw values

For some workflows it is simplest to extract the cell values as a plain *NumPy*
array, send those numbers to the workers, do the computation, ship the numbers
back, and put them back in a `SpatRaster` on the parent.

```python
import numpy as np
import tappa as pt

r = pt.rast("elev.tif")
v = pt.values(r)
chunks = np.array_split(np.arange(v.shape[0]), 4)

def sqrt_chunk(idx, mat):
    return np.sqrt(mat[idx, :])

parts = [sqrt_chunk(i, v) for i in chunks]
out = pt.set_values(pt.deepcopy(r), np.vstack(parts).ravel())
```

For rasters that do *not* fit in memory the same idea applies, but you process
one block at a time using `pt.write_start()` / `pt.write_values()` /
`pt.write_stop()`.

## Function-level parallelism: the `cores` argument

Some functions in *terra* take a `cores` argument and use `parallel::makeCluster`
under the hood (`app`, `tapp`, `lapp`, `predict`, `interpolate`, `aggregate`,
`focal`, …). In *tappa*, `pt.tile_apply(..., cores=)` is the main built-in
option for spatial tiling. Per-call `cores=` on `pt.app()` / `pt.focal()` is
not yet wired up the same way as in *terra*.

## Within-process parallelism: TBB

A growing number of *terra*'s C++ code paths are parallelized internally with
[Intel TBB](https://github.com/oneapi-src/oneTBB). When TBB is available at
build time, some kernels (parts of `arith`, distance calculations, `focal` with
built-in functions such as `"mean"` and `"sum"`) can use multiple threads inside
a single process. Control this through `SpatOptions` (for example
`parallel=True`) where your *tappa* build exposes those options.

## Single computer vs. HPC cluster

On a single machine, prefer within-process TBB when supported, then
`pt.tile_apply(..., cores=)`, then filename-based `ProcessPoolExecutor` workers.

On an HPC cluster, combine **two levels** of parallelism:

- **Across nodes**: one Python process per node (or per task), launched via the
  scheduler (SLURM, PBS, …), partitioning input filenames or tiles across array
  jobs.
- **Within node**: TBB and/or `pt.tile_apply(..., cores=)` for tiled
  neighbourhood operations.

The most reliable inter-node "serialization" of raster data is **the filename on
a shared file system**. Build the `SpatRaster` on each node from the path; do
not ship raster values across the network if the file is reachable.

```python
# slurm_array.py — one task per tile index
import sys
import tappa as pt

i = int(sys.argv[1])
r = pt.rast("/shared/dem.tif")
# window/tile setup here
out = pt.focal(r, w=11, fun="mean")
pt.write(out, f"/shared/out/tile_{i:03d}.tif", overwrite=True)
```

Then mosaic the tiles in a final, single-process step with `pt.merge()` or
`pt.mosaic()`.

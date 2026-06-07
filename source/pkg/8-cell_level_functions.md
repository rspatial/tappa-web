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

# Cell-level functions

## Introduction

The cell number is an important concept in *tappa*. Raster data can be thought of
as a matrix, but in a `SpatRaster` it is more commonly treated as a vector.
Cells are numbered from the upper-left cell to the upper-right cell and then
continuing on the left side of the next row, and so on until the last cell at
the lower-right side of the raster. In *tappa* cell indices are **0-based**
(unlike *terra* in *R*, which uses 1-based cell numbers). There are several
helper functions to determine the column or row number from a cell and vice
versa, and to determine the cell number for x, y coordinates and vice versa.

```{code-cell} python
:tags: [raster-15]
import tappa as pt

r = pt.rast(ncols=36, nrows=18)
pt.ncol(r), pt.nrow(r), pt.ncell(r)
pt.row_col_from_cell(r, [99])
pt.cell_from_row_col(r, 4, 4)
pt.xy_from_cell(r, [99])
pt.cell_from_xy(r, 0.0, 0.0)
pt.col_from_x(r, 0.0)
pt.row_from_y(r, 0.0)
```

## Accessing cell values

Cell values can be accessed with several methods. Use `pt.values()` to get all
values or a subset such as a single row; and `pt.values_block()` to read a block
(rectangle) of cell values.

```{code-cell} python
:tags: [raster-20]
from pathlib import Path
import tappa as pt

DATA = Path("../../data").resolve()
r = pt.rast(str(DATA / "meuse.tif"))
v = pt.values(r)
v[707:712]
```

You can also read values using cell numbers or coordinates (xy) using the
`pt.extract()` method.

```{code-cell} python
:tags: [raster-21]
import numpy as np

cells = pt.cell_from_row_col(r, 32, list(range(34, 40)))
cells
xy = pt.xy_from_cell(r, cells)
xy
pt.extract(r, xy, ID=False)
```

You can also extract values using `SpatVector` polygons or lines. The default
approach for extracting raster values with polygons is that a polygon has to
cover the centre of a cell for the cell to be included. However, you can use
`weights=True`, in which case you get, apart from the cell values, the
percentage of each cell that is covered by the polygon, so that you can apply,
e.g., a "50% area covered" threshold, or compute an area-weighted average.

In the case of lines, any cell that is crossed by a line is included. For lines
and points, a cell that is only "touched" is included when it is below or to the
right (or both) of the line segment / point (except for the bottom row and
right-most column).

In addition, you can use `pt.subset()` and `pt.set_values()` to read and replace
values in a `SpatRaster` object. If you replace values in a `SpatRaster` based
on a file, the connection to that file is lost (because it now is different from
that file). Setting raster values for very large files will be very slow with
this approach as each time a new (temporary) file, with all the values, is
written to disk.

Note that in the above examples values are retrieved using cell numbers. That
is, a raster is represented as a (one-dimensional) vector. Values can also be
inspected using a (two-dimensional) matrix notation via `pt.as_matrix()`. As for
*NumPy* arrays, the first index represents the row number, the second the column
number (both 0-based).

Accessing values through matrix-style indexing should be avoided inside
functions as it is less efficient than accessing values via `pt.values()`.

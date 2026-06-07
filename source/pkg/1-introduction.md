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

# The tappa package

This vignette describes the *Python* package *tappa*. A raster is a spatial
(geographic) data structure that divides a region into rectangles called
"cells" (or "pixels") that can store one or more values for each of these
cells. Such a data structure is also referred to as a "grid" and is often
contrasted with "vector" data that is used to represent points, lines, and
polygons.

*tappa* has functions for creating, reading, manipulating, and writing raster
data. The package provides, among other things, general raster data manipulation
functions that can easily be used to develop more specific functions. For
example, there are functions to read a chunk of raster values from a file or to
convert cell numbers to coordinates and back. The package also implements raster
algebra and most functions for raster data manipulation.

A notable feature of *tappa* (inherited from *terra*) is that it can work with
raster datasets that are stored on disk and are too large to be loaded into
memory (RAM). The package can work with large files because the objects it
creates from these files only contain information about the structure of the
data — such as the number of rows and columns, the spatial extent, and the
filename — but it does not attempt to read all the cell values into memory. In
computations with these objects, data is processed in chunks. If no output
filename is specified to a function, and the output raster is too large to keep
in memory, the results are written to a temporary file.

To understand what is covered in this vignette, you should know the basics of
*Python*. See the [official tutorial](https://docs.python.org/3/tutorial/) and
the [Scientific Python lectures](https://lectures.scientific-python.org/) for
*NumPy*, *pandas*, and *Matplotlib*.

In the next section, some general aspects of the design of *tappa* are
discussed, notably the structure of the main classes and what they represent.
The use of the package is illustrated in subsequent sections. *tappa* has a
large number of functions; not all of them are discussed here, and those that
are discussed are mentioned only briefly. See the
[API reference](https://rspatial.org/tappa/api) for more information on
individual functions.

## Example data

Several chapters use small GeoTIFF files from the *terra* package examples.
`elev.tif` and `logo.tif` ship with this tutorial site; `meuse.tif` is
downloaded on first use.

```{code-cell} python
from pathlib import Path
import urllib.request

DATA = Path("../../data").resolve()
BASE = "https://github.com/rspatial/terra/raw/master/inst/ex"

for name in ("meuse.tif",):
    dest = DATA / name
    if not dest.exists():
        print(f"downloading {name} …")
        urllib.request.urlretrieve(f"{BASE}/{name}", dest)
```

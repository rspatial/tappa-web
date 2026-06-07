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

# Reading and writing spatial data

## Introduction

Reading and writing spatial data is complicated by the fact that there are
many different file formats. However, there are a few formats that are most
common, and we discuss them here.

The example data used below ships with this tutorial. We resolve their paths
relative to the notebook's working directory:

```{code-cell} python
from pathlib import Path
import tappa as pt

DATA = Path("../../data").resolve()
DATA
```

## Vector files

The `shapefile` is the most commonly used file format for vector data. If you
are not familiar with this format, the important thing to understand is that a
[shapefile](https://en.wikipedia.org/wiki/Shapefile) is really a set of at
least three (ideally four) files with the same name but different extensions.
For shapefile `x` you *must* have, in the same directory, these files:
`x.shp`, `x.shx`, `x.dbf`, and ideally also `x.prj`.

It is easy to read and write such files.

### Reading

```{code-cell} python
filename = DATA / "lux.shp"
filename.name
```

Now we use `pt.vect()` to read the file.

```{code-cell} python
s = pt.vect(str(filename))
s
```

`pt.vect()` returns `SpatVector` objects. It is important to recognise the
difference between this type of *Python* object (`SpatVector`) and the file
("shapefile") that was used to create it. Thus, you should never say "I have
a shapefile in Python", say "I have a `SpatVector` of polygons in Python"
(and in some cases you can add "created from a shapefile"). The shapefile is
one of many file formats for vector data.

### Writing

You can write new files using `pt.write()`. Use ``overwrite=True`` to
overwrite an existing file.

```{code-cell} python
out_path = "shp_test.shp"
pt.write(s, out_path, overwrite=True)
```

To remove the file again you can use `pathlib.Path.unlink()` (be careful!).
Shapefiles consist of several sidecar files; remove them together:

```{code-cell} python
for f in Path(".").glob("shp_test.*"):
    f.unlink()
```

## Raster files

*tappa* can read and write several raster file formats.

### Reading raster data

```{code-cell} python
f = DATA / "logo.tif"
f.name
```

```{code-cell} python
r = pt.rast(str(f))
r
```

Note that `r` is a `SpatRaster` of three layers ("bands"). We can subset it
to get a single layer.

```{code-cell} python
r2 = pt.subset(r, [1])   # 0-based: layer 2
r2
```

The same approach holds for other raster file formats, including GeoTIFF,
NetCDF, Imagine and ESRI Grid formats.

### Writing raster data

Use `pt.write()` to write raster data. You must provide a `SpatRaster`
and a filename. The file format will be guessed from the filename extension.
If that does not work you can pass an explicit `filetype="GTiff"` argument.
Note `overwrite=True` and see ``help(pt.write)`` for more arguments,
such as `datatype="INT2S"` to set a specific data type.

```{code-cell} python
x = pt.write(r, "test_output.tif", overwrite=True)
x
```

```{code-cell} python
:tags: [remove-output]
Path("test_output.tif").unlink(missing_ok=True)
```

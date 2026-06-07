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

# Classes

The package is built around a number of classes, of which `SpatRaster` and
`SpatVector` are the most important.

## SpatRaster

A `SpatRaster` represents multi-layer (multi-variable) raster data. A
`SpatRaster` object stores fundamental parameters that describe it. These
include the number of columns and rows, the coordinates of its spatial extent
("bounding box"), and the coordinate reference system (the "map projection"). In
addition, a `SpatRaster` can store information about the file(s) in which the
raster cell values are stored (if there are such files) — as raster cell values
can also be held in memory.

## SpatVector

A `SpatVector` represents "vector" data: points, lines or polygon geometries
and their tabular attributes.

## SpatExtent

`SpatExtent` is the class for a spatial extent (bounding box). In *tappa* you
can create one with `pt.ext(xmin, xmax, ymin, ymax)` or obtain it from a raster
or vector with `pt.ext(x)`.

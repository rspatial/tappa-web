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

# Miscellaneous

## Session options

There are a number of session options that influence reading and writing files.
In *terra* for *R* these are set with `terraOptions()` and can be saved between
sessions. In *tappa* you create a `SpatOptions` object with `pt.spat_options()`
and pass it to functions that accept a `filename` / options argument, or set
attributes on the object before I/O.

You probably should not change the default values unless you have a pressing
need to do so. You can, for example, set the directory where temporary files are
written, and set your preferred default file format and data type. Some of these
settings can be overwritten by arguments to individual functions (`filename`,
`datatype`, `overwrite`). For generic functions like `pt.rast_mean()`, `+`, and
`pt.sqrt()`, the result may be written to a temporary file when it is too large
to hold in memory; those paths follow the session options.

The options `chunksize` and `maxmemory` determine the maximum size (in number of
cells) of a single chunk of values that is read or written in chunk-by-chunk
processing of very large files.

```{code-cell} python
:tags: [raster-119]
import tappa as pt

opt = pt.spat_options()
opt
```

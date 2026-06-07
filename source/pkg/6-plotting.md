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

# Plotting

Several functions have been implemented for `SpatRaster` objects to create maps
and other plot types. Use `pt.plot()` to create a map of a `SpatRaster` object.
When `pt.plot()` is used with a multi-layer `SpatRaster`, all layers are plotted
(up to 16), unless the layers desired are indicated with an additional argument.
You can add vector type spatial data (points, lines, polygons) with
`pt.points()`, `pt.lines()`, and `pt.polys()`.

Multi-layer `SpatRaster`s can be plotted as a single RGB image when the layers
are declared as RGB channels (red, green, blue); see `pt.plot_rgb()` and
`SpatRaster.setRGB()`.

```{code-cell} python
:tags: [raster-20a]
from pathlib import Path
import matplotlib.pyplot as plt
import tappa as pt

DATA = Path("../../data").resolve()
b = pt.rast(str(DATA / "logo.tif"))
pt.nlyr(b)
b.getRGB()
pt.plot(b, figsize=(5, 4));
```

You can also use other plotting functions with a `SpatRaster` as argument,
including `pt.hist()` and `pt.density()`. For interactive maps, consider
[leafmap](https://leafmap.org/) or other *Matplotlib*-based extensions.

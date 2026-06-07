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

# Writing files

## File format

*tappa* can read and write most raster and vector file formats via the GDAL
library. Use `pt.write()` to write a `SpatRaster` or `SpatVector` to disk.

```{code-cell} python
from pathlib import Path
import tappa as pt

DATA = Path("../../data").resolve()
r = pt.rast(str(DATA / "logo.tif"))
out = DATA / "pkg_logo_copy.tif"
pt.write(r, str(out), overwrite=True)
pt.rast(str(out))
```

```{code-cell} python
out.unlink(missing_ok=True)
```

For NetCDF files, use `pt.write_cdf()` when that function is available for your
build; otherwise export through GDAL with an appropriate driver name.

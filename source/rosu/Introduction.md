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

# Introduction

These pages accompany the book *Geographic Information Analysis* by David
O'Sullivan and David J. Unwin
[(2nd Edition, 2010)](http://www.wiley.com/WileyCDA/WileyTitle/productCd-0470288574.html)
— hereinafter referred to as "OSU".

OSU is an excellent and very accessible introduction to spatial data analysis,
but it does not show how to practically implement the methods that are
discussed. Many of the numerical examples in the text are implemented here, and
some of the other techniques discussed are illustrated as well. We hope that
this allows readers of OSU to get a more hands-on way to understand the material
covered, and to apply such approaches in their own work. Throughout these pages
reference is made to OSU, and no attempt is made to explain the material to
those who have no access to OSU.

The examples are implemented with *Python* and [*tappa*](https://github.com/rspatial/tappa).
If you are new to *Python*, first go through the
[spatial data manipulation](../spatial/index) tutorials.

## Data

Most chapter data come from the *R* [rspat](https://github.com/rspatial/rspat)
package. For *tappa* we ship GeoTIFF/GPKG/CSV exports under `web/tappa/data/rosu/`.
City, crime, and county boundaries also live in `web/tappa/data/`.

```{code-cell} python
from pathlib import Path

DATA = Path("../../data").resolve()
ROSU = DATA / "rosu"
ROSU.mkdir(parents=True, exist_ok=True)
DATA, ROSU
```

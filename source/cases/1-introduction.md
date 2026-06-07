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

This is a (still very small) collection of case studies in spatial data analysis
with *Python* and *tappa*. It is part of the
[Spatial Data Science with Python](https://rspatial.org/tappa) tutorials — the
*tappa* port of the
[Introduction to Spatial Data Analysis with *R*](https://rspatial.org/terra)
resources.

The chapters in this section are self-contained workflows that build on the
[spatial data manipulation](../spatial/index) material:

1. **Coastline length** — measuring a coastline with rulers of different length
   and estimating its fractal dimension.
2. **Species distribution** — summarising and mapping wild potato occurrence
   records across the Americas.

## Data

Case-study data live under `web/tappa/data/cases/`. The wild potato CSV and
Americas country polygons are bundled with the tutorial site. The United Kingdom
coastline (GADM) is downloaded on first use in chapter 2.

```{code-cell} python
from pathlib import Path

DATA = Path("../../data").resolve()
CASES = DATA / "cases"
CASES.mkdir(parents=True, exist_ok=True)

for name in ("wildpot.csv", "pt_countries.gpkg"):
    path = CASES / name
    print(name, "OK" if path.exists() else "missing — see chapter 3")
```

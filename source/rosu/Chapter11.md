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

# Map overlay

This page accompanies Chapter 11 in
[O'Sullivan and Unwin (2010)](https://www.wiley.com/en-us/Geographic+Information+Analysis%2C+2nd+Edition-p-9780470288573).

```{code-cell} python
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import tappa as pt

DATA = Path("../../data").resolve()
ROSU = DATA / "rosu"
DATA, ROSU
```

## Read data

```{code-cell} python
counties = pt.vect(str(DATA / "counties.gpkg"))
city = pt.vect(str(DATA / "city.gpkg"))
crime = pt.vect(str(DATA / "crime.gpkg"))
rail = pt.vect(str(ROSU / "yolo-rail.gpkg"))
parks = pt.vect(str(ROSU / "parks.gpkg"))
elev = pt.rast(str(ROSU / "elevation.tif"))

counties, city, crime, rail, parks, elev
```

## Selection by attribute

Select Yolo county by name.

```{code-cell} python
yolo = counties[counties["NAME"] == "Yolo"]
yolo
```

```{code-cell} python
fig, ax = plt.subplots(figsize=(6, 6))
pt.plot(counties, ax=ax, col="lightgray", border="gray", legend=False)
pt.plot(yolo, ax=ax, col="none", border="red", linewidth=2, legend=False);
```

## Intersection and buffer

Use Teale Albers (same CRS string as in the R version).

```{code-cell} python
TA = ("+proj=aea +lat_1=34 +lat_2=40.5 +lat_0=0 +lon_0=-120 +x_0=0 "
      "+y_0=-4000000 +datum=WGS84 +units=m")

counties_ta = pt.project(counties, TA)
yolo_ta = pt.project(yolo, TA)
city_ta = pt.project(city, TA)
rail_ta = pt.project(rail, TA)
parks_ta = pt.project(parks, TA)
elev_ta = pt.project(elev, TA)

pt.crs(yolo_ta)
```

Check which county (or counties) Davis intersects.

```{code-cell} python
davis_cent = pt.centroids(city_ta)
i = np.where(pt.relate(davis_cent, counties_ta, "intersects"))[1]
counties_ta["NAME"][i]
```

Intersect city and counties directly.

```{code-cell} python
city_counties = pt.intersect(city_ta, counties_ta)
city_counties["area"] = pt.expanse(city_counties)
pt.vect_as_df(city_counties)
```

Railroad segments inside the city, then a 500 m buffer around rail and clipped
to city limits.

```{code-cell} python
davis_rail = pt.intersect(rail_ta, city_ta)

buf = pt.buffer(rail_ta, width=500)
buf = pt.aggregate(buf)
rail_buf = pt.intersect(buf, city_ta)

fig, ax = plt.subplots(figsize=(6, 6))
pt.plot(city_ta, ax=ax, col="lightgray", border="gray", legend=False)
pt.plot(rail_buf, ax=ax, col="lightblue", border="lightblue", legend=False)
pt.plot(rail_ta, ax=ax, col="blue", linewidth=1.5, legend=False)
pt.plot(davis_rail, ax=ax, col="red", linewidth=2.5, legend=False);
```

Percent of city area within 500 m of rail:

```{code-cell} python
100 * pt.expanse(rail_buf) / pt.expanse(city_ta)
```

## Proximity and Voronoi

Which park is closest to rail, and which is furthest?

```{code-cell} python
d = pt.distance(parks_ta, rail_ta)
dmin = np.asarray(d).min(axis=1)
parks_ta["railDist"] = dmin

i_far = int(np.argmax(dmin))
i_near = int(np.argmin(dmin))
pt.vect_as_df(parks_ta).iloc[[i_near, i_far], :]
```

```{code-cell} python
fig, ax = plt.subplots(figsize=(6, 6))
pt.plot(city_ta, ax=ax, col="lightgray", border="lightgray", legend=False)
pt.plot(rail_ta, ax=ax, col="blue", linewidth=2, legend=False)
pt.plot(parks_ta, ax=ax, col="darkgreen", border="darkgreen", legend=False)
pt.plot(parks_ta[i_far], ax=ax, col="red", border="red", legend=False)
pt.plot(parks_ta[i_near], ax=ax, col="orange", border="orange", legend=False);
```

Voronoi polygons from park centroids, clipped to the city.

```{code-cell} python
centr = pt.centroids(parks_ta)
voro = pt.voronoi(centr)
voro_city = pt.intersect(voro, city_ta)

fig, ax = plt.subplots(figsize=(7, 6))
pt.plot(voro_city, ax=ax, border="red", col="none", legend=False)
pt.plot(parks_ta, ax=ax, col="green", border="green", legend=False)
pt.points(centr, ax=ax, col="black", s=8);
```

## Raster data: crop, mask, extract

Extract elevation values for Yolo county.

```{code-cell} python
vals = pt.extract(elev_ta, yolo_ta, ID=False)
vals_arr = np.asarray(vals).ravel()
vals_arr = vals_arr[np.isfinite(vals_arr)]

fig, ax = plt.subplots(figsize=(6, 4))
ax.hist(vals_arr, bins=30)
ax.set_title("Elevation in Yolo county")
ax.set_xlabel("Elevation")
ax.set_ylabel("Frequency");
```

Crop to Yolo extent, then mask to Yolo boundary.

```{code-cell} python
yalt = pt.crop(elev_ta, yolo_ta)
ymask = pt.mask(yalt, yolo_ta)

fig, ax = plt.subplots(figsize=(7, 5))
pt.plot(ymask, ax=ax, legend=True)
pt.plot(yolo_ta, ax=ax, col="none", border="black", legend=False);
```

## Exercise

Travel by train in Yolo county and identify where to leave the rail line to
reach "hilly" terrain quickly.

Use elevation and slope to define a hilliness score, then:

1. Compute distance from rail to all candidate locations.
2. Plot distance versus hilliness.
3. Map a plausible get-off point on rail and a target hilly location.
4. Plot an elevation and slope profile along the straight-line path.

Bonus: build a least-cost path (e.g. slope-based travel cost) instead of a
straight-line route.

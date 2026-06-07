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

This section provides a short introduction to satellite data analysis with
*Python* and *tappa*. Before reading this you should first learn the
[basics of spatial data manipulation](../spatial/index).

Getting satellite images for a specific project remains a challenging task.
You have to find data that is suitable for your objectives, and that you can
get access to. Important properties to consider while searching remotely sensed
(satellite) data include:

1. [Spatial resolution](http://www.nrcan.gc.ca/node/9407) — the size of the grid cells
2. [Temporal resolution](http://www.seos-project.eu/modules/remotesensing/remotesensing-c03-p05.html) — return time or frequency of data collection; availability of historical images
3. [Spectral resolution](http://www.seos-project.eu/modules/remotesensing/remotesensing-c03-p03.html) — wavelengths measured
4. Radiometric resolution (sensor sensitivity; ability to measure small differences)
5. Quality issues, such as cloud cover or artifacts (see [Landsat ETM+](http://landsat.usgs.gov/products_slcoffbackground.php))

There are numerous sources of remotely sensed data from satellites. Generally,
very high spatial resolution data is available as commercial products. Lower
resolution data is freely available from [NASA](https://www.nasa.gov/),
[ESA](https://www.esa.int/), and other organizations. In this tutorial we use
freely available [Landsat 8](https://landsat.gsfc.nasa.gov/landsat-8/),
[Landsat 7](https://landsat.gsfc.nasa.gov/landsat-7/),
[Landsat 5](https://landsat.gsfc.nasa.gov/landsat-5/),
[Sentinel](https://earth.esa.int/web/sentinel/user-guides/sentinel-2-msi), and
[MODIS](https://lpdaac.usgs.gov/dataset_discovery/modis/modis_products_table)
data. The [Landsat program](https://landsat.gsfc.nasa.gov/a-landsat-timeline/)
started in 1972 and is the longest running Earth-observation satellite program.

You can access public satellite data from several sources, including:

- <http://earthexplorer.usgs.gov/>
- <https://lpdaacsvc.cr.usgs.gov/appeears/>
- <https://search.earthdata.nasa.gov/search>
- <https://lpdaac.usgs.gov/data_access/data_pool>
- <https://scihub.copernicus.eu/>
- <https://aws.amazon.com/public-data-sets/landsat/>

See [this website](http://gisgeography.com/free-satellite-imagery-data-list/)
for more sources of freely available satellite remote sensing data.

In *R*, packages such as [luna](https://github.com/rspatial/luna),
[MODIS](https://cran.r-project.org/web/packages/MODIS/index.html), and
[MODISTools](https://cran.r-project.org/web/packages/MODISTools/index.html)
can search, download, and pre-process MODIS products. In Python, similar
workflows typically combine `rasterio`, `pystac`, or vendor APIs with
*tappa* for analysis.

## Terminology

Most remote sensing products consist of observations of reflectance data —
measures of the intensity of the sun's radiation reflected by the earth.
Reflectance is normally measured for different wavelengths of the
electromagnetic spectrum. Satellite data with measurements in multiple
wavelengths is called *multi-spectral* (or *hyper-spectral* when there are
many bands). See [this overview](https://gisgeography.com/multispectral-vs-hyperspectral-imagery-explained/).

Data are normally stored as raster data and are generally referred to as
*images*. Each scene (or tile) is a single acquisition. A multi-band image has
multiple observations per pixel, stored in separate raster layers. In remote
sensing jargon these layers are *bands* and grid cells are *pixels*.

## Data

You can download all raster data required for the examples in this section
with the code below. Training polygons (`lcsamples.gpkg`) are included in the
*tappa* tutorial data bundle.

```{code-cell} python
from pathlib import Path
import urllib.request
import zipfile

DATA = Path("../../data").resolve()
RS = DATA / "rs"
RS.mkdir(parents=True, exist_ok=True)

zip_path = RS / "rs.zip"
marker = RS / "LC08_044034_20170614_B2.tif"
if not marker.exists():
    url = "https://geodata.ucdavis.edu/rspatial/rs.zip"
    print("Downloading RS tutorial data …")
    urllib.request.urlretrieve(url, zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(DATA)
    print("Done.")
else:
    print("RS data already present in", RS)
```

## Resources

- [Remote Sensing Digital Image Analysis](http://www.springer.com/us/book/9783642300615)
- [Introductory Digital Image Processing: A Remote Sensing Perspective](https://www.pearsonhighered.com/program/Jensen-Introductory-Digital-Image-Processing-A-Remote-Sensing-Perspective-4th-Edition/PGM30020.html)
- [A survey of image classification methods and techniques for improving classification performance](http://www.tandfonline.com/doi/pdf/10.1080/01431160600746456)
- [A Review of Modern Approaches to Classification of Remote Sensing Data](http://link.springer.com/chapter/10.1007%2F978-94-007-7969-3_9)
- [Online remote sensing course](http://nptel.ac.in/courses/105108077/)

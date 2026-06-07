# rspatial/tappa-web

Source for the Python tutorials at <https://rspatial.org/tappa>.

This is the Python mirror of <https://rspatial.org/terra>. Content is authored
as MyST-NB markdown notebooks under `source/<section>/_py/*.md`; running
`make html` (or `python _script/build_site.py`) executes those notebooks via
`myst-nb` and renders the result with Sphinx and the `rtheme` skin shared with
the terra site.

## Build

```bash
pip install -r _script/requirements.txt
make html             # full build with notebook execution
TAPPA_NB_EXEC=off make html   # render only, skip execution
```

The HTML output lands in `build/html/`.

## Layout

```
source/
  index.rst                 top-level TOC
  conf.py                   Sphinx config (myst-nb, rtheme)
  _static/                  CSS, shared images
  spatial/                  one folder per section, mirrors web/terra/source/
    index.rst
    _py/*.md                MyST-NB notebooks (executable)
    *.md / *.rst            executed/rendered output
    figures/                generated plots
rtheme/                     custom Sphinx theme (copy of the rtheme used by terra)
_script/build_site.py       build orchestrator
data/                       any small datasets shipped with the tutorials
```

# -*- coding: utf-8 -*-
#
# Sphinx config for the tappa tutorial site (rspatial.org/tappa).
# Mirrors web/terra/source/conf.py, but tuned for Python content authored as
# MyST-NB notebooks (.md with executable code-cells).
#

import os
import sys


def setup(app):
    app.add_css_file("custom.css")


# -- General configuration -----------------------------------------------------

extensions = [
    "myst_nb",
    "sphinx.ext.mathjax",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx_design",
]

# Source files: .md is parsed by MyST (and executed by myst-nb when it has a
# jupytext header), .ipynb is executed and rendered, .rst is plain Sphinx.
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "myst-nb",
    ".ipynb": "myst-nb",
}

# Templates from the bundled rtheme (gives us the rspatial footer / banner).
templates_path = ["../rtheme/templates"]

master_doc = "index"

project = "Spatial Data Science with Python"
copyright = "2020-2026, Robert J. Hijmans"
author = "Robert J. Hijmans"

language = "en"

exclude_patterns = [
    "**.ipynb_checkpoints",
    "**/_py/**",          # raw notebook sources before execution
    "**/_build/**",
]

pygments_style = "sphinx"

todo_include_todos = False


# -- MyST / MyST-NB ------------------------------------------------------------

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "dollarmath",
    "amsmath",
    "linkify",
    "substitution",
]
myst_heading_anchors = 3

# Notebook execution policy.
#   "off"   — render notebooks without running them
#   "cache" — execute and cache results; reused unless the source changed
#   "force" — always re-execute
#
# Default: pick "cache" automatically when tappa can be imported (so outputs
# show up out of the box on Linux/WSL/CI), otherwise fall back to "off" so
# Windows hosts that can't build the C++ extension still produce a site.
# Override by setting TAPPA_NB_EXEC in the environment.
def _default_exec_mode() -> str:
    try:
        import importlib.util
        if importlib.util.find_spec("tappa") is not None:
            return "cache"
    except Exception:
        pass
    return "off"


nb_execution_mode = os.environ.get("TAPPA_NB_EXEC", _default_exec_mode())
if nb_execution_mode == "off":
    print(
        "[tappa docs] nb_execution_mode='off' — code cell outputs will NOT be "
        "rendered. Install 'tappa' in the build environment, or set "
        "TAPPA_NB_EXEC=cache (or =force) to enable execution.",
        flush=True,
    )
nb_execution_timeout = 300
nb_execution_allow_errors = False
nb_merge_streams = True


# -- HTML output ---------------------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_theme_options = {}
html_theme_path = ["../rtheme/theme/"]
html_title = "R Spatial \u2014 Python"
html_static_path = ["_static"]
html_show_sphinx = False
html_show_copyright = False

htmlhelp_basename = "tappadoc"


# -- Intersphinx (cross-link to upstream Python docs) --------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "pandas": ("https://pandas.pydata.org/docs", None),
    "matplotlib": ("https://matplotlib.org/stable", None),
}


# -- LaTeX (for the per-section PDFs that the build script copies) ------------

latex_elements = {}
latex_documents = [
    (master_doc, "tappa.tex", "Spatial Data Science with Python",
     "Robert J. Hijmans", "manual"),
]

man_pages = [
    (master_doc, "tappa", "Spatial Data Science with Python",
     [author], 1)
]

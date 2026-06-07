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

This is an introduction to spatial data manipulation with *Python* and the
[tappa](https://github.com/rspatial/tappa) package. *tappa* is the Python port
of the *R* [terra](https://github.com/rspatial/terra) package. It exposes the
same C++ core (the `terra_lib` source tree) and uses the same `Spat*` class
names, so most workflows from the
[R rspatial.org tutorials](https://rspatial.org/) translate directly. In this
context "spatial data" refers to data about geographical locations, that is,
places on earth. To be more precise we should speak about "geospatial" data, but
we use the shorthand "spatial".

You can install the latest released version of *tappa* with

```bash
pip install tappa
```

(or in a *conda* environment, see the
[tappa README](https://github.com/rspatial/tappa#readme) for details on the
geospatial dependencies). The development version is available from
[github](https://www.github.com/rspatial/tappa); the README there has build
instructions. The github tracker is the right place to report what you believe
to be bugs (errors in the software) or to request new features. You can ask
questions on how to use *tappa* on
[stackoverflow](https://stackoverflow.com/search?tab=newest&q=tappa).

This is the introductory part of a set of resources for learning about spatial
analysis and modeling with *Python*. Here we cover the basics of data
manipulation. Throughout the tutorials we use *tappa* together with
[NumPy](https://numpy.org/), [pandas](https://pandas.pydata.org/), and
[Matplotlib](https://matplotlib.org/).

You need to know some of the basics of the *Python* language before you can
work with spatial data in *Python*. If you have not used *Python* before, the
[official tutorial](https://docs.python.org/3/tutorial/) is a good place to
start, and the
[Scientific Python lectures](https://lectures.scientific-python.org/) cover
NumPy and Matplotlib in depth.

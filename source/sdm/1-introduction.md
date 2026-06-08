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

This document provides an introduction to species distribution modeling with
*Python* and [*tappa*](https://github.com/rspatial/tappa). Species distribution
modeling (SDM) is also known under other names including climate
envelope-modeling, habitat modeling, and (environmental or ecological)
niche-modeling. The aim of SDM is to estimate the similarity of the conditions
at any site to the conditions at the locations of known occurrence (and perhaps
of non-occurrence) of a phenomenon. A common application of this method is to
predict species ranges with climate data as predictors.

In SDM, the following steps are usually taken: (1) locations of occurrence of a
species (or other phenomenon) are compiled; (2) values of environmental
predictor variables (such as climate) at these locations are extracted from
spatial databases; (3) the environmental values are used to fit a model to
estimate similarity to the sites of occurrence, or another measure such as
abundance of the species; (4) the model is used to predict the variable of
interest across the region of interest (and perhaps for a future or past
climate).

We assume that you are familiar with most of the concepts in SDM. If in doubt,
you could consult, for example, the book by Janet Franklin (2009), the somewhat
more theoretical book by Peterson *et al.* (2011), or the recent review article
by Elith and Leathwick (2009). It is important to have a good understanding of
the interplay of environmental (niche) and geographic (biotope) space – see
Colwell and Rangel (2009) and Peterson *et al.* (2011) for a discussion. SDM is
a widely used approach but there is much debate on when and how to best use this
method.

We also assume that you are already somewhat familiar with *Python* and spatial
data handling with *tappa*. If you are new to these topics, start with the
[spatial data manipulation](../spatial/index) tutorials.

The original *R* version of this SDM tutorial uses the `predicts` and `terra`
packages. Here we use *tappa* for spatial data and common *Python* libraries
(*pandas*, *statsmodels*, *scikit-learn*) for statistical modeling. Profile
methods such as Bioclim are illustrated with small helper classes; for
production SDM workflows you may also want dedicated packages such as
`scikit-learn`, `maxent` ports, or the original *R* `predicts` / `dismo`
tools via *R*.

This document consists of four main parts: data preparation (occurrence and
environmental data, absence/background sampling), model fitting and evaluation,
and references. Advanced topics from the full *R* tutorial (additional modeling
methods, null models) are not yet covered here.

Robert J. Hijmans and Jane Elith

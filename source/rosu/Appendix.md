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

# Appendix

This page accompanies the Appendix of
[O'Sullivan and Unwin (2010)](https://www.wiley.com/en-us/Geographic+Information+Analysis%2C+2nd+Edition-p-9780470288573).

Add two matrices:

```{code-cell} python
import numpy as np

A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])
A + B
```

Matrix multiplication:

```{code-cell} python
A = np.array([[1, -4, -2], [5, 3, -6]])
B = np.array([[6, 4], [-5, -3], [2, -1]])
A @ B
B @ A
```

Matrix transposition:

```{code-cell} python
A = np.array([[1, 2, 3], [4, 5, 6]])
A, A.T
```

Identity matrix:

```{code-cell} python
I = np.eye(2)
I
np.eye(5)
```

Finding the inverse matrix:

```{code-cell} python
A = np.array([[1, 2], [3, 4]])
Inv = np.linalg.inv(A)
Inv
np.round(A @ Inv, 10)
```

`inv(AB) == inv(B) @ inv(A)`:

```{code-cell} python
A = np.array([[1, 2], [3, 4]])
B = np.array([[4, 3], [2, 1]])
AB = A @ B
np.linalg.inv(AB)
np.linalg.inv(B) @ np.linalg.inv(A)
```

Simultaneous equations:

```{code-cell} python
A = np.array([[3, 2], [4, -4]])
b = np.array([[11], [-6]])
np.linalg.inv(A) @ b
```

Rotation:

```{code-cell} python
A = np.array([[0.6, -0.8], [0.8, 0.6]])
s = np.array([[3], [4]])
np.round(A @ s, 10)

S = np.array([[1, 3, 0, -1, -2.5], [1, -2, 5, 4, -4]])
A @ S
```

The angle of rotation matrix `A` is:

```{code-cell} python
angle = np.arccos(A[0, 0])
angle, 180 * angle / np.pi
```

Eigenvectors and eigenvalues:

```{code-cell} python
M = np.array([[3, 2], [4, -4]])
np.linalg.eig(M)

M = np.array([[1, 3], [3, 2]])
np.linalg.eig(M)
```

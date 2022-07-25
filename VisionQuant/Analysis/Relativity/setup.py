from setuptools import Extension, setup
from Cython.Build import cythonize
import numpy as np

extensions = [
    Extension("relativity_cy",
              ["relativity_cy.pyx", "relativity_cfunc.c"],
              include_dirs=[np.get_include()]),
]
setup(
    name='Relativity',
    ext_modules=cythonize(extensions),
)

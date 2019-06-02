from distutils.core import setup
from Cython.Build import cythonize

setup(name='kspace',
      ext_modules=cythonize("kspace.pyx"))

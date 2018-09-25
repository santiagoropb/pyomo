from pyomo.contrib.pynumero.extensions.utils import find_pynumero_library
from pkg_resources import resource_filename
import numpy.ctypeslib as npct
import numpy as np
import platform
import ctypes
import sys
import os


class SparseLibInterface(object):
    def __init__(self):
        self.libname = find_pynumero_library('pynumero_SPARSE')
        self.lib = None

    def __call__(self):
        if self.lib is None:
            self._setup()
        return self.lib

    def available(self):
        if self.libname is None:
            return False
        return os.path.exists(self.libname)

    def _setup(self):
        if not self.available():
            raise RuntimeError(
                "SparseUtils is not supported on this platform (%s)"
                % (os.name,) )
        self.lib = ctypes.cdll.LoadLibrary(self.libname)
        self.lib.EXTERNAL_SPARSE_sym_coo_matvec.argtypes = [
            array_1d_int,
            array_1d_int,
            array_1d_double,
            ctypes.c_int,
            array_1d_double,
            ctypes.c_int,
            array_1d_double,
            ctypes.c_int
            ]
        self.lib.EXTERNAL_SPARSE_sym_coo_matvec.restype = None

SparseLib = SparseLibInterface()

# define 1d array
array_1d_double = npct.ndpointer(dtype=np.double, ndim=1, flags='CONTIGUOUS')
array_1d_int = npct.ndpointer(dtype=np.intc, ndim=1, flags='CONTIGUOUS')

def sym_coo_matvec(irow, jcol, values, x, result):
    data = values.astype(np.double, casting='safe')
    SparseLib().EXTERNAL_SPARSE_sym_coo_matvec(irow,
                                               jcol,
                                               data,
                                               len(irow),
                                               x,
                                               len(x),
                                               result,
                                               len(result))

def sym_csr_matvec():
    raise RuntimeError("TODO")

def sym_csc_matvec():
    raise RuntimeError("TODO")

def csr_matvec_no_diag():
    raise RuntimeError("TODO")

def csc_matvec_no_diag():
    raise RuntimeError("TODO")

from scipy.sparse import csc_matrix as scipy_csc_matrix
from scipy.sparse import coo_matrix as scipy_coo_matrix

from scipy.sparse._sparsetools import csc_tocsr
from scipy.sparse.sputils import (upcast,
                                  upcast_char,
                                  get_index_dtype)

from scipy.sparse import _sparsetools

try:
    from pyomo.contrib.pynumero.extensions.sparseutils import (sym_csc_matvec,
                                                 csr_matvec_no_diag,
                                                 csc_matvec_no_diag)
except ImportError as e:
    print('{}'.format(e))
    raise ImportError('Error importing sparseutils while running coo interface. '
                      'Make sure libpynumero_SPARSE is installed and added to path.')

from pyomo.contrib.pynumero.sparse.base import SparseBase
import numpy as np

__all__ = ['CSCMatrix', 'CSCSymMatrix']


class CSCMatrix(SparseBase, scipy_csc_matrix):

    def __init__(self, arg1, shape=None, dtype=None, copy=False):

        scipy_csc_matrix.__init__(self, arg1, shape=shape, dtype=dtype, copy=copy)
        SparseBase.__init__(self)

    def tosymcsc(self, copy=False):
        raise NotImplementedError('Not supported')

    def tocsr(self, copy=False):
        M, N = self.shape
        idx_dtype = get_index_dtype((self.indptr, self.indices),
                                    maxval=max(self.nnz, N))
        indptr = np.empty(M + 1, dtype=idx_dtype)
        indices = np.empty(self.nnz, dtype=idx_dtype)
        data = np.empty(self.nnz, dtype=upcast(self.dtype))

        csc_tocsr(M, N,
                  self.indptr.astype(idx_dtype),
                  self.indices.astype(idx_dtype),
                  self.data,
                  indptr,
                  indices,
                  data)

        from pyomo.contrib.pynumero.sparse.csr import CSRMatrix
        A = CSRMatrix((data, indices, indptr), shape=self.shape, copy=False)
        A.has_sorted_indices = True
        return A

    def tocoo(self, copy=True):
        major_dim, minor_dim = self._swap(self.shape)
        minor_indices = self.indices
        major_indices = np.empty(len(minor_indices), dtype=self.indices.dtype)
        _sparsetools.expandptr(major_dim, self.indptr, major_indices)
        row, col = self._swap((major_indices, minor_indices))

        from pyomo.contrib.pynumero.sparse.coo import COOMatrix
        return COOMatrix((self.data, (row, col)), self.shape, copy=copy,
                         dtype=self.dtype)

    def transpose(self, axes=None, copy=False):
        if axes is not None:
            raise ValueError(("Sparse matrices do not support "
                              "an 'axes' parameter because swapping "
                              "dimensions is the only logical permutation."))

        M, N = self.shape

        from pyomo.contrib.pynumero.sparse.csr import CSRMatrix
        return CSRMatrix((self.data, self.indices,
                          self.indptr), (N, M), copy=copy)

    def _with_data(self,data,copy=True):
        """Returns a matrix with the same sparsity structure as self,
        but with different data.  By default the structure arrays
        (i.e. .indptr and .indices) are copied.
        """
        if copy:
            return self.__class__((data, self.indices.copy(), self.indptr.copy()),
                                  shape=self.shape, dtype=data.dtype)
        else:
            return self.__class__((data, self.indices, self.indptr),
                                  shape=self.shape, dtype=data.dtype)

    def _add_sparse(self, other):
        if other.is_symmetric:
            return super(CSCMatrix, self)._add_sparse(other.tofullmatrix())
        else:
            return super(CSCMatrix, self)._add_sparse(other)

    def _sub_sparse(self, other):
        if other.is_symmetric:
            return super(CSCMatrix, self)._sub_sparse(other.tofullmatrix())
        else:
            return super(CSCMatrix, self)._sub_sparse(other)

    def getcol(self, j):
        return CSCMatrix(super(CSCMatrix, self).getcol(j))

    def getrow(self, i):
        from pyomo.contrib.pynumero.sparse.csr import CSRMatrix
        return CSRMatrix(super(CSCMatrix, self).getrow(i))

    def __repr__(self):
        return 'CSCMatrix{}'.format(self.shape)

# this matrix will only store the lower triangular indices
class CSCSymMatrix(CSCMatrix):

    def __init__(self, arg1, shape=None, dtype=None, copy=False):

        super().__init__(arg1, shape=shape, dtype=dtype, copy=copy)

        # add check to verify square matrix
        if self.shape[0] != self.shape[1]:
            raise RuntimeError('A rectangular matrix is not symmetric')

        # check nnz is less than the full lower triangular
        if self.nnz > self.shape[0] * (self.shape[0] + 1) / 2:
            raise RuntimeError('CSCSymMatrix only store lower triangular entries. Too many nnz')

        # TODO: check only lower triangular entries

        # makes sparse matrix symmetric
        self._symmetric = True

    def transpose(self, axes=None, copy=False):
        if axes is not None:
            raise ValueError(("Sparse matrices do not support "
                              "an 'axes' parameter because swapping "
                              "dimensions is the only logical permutation."))

        M, N = self.shape

        return CSCSymMatrix((self.data, self.indices,
                             self.indptr), (N, M), copy=copy)

    def toarray(self, order=None, out=None):
        m = self.tofullcoo()
        return m.toarray(order=order, out=out)

    def todense(self, order=None, out=None):
        return np.asmatrix(self.toarray(order=order, out=out))

    def tocsr(self, copy=False):
        M, N = self.shape
        idx_dtype = get_index_dtype((self.indptr, self.indices),
                                    maxval=max(self.nnz, N))
        indptr = np.empty(M + 1, dtype=idx_dtype)
        indices = np.empty(self.nnz, dtype=idx_dtype)
        data = np.empty(self.nnz, dtype=upcast(self.dtype))

        csc_tocsr(M, N,
                  self.indptr.astype(idx_dtype),
                  self.indices.astype(idx_dtype),
                  self.data,
                  indptr,
                  indices,
                  data)

        from pyomo.contrib.pynumero.sparse.csr import CSRSymMatrix
        A = CSRSymMatrix((data, indices, indptr), shape=self.shape, copy=False)
        A.has_sorted_indices = True
        return A

    def tocoo(self, copy=True):
        major_dim, minor_dim = self._swap(self.shape)
        minor_indices = self.indices
        major_indices = np.empty(len(minor_indices), dtype=self.indices.dtype)
        _sparsetools.expandptr(major_dim, self.indptr, major_indices)
        row, col = self._swap((major_indices, minor_indices))

        from pyomo.contrib.pynumero.sparse.coo import COOSymMatrix
        return COOSymMatrix((self.data, (row, col)), self.shape, copy=copy,
                            dtype=self.dtype)

    def tofullcoo(self):
        return self.tocoo().tofullcoo()

    def tofullcsr(self):
        return self.tocoo().tofullcsr()

    def tofullcsc(self):
        return self.tocoo().tofullcsc()

    def tofullmatrix(self):
        return self.tofullcsc()

    def todia(self, copy=False):
        raise NotImplementedError('Not supported')

    def tolil(self, copy=False):
        raise NotImplementedError('Not supported')

    def _add_sparse(self, other):
        if other.is_symmetric:
            return self.tocsr()._add_sparse(other)
        else:
            return self.tofullmatrix()._add_sparse(other)

    def _sub_sparse(self, other):
        if other.is_symmetric:
            # ToDo: check if binopt works here directly
            return self.tocsr()._sub_sparse(other)
        else:
            return self.tofullmatrix()._sub_sparse(other)

    def _add_dense(self, other):
        return self.tofullcoo()._add_dense(other)

    def _mul_vector(self, other):

        M, N = self.shape

        # output array
        resultl = np.zeros(M, dtype=upcast_char(self.dtype.char,
                                                other.dtype.char))

        resultu = np.zeros(M, dtype=upcast_char(self.dtype.char,
                                                other.dtype.char))

        # csr_matvec or csc_matvec
        fnl = getattr(_sparsetools, self.format + '_matvec')
        fnl(M, N, self.indptr, self.indices, self.data, other, resultl)

        upper = self.transpose()
        #fnu = getattr(_sparsetools, upper.format + '_matvec')
        #fnu(M, N, upper.indptr, upper.indices, upper.data, other, resultu)
        csr_matvec_no_diag(M, upper.indptr, upper.indices, upper.data, other, resultu)
        #diagonal = self.diagonal()

        # result = np.zeros(M, dtype=upcast_char(self.dtype.char, other.dtype.char))
        # sym_csc_matvec(N, self.indptr, self.indices, self.data, other, result)
        # return result

        return resultl + resultu # - np.multiply(other, diagonal)

    def _mul_multivector(self, other):
        raise NotImplementedError('Not supported')

    def _mul_sparse_matrix(self, other):
        raise NotImplementedError('Not supported')

    def getcol(self, j):
        return self.tofullmatrix().getcol(j)

    def getrow(self, i):
        return self.tofullmatrix().getrow(i)

    def __repr__(self):
        return 'CSCSymMatrix{}'.format(self.shape)


if __name__ == "__main__":

    row = np.array([0, 3, 1, 0])
    col = np.array([0, 3, 1, 2])
    data = np.array([4, 5, 7, 9])
    m = CSCMatrix((data, (row, col)), shape=(4, 4))
    print(m.toarray())
    print(m.is_symmetric)

    row = np.array([0, 3, 1, 2, 3])
    col = np.array([0, 0, 1, 2, 3])
    data = np.array([2, 1, 3, 4, 5])
    m = CSCSymMatrix((data, (row, col)), shape=(4, 4))
    print(m.toarray())
    print(m.is_symmetric)

    mcsc = m.tofullcsc()
    print(mcsc.toarray())
    print(mcsc.is_symmetric)

    x = np.ones(m.shape[0])
    print(mcsc.dot(x))
    print(m.dot(x))

    row = np.array([0, 1, 4, 1, 2, 7, 2, 3, 5, 3, 4, 5, 4, 7, 5, 6, 6, 7])
    col = np.array([0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 5, 5, 6, 7])
    data = np.array([27, 5, 12, 56, 66, 34, 94, 31, 41, 7, 98, 72, 24, 33, 78, 47, 98, 41])
    big_m = CSCSymMatrix((data, (row, col)), shape=(8, 8))
    print(big_m.toarray())
    print(big_m.is_symmetric)
    x = np.ones(big_m.shape[0])
    print(big_m.tofullcsc().dot(x))
    print(big_m.dot(x))
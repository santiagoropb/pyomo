from pkg_resources import resource_filename
import numpy.ctypeslib as npct
import numpy as np
import platform
import ctypes
import sys
import os


#TODO: ask about assertions
#TODO: ask about freeing memory

class AmplInterface(object):
    def __init__(self, filename=None, nl_buffer=None):

        #TODO: check for 32 or 64 bit and raise error if not supported

        if os.name in ['nt', 'dos']:
            libasl = resource_filename(__name__, 'lib/Windows/libpynumero_ASL.dll')
            raise RuntimeError("Not supported yet")
        elif sys.platform in ['darwin']:
            libasl = resource_filename(__name__, 'lib/Darwin/libpynumero_ASL.so')
        else:
            libasl = resource_filename(__name__, 'lib/Linux/libpynumero_ASL.so')


        self.ASLib = ctypes.cdll.LoadLibrary(libasl)

        # define 1d array
        array_1d_double = npct.ndpointer(dtype=np.double, ndim=1, flags='CONTIGUOUS')
        array_1d_int = npct.ndpointer(dtype=np.intc, ndim=1, flags='CONTIGUOUS')

        # constructor
        self.ASLib.EXTERNAL_AmplInterface_new.argtypes = [ctypes.c_char_p]
        self.ASLib.EXTERNAL_AmplInterface_new.restype = ctypes.c_void_p

        self.ASLib.EXTERNAL_AmplInterface_new_file.argtypes = [ctypes.c_char_p]
        self.ASLib.EXTERNAL_AmplInterface_new_file.restype = ctypes.c_void_p

        #self.ASLib.EXTERNAL_AmplInterface_new_str.argtypes = [ctypes.c_char_p]
        #self.ASLib.EXTERNAL_AmplInterface_new_str.restype = ctypes.c_void_p

        # number of variables
        self.ASLib.EXTERNAL_AmplInterface_n_vars.argtypes = [ctypes.c_void_p]
        self.ASLib.EXTERNAL_AmplInterface_n_vars.restype = ctypes.c_int

        # number of constraints
        self.ASLib.EXTERNAL_AmplInterface_n_constraints.argtypes = [ctypes.c_void_p]
        self.ASLib.EXTERNAL_AmplInterface_n_constraints.restype = ctypes.c_int

        # number of nonzeros in jacobian
        self.ASLib.EXTERNAL_AmplInterface_nnz_jac_g.argtypes = [ctypes.c_void_p]
        self.ASLib.EXTERNAL_AmplInterface_nnz_jac_g.restype = ctypes.c_int

        # number of nonzeros in hessian of lagrangian
        self.ASLib.EXTERNAL_AmplInterface_nnz_hessian_lag.argtypes = [ctypes.c_void_p]
        self.ASLib.EXTERNAL_AmplInterface_nnz_hessian_lag.restype = ctypes.c_int

        # bounds info
        self.ASLib.EXTERNAL_AmplInterface_get_bounds_info.argtypes = [ctypes.c_void_p,
                                                                      array_1d_double,
                                                                      array_1d_double,
                                                                      ctypes.c_int,
                                                                      array_1d_double,
                                                                      array_1d_double,
                                                                      ctypes.c_int]
        self.ASLib.EXTERNAL_AmplInterface_get_bounds_info.restype = None
        # lower bounds on x
        self.ASLib.EXTERNAL_AmplInterface_x_lower_bounds.argtypes = [ctypes.c_void_p,
                                                                     array_1d_double,
                                                                     ctypes.c_int]
        self.ASLib.EXTERNAL_AmplInterface_x_lower_bounds.restype = None

        # upper bounds on x
        self.ASLib.EXTERNAL_AmplInterface_x_upper_bounds.argtypes = [ctypes.c_void_p,
                                                                     array_1d_double,
                                                                     ctypes.c_int]
        self.ASLib.EXTERNAL_AmplInterface_x_upper_bounds.restype = None

        # lower bounds on g
        self.ASLib.EXTERNAL_AmplInterface_g_lower_bounds.argtypes = [ctypes.c_void_p,
                                                                     array_1d_double,
                                                                     ctypes.c_int]
        self.ASLib.EXTERNAL_AmplInterface_g_lower_bounds.restype = None

        # upper bounds on g
        self.ASLib.EXTERNAL_AmplInterface_g_upper_bounds.argtypes = [ctypes.c_void_p,
                                                                     array_1d_double,
                                                                     ctypes.c_int]
        self.ASLib.EXTERNAL_AmplInterface_g_upper_bounds.restype = None

        # initial value x
        self.ASLib.EXTERNAL_AmplInterface_x_init.argtypes = [ctypes.c_void_p,
                                                             array_1d_double,
                                                             ctypes.c_int]
        self.ASLib.EXTERNAL_AmplInterface_x_init.restype = None

        # initial value multipliers
        self.ASLib.EXTERNAL_AmplInterface_lam_init.argtypes = [ctypes.c_void_p,
                                                               array_1d_double,
                                                               ctypes.c_int]
        self.ASLib.EXTERNAL_AmplInterface_lam_init.restype = None

        # starting point
        self.ASLib.EXTERNAL_AmplInterface_starting_point.argtypes = [ctypes.c_void_p,
                                                                     array_1d_double,
                                                                     ctypes.c_int,
                                                                     array_1d_double,
                                                                     ctypes.c_int]
        self.ASLib.EXTERNAL_AmplInterface_starting_point.restype = None

        # evaluate objective
        self.ASLib.EXTERNAL_AmplInterface_eval_f.argtypes = [ctypes.c_void_p,
                                                             array_1d_double,
                                                             ctypes.c_int,
                                                             ctypes.POINTER(ctypes.c_double)]
        self.ASLib.EXTERNAL_AmplInterface_eval_f.restype = ctypes.c_bool

        # gradient objective
        self.ASLib.EXTERNAL_AmplInterface_eval_deriv_f.argtypes = [ctypes.c_void_p,
                                                                   array_1d_double,
                                                                   array_1d_double,
                                                                   ctypes.c_int]
        self.ASLib.EXTERNAL_AmplInterface_eval_deriv_f.restype = ctypes.c_bool

        # structure jacobian of constraints
        self.ASLib.EXTERNAL_AmplInterface_struct_jac_g.argtypes = [ctypes.c_void_p,
                                                                   array_1d_int,
                                                                   array_1d_int,
                                                                   ctypes.c_int]
        self.ASLib.EXTERNAL_AmplInterface_struct_jac_g.restype = None

        # structure hessian of Lagrangian
        self.ASLib.EXTERNAL_AmplInterface_struct_hes_lag.argtypes = [ctypes.c_void_p,
                                                                     array_1d_int,
                                                                     array_1d_int,
                                                                     ctypes.c_int]
        self.ASLib.EXTERNAL_AmplInterface_struct_hes_lag.restype = None

        # evaluate constraints
        self.ASLib.EXTERNAL_AmplInterface_eval_g.argtypes = [ctypes.c_void_p,
                                                             array_1d_double,
                                                             ctypes.c_int,
                                                             array_1d_double,
                                                             ctypes.c_int]
        self.ASLib.EXTERNAL_AmplInterface_eval_g.restype = ctypes.c_bool

        # evaluate jacobian constraints
        self.ASLib.EXTERNAL_AmplInterface_eval_jac_g.argtypes = [ctypes.c_void_p,
                                                                 array_1d_double,
                                                                 ctypes.c_int,
                                                                 array_1d_double,
                                                                 ctypes.c_int]
        self.ASLib.EXTERNAL_AmplInterface_eval_jac_g.restype = ctypes.c_bool

        # evaluate hessian Lagrangian
        self.ASLib.EXTERNAL_AmplInterface_eval_hes_lag.argtypes = [ctypes.c_void_p,
                                                                   array_1d_double,
                                                                   ctypes.c_int,
                                                                   array_1d_double,
                                                                   ctypes.c_int,
                                                                   array_1d_double,
                                                                   ctypes.c_int]
        self.ASLib.EXTERNAL_AmplInterface_eval_hes_lag.restype = ctypes.c_bool

        # finalize solution
        self.ASLib.EXTERNAL_AmplInterface_finalize_solution.argtypes = [ctypes.c_void_p,
                                                                        ctypes.c_int,
                                                                        array_1d_double,
                                                                        ctypes.c_int,
                                                                        array_1d_double,
                                                                        ctypes.c_int]
        self.ASLib.EXTERNAL_AmplInterface_finalize_solution.restype = None

        # mapping
        self.ASLib.EXTERNAL_AmplInterface_map_g_indices.argtypes = [array_1d_int,
                                                                    ctypes.c_int,
                                                                    array_1d_int,
                                                                    ctypes.c_int]
        self.ASLib.EXTERNAL_AmplInterface_map_g_indices.restype = None

        # destructor
        self.ASLib.EXTERNAL_AmplInterface_free_memory.argtypes = [ctypes.c_void_p]
        self.ASLib.EXTERNAL_AmplInterface_free_memory.restype = None

        if filename is not None:
            if nl_buffer is not None:
                raise ValueError("Cannot specify both filename= and nl_buffer=")

            b_data = filename.encode('utf-8')
            # ToDo: add check pointer is not null in the c-code
            self._obj = self.ASLib.EXTERNAL_AmplInterface_new_file(b_data)
        elif nl_buffer is not None:
            b_data = nl_buffer.encode('utf-8')
            if os.name in ['nt', 'dos']:
                # ToDo: add check pointer is not null in the c-code
                self._obj = self.ASLib.EXTERNAL_AmplInterface_new_file(b_data)
            else:
                self._obj = self.ASLib.EXTERNAL_AmplInterface_new_str(b_data)

        assert self._obj, "Error building ASL interface. Possible error in nl-file"


        self._nx = self.get_n_vars()
        self._ny = self.get_n_constraints()
        self._nnz_jac_g = self.get_nnz_jac_g()
        self._nnz_hess = self.get_nnz_hessian_lag()

    def __del__(self):
        self.ASLib.EXTERNAL_AmplInterface_free_memory(self._obj)

    def get_n_vars(self):
        return self.ASLib.EXTERNAL_AmplInterface_n_vars(self._obj)

    def get_n_constraints(self):
        return self.ASLib.EXTERNAL_AmplInterface_n_constraints(self._obj)

    def get_nnz_jac_g(self):
        return self.ASLib.EXTERNAL_AmplInterface_nnz_jac_g(self._obj)

    def get_nnz_hessian_lag(self):
        return self.ASLib.EXTERNAL_AmplInterface_nnz_hessian_lag(self._obj)

    def get_bounds_info(self, xl, xu, gl, gu):
        x_l = xl.astype(np.double, casting='safe', copy=False)
        x_u = xu.astype(np.double, casting='safe', copy=False)
        g_l = gl.astype(np.double, casting='safe', copy=False)
        g_u = gu.astype(np.double, casting='safe', copy=False)
        nx = len(x_l)
        ng = len(g_l)
        assert nx == len(x_u), "lower and upper bound x vectors must be the same size"
        assert ng == len(g_u), "lower and upper bound g vectors must be the same size"
        self.ASLib.EXTERNAL_AmplInterface_get_bounds_info(self._obj,
                                                          x_l,
                                                          x_u,
                                                          nx,
                                                          g_l,
                                                          g_u,
                                                          ng)

    def get_x_lower_bounds(self, invec):
        self.ASLib.EXTERNAL_AmplInterface_x_lower_bounds(self._obj, invec, len(invec))

    def get_x_upper_bounds(self, invec):
        self.ASLib.EXTERNAL_AmplInterface_x_upper_bounds(self._obj, invec, len(invec))

    def get_g_lower_bounds(self, invec):
        self.ASLib.EXTERNAL_AmplInterface_g_lower_bounds(self._obj, invec, len(invec))

    def get_g_upper_bounds(self, invec):
        self.ASLib.EXTERNAL_AmplInterface_g_upper_bounds(self._obj, invec, len(invec))

    def get_init_x(self, invec):
        self.ASLib.EXTERNAL_AmplInterface_x_init(self._obj, invec, len(invec))

    def get_init_multipliers(self, invec):
        self.ASLib.EXTERNAL_AmplInterface_lam_init(self._obj, invec, len(invec))

    def get_starting_point(self, x, lam):
        self.ASLib.EXTERNAL_AmplInterface_starting_point(self._obj,
                                                         x,
                                                         len(x),
                                                         lam,
                                                         len(lam))

    def eval_f(self, x):
        assert x.size == self._nx, "Error: Dimension missmatch."
        assert x.dtype == np.double, "Error: array type. Function eval_deriv_f expects an array of type double"
        sol = ctypes.c_double()
        res = self.ASLib.EXTERNAL_AmplInterface_eval_f(self._obj, x, self._nx, ctypes.byref(sol))
        assert res, "Error in AMPL evaluation"
        return sol.value

    def eval_deriv_f(self, x, df):
        assert x.size == self._nx, "Error: Dimension missmatch."
        assert x.dtype == np.double, "Error: array type. Function eval_deriv_f expects an array of type double"
        res = self.ASLib.EXTERNAL_AmplInterface_eval_deriv_f(self._obj, x, df, len(x))
        assert res, "Error in AMPL evaluation"

    def struct_jac_g(self, irow, jcol):
        irow_p = irow.astype(np.intc, casting='safe', copy=False)
        jcol_p = jcol.astype(np.intc, casting='safe', copy=False)
        assert len(irow) == len(jcol), "Error: Dimension missmatch. Arrays irow and jcol must be of the same size"
        assert len(irow) == self._nnz_jac_g, "Error: Dimension missmatch. Jacobian has {} nnz".format(self._nnz_jac_g)
        self.ASLib.EXTERNAL_AmplInterface_struct_jac_g(self._obj,
                                                       irow_p,
                                                       jcol_p,
                                                       len(irow))

    def struct_hes_lag(self, irow, jcol):
        irow_p = irow.astype(np.intc, casting='safe', copy=False)
        jcol_p = jcol.astype(np.intc, casting='safe', copy=False)
        assert len(irow) == len(jcol), "Error: Dimension missmatch. Arrays irow and jcol must be of the same size"
        assert len(irow) == self._nnz_hess, "Error: Dimension missmatch. Hessian has {} nnz".format(self._nnz_hess)
        self.ASLib.EXTERNAL_AmplInterface_struct_hes_lag(self._obj,
                                                         irow_p,
                                                         jcol_p,
                                                         len(irow))

    def eval_jac_g(self, x, jac_g_values):
        assert x.size == self._nx, "Error: Dimension missmatch."
        assert jac_g_values.size == self._nnz_jac_g, "Error: Dimension missmatch."
        xeval = x.astype(np.double, casting='safe', copy=False)
        jac_eval = jac_g_values.astype(np.double, casting='safe', copy=False)
        res = self.ASLib.EXTERNAL_AmplInterface_eval_jac_g(self._obj,
                                                           xeval,
                                                           self._nx,
                                                           jac_eval,
                                                           self._nnz_jac_g)
        assert res, "Error in AMPL evaluation"

    def eval_g(self, x, g):
        assert x.size == self._nx, "Error: Dimension missmatch."
        assert g.size == self._ny, "Error: Dimension missmatch."
        assert x.dtype == np.double, "Error: array type. Function eval_g expects an array of type double"
        assert g.dtype == np.double, "Error: array type. Function eval_g expects an array of type double"
        res = self.ASLib.EXTERNAL_AmplInterface_eval_g(self._obj,
                                                       x,
                                                       self._nx,
                                                       g,
                                                       self._ny)
        assert res, "Error in AMPL evaluation"

    def eval_hes_lag(self, x, lam, hes_lag):
        assert x.size == self._nx, "Error: Dimension missmatch."
        assert lam.size == self._ny, "Error: Dimension missmatch."
        assert hes_lag.size == self._nnz_hess, "Error: Dimension missmatch."
        assert x.dtype == np.double, "Error: array type. Function eval_hes_lag expects an array of type double"
        assert lam.dtype == np.double, "Error: array type. Function eval_hes_lag expects an array of type double"
        assert hes_lag.dtype == np.double, "Error: array type. Function eval_hes_lag expects an array of type double"
        res = self.ASLib.EXTERNAL_AmplInterface_eval_hes_lag(self._obj,
                                                             x,
                                                             self._nx,
                                                             lam,
                                                             self._ny,
                                                             hes_lag,
                                                             self._nnz_hess)
        assert res, "Error in AMPL evaluation"

    def finalize_solution(self, status, x, lam):
        self.ASLib.EXTERNAL_AmplInterface_finalize_solution(self._obj,
                                                            status,
                                                            x,
                                                            len(x),
                                                            lam,
                                                            len(lam))

    def inplace_map(self, arr, map_arr):
        self.ASLib.EXTERNAL_AmplInterface_map_g_indices(arr,
                                                        len(arr),
                                                        map_arr,
                                                        len(map_arr))


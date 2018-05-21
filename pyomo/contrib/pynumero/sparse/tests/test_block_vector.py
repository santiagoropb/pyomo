import unittest
import sys

try:
    from pyomo.contrib.pynumero.sparse import BlockVector
    import numpy as np
except:
    raise unittest.SkipTest("Pynumero needs scipy and numpy to run NLP tests")


class TestBlockVector(unittest.TestCase):

    def test_constructor(self):

        v = BlockVector(4)
        self.assertEqual(v.nblocks, 4)
        self.assertEqual(v.bshape, (4,))
        self.assertEqual(v.size, 0)

        v[0] = np.ones(2)
        v[1] = np.ones(4)
        self.assertEqual(v.size, 6)
        self.assertEqual(v.shape, (6,))
        v[0] = None
        self.assertEqual(v.size, 4)
        self.assertEqual(v.shape, (4,))
        self.assertEqual(v.ndim, 1)

    def setUp(self):

        self.ones = BlockVector(3)
        self.list_sizes_ones = [2, 4, 3]
        for idx, s in enumerate(self.list_sizes_ones):
            self.ones[idx] = np.ones(s)

    def test_block_sizes(self):
        self.assertListEqual(self.ones.block_sizes().tolist(), self.list_sizes_ones)

    def test_dot(self):
        v1 = self.ones
        self.assertEqual(v1.dot(v1), v1.size)
        v2 = v1.clone(3.3)
        self.assertAlmostEqual(v1.dot(v2), v1.size*3.3)

    def test_mean(self):
        flat_v = np.ones(self.ones.size)
        v = self.ones
        self.assertEqual(v.mean(), flat_v.mean())

    def test_sum(self):
        self.assertEqual(self.ones.sum(), self.ones.size)
        v = BlockVector(2)
        v[0] = np.arange(5)
        v[1] = np.arange(9)
        self.assertEqual(v.sum(), 46)

    def test_prod(self):
        self.assertEqual(self.ones.prod(), 1)
        v = BlockVector(2)
        a = np.arange(5)
        b = np.arange(9)
        c = np.concatenate([a, b])
        v[0] = a
        v[1] = b
        self.assertEqual(v.prod(), c.prod())

    def test_max(self):
        self.assertEqual(self.ones.max(), 1)
        v = BlockVector(2)
        a = np.arange(5)
        b = np.arange(9)
        c = np.concatenate([a, b])
        v[0] = a
        v[1] = b
        self.assertEqual(v.max(), c.max())

    def test_min(self):
        self.assertEqual(self.ones.min(), 1)
        v = BlockVector(2)
        a = np.arange(5)
        b = np.arange(9)
        c = np.concatenate([a, b])
        v[0] = a
        v[1] = b
        self.assertEqual(v.min(), c.min())

    def test_tolist(self):
        v = BlockVector(2)
        a = np.arange(5)
        b = np.arange(9)
        c = np.concatenate([a, b])
        v[0] = a
        v[1] = b
        self.assertListEqual(v.tolist(), c.tolist())

    def test_flatten(self):
        v = BlockVector(2)
        a = np.arange(5)
        b = np.arange(9)
        c = np.concatenate([a, b])
        v[0] = a
        v[1] = b
        self.assertListEqual(v.flatten().tolist(), c.tolist())

    def test_fill(self):
        v = BlockVector(2)
        a = np.arange(5)
        b = np.arange(9)
        v[0] = a
        v[1] = b
        v.fill(1.0)
        c = np.ones(v.size)
        self.assertListEqual(v.tolist(), c.tolist())

    def test_scale(self):
        v = self.ones
        v.scale(2.0)
        self.assertListEqual(v.tolist(), [2]*v.size)

    def test_shape(self):
        size = sum(self.list_sizes_ones)
        self.assertEqual(self.ones.shape, (size,))
        self.assertRaises(RuntimeError, setattr, self.ones, 'shape', 5)

    def test_bshape(self):
        self.assertEqual(self.ones.bshape, (3,))
        self.assertRaises(RuntimeError, setattr, self.ones, 'bshape', 5)

    def test_size(self):
        size = sum(self.list_sizes_ones)
        self.assertEqual(self.ones.size, size)
        self.assertRaises(RuntimeError, setattr, self.ones, 'size', 5)

    def test_norm(self):
        v = self.ones
        self.assertEqual(v.norm(ord=2), v.size**0.5)

    def test_argmax(self):
        v = BlockVector(2)
        v[0] = np.arange(5)
        v[1] = np.arange(10, 15)
        self.assertEqual(v.argmax(), v.size-1)

    def test_argmin(self):
        v = BlockVector(2)
        v[0] = np.arange(5)
        v[1] = np.arange(10, 15)
        self.assertEqual(v.argmin(), 0)

    def test_cumprod(self):

        v = BlockVector(3)
        v[0] = np.arange(1, 5)
        v[1] = np.arange(5, 10)
        v[2] = np.arange(10, 15)
        c = np.arange(1, 15)
        self.assertListEqual(v.cumprod().tolist(), c.cumprod().tolist())

    def test_cumsum(self):
        v = BlockVector(3)
        v[0] = np.arange(1, 5)
        v[1] = np.arange(5, 10)
        v[2] = np.arange(10, 15)
        c = np.arange(1, 15)
        self.assertListEqual(v.cumsum().tolist(), c.cumsum().tolist())

    def test_clone(self):
        v = self.ones
        w = v.clone()
        self.assertListEqual(w.tolist(), v.tolist())
        x = v.clone(4)
        self.assertListEqual(x.tolist(), [4]*v.size)
        y = x.clone(copy=False)
        y[2][-1] = 6
        d = np.ones(y.size)*4
        d[-1] = 6
        self.assertListEqual(y.tolist(), d.tolist())
        self.assertListEqual(x.tolist(), d.tolist())

    def test_add(self):

        v = self.ones
        v1 = self.ones
        result = v + v1
        self.assertListEqual(result.tolist(), [2]*v.size)
        self.assertRaises(RuntimeError, v.__add__, 1.0)
        self.assertRaises(RuntimeError, v.__add__, v1.flatten())

    def test_radd(self):
        v = self.ones
        v1 = self.ones
        result = v + v1
        self.assertListEqual(result.tolist(), [2] * v.size)
        self.assertRaises(RuntimeError, v.__radd__, 1.0)
        self.assertRaises(RuntimeError, v.__radd__, v1.flatten())

    def test_sub(self):
        v = self.ones
        v1 = self.ones
        result = v - v1
        self.assertListEqual(result.tolist(), [0] * v.size)
        self.assertRaises(RuntimeError, v.__sub__, 1.0)
        self.assertRaises(RuntimeError, v.__sub__, v1.flatten())

    def test_rsub(self):
        v = self.ones
        v1 = self.ones
        result = v1.__rsub__(v)
        self.assertListEqual(result.tolist(), [0] * v.size)
        self.assertRaises(RuntimeError, v.__rsub__, 1.0)
        self.assertRaises(RuntimeError, v.__rsub__, v1.flatten())

    def test_mul(self):
        v = self.ones
        v1 = v.clone(5, copy=True)
        result = v1 * v
        self.assertListEqual(result.tolist(), [5] * v.size)
        self.assertRaises(RuntimeError, v.__mul__, 1.0)
        self.assertRaises(RuntimeError, v.__mul__, v1.flatten())

    def test_rmul(self):
        v = self.ones
        v1 = v.clone(5, copy=True)
        result = v1.__rmul__(v)
        self.assertListEqual(result.tolist(), [5] * v.size)
        self.assertRaises(RuntimeError, v.__rmul__, 1.0)
        self.assertRaises(RuntimeError, v.__rmul__, v1.flatten())

    @unittest.skipIf(sys.version_info < (3, 0), "not supported in this veresion")
    def test_truediv(self):
        v = self.ones
        v1 = v.clone(5, copy=True)
        result = v / v1
        self.assertListEqual(result.tolist(), [1/5] * v.size)
        self.assertRaises(RuntimeError, v.__truediv__, 1.0)
        self.assertRaises(RuntimeError, v.__truediv__, v1.flatten())

    @unittest.skipIf(sys.version_info < (3, 0), "not supported in this veresion")
    def test_rtruediv(self):
        v = self.ones
        v1 = v.clone(5, copy=True)
        result = v1.__rtruediv__(v)
        self.assertListEqual(result.tolist(), [1 / 5] * v.size)
        self.assertRaises(RuntimeError, v.__rtruediv__, 1.0)
        self.assertRaises(RuntimeError, v.__rtruediv__, v1.flatten())

    def test_floordiv(self):
        v = self.ones
        v.fill(2)
        v1 = v.clone(5, copy=True)
        result = v1 // v
        self.assertListEqual(result.tolist(), [5 // 2] * v.size)
        self.assertRaises(RuntimeError, v.__floordiv__, 1.0)
        self.assertRaises(RuntimeError, v.__floordiv__, v1.flatten())

    def test_rfloordiv(self):
        v = self.ones
        v.fill(2)
        v1 = v.clone(5, copy=True)
        result = v.__rfloordiv__(v1)
        self.assertListEqual(result.tolist(), [5 // 2] * v.size)
        self.assertRaises(RuntimeError, v.__floordiv__, 1.0)
        self.assertRaises(RuntimeError, v.__floordiv__, v1.flatten())

    def test_iadd(self):
        v = self.ones
        v += 3
        self.assertListEqual(v.tolist(), [4]*v.size)
        v.fill(1.0)
        v += v
        self.assertListEqual(v.tolist(), [2] * v.size)

    def test_isub(self):
        v = self.ones
        v -= 3
        self.assertListEqual(v.tolist(), [-2] * v.size)
        v.fill(1.0)
        v -= v
        self.assertListEqual(v.tolist(), [0] * v.size)

    def test_imul(self):
        v = self.ones
        v *= 3
        self.assertListEqual(v.tolist(), [3] * v.size)
        v.fill(1.0)
        v *= v
        self.assertListEqual(v.tolist(), [1] * v.size)

    @unittest.skipIf(sys.version_info < (3, 0), "not supported in this veresion")
    def test_itruediv(self):
        v = self.ones
        v /= 3
        self.assertListEqual(v.tolist(), [1/3] * v.size)
        v /= v
        self.assertListEqual(v.tolist(), [1] * v.size)

    def test_getitem(self):
        v = self.ones
        for i, s in enumerate(self.list_sizes_ones):
            self.assertEqual(v[i].size, s)
            self.assertEqual(v[i].shape, (s,))
            self.assertListEqual(v[i].tolist(), np.ones(s).tolist())

    def test_setitem(self):
        v = self.ones
        for i, s in enumerate(self.list_sizes_ones):
            v[i] = np.ones(s) * i
        for i, s in enumerate(self.list_sizes_ones):
            self.assertEqual(v[i].size, s)
            self.assertEqual(v[i].shape, (s,))
            res = np.ones(s) * i
            self.assertListEqual(v[i].tolist(), res.tolist())

    def test_set_blocks(self):
        v = self.ones
        blocks = [np.ones(s)*i for i, s in enumerate(self.list_sizes_ones)]
        v.set_blocks(blocks)
        for i, s in enumerate(self.list_sizes_ones):
            self.assertEqual(v[i].size, s)
            self.assertEqual(v[i].shape, (s,))
            res = np.ones(s) * i
            self.assertListEqual(v[i].tolist(), res.tolist())

    def test_copyfrom(self):
        v = self.ones
        v1 = np.zeros(v.size)
        v.copyfrom(v1)
        self.assertListEqual(v.tolist(), v1.tolist())

        v2 = BlockVector(len(self.list_sizes_ones))
        for i, s in enumerate(self.list_sizes_ones):
            v2[i] = np.ones(s)*i
        v.copyfrom(v2)
        for idx, blk in enumerate(v2):
            self.assertListEqual(blk.tolist(), v2[idx].tolist())

        v3 = BlockVector(2)
        v4 = v.clone(2)
        v3[0] = v4
        v3[1] = np.zeros(3)
        self.assertListEqual(v3.tolist(), v4.tolist() + [0]*3)

    def test_copyto(self):
        v = self.ones
        v2 = BlockVector(len(self.list_sizes_ones))
        v.copyto(v2)
        self.assertListEqual(v.tolist(), v2.tolist())
        v3 = np.zeros(v.size)
        v.copyto(v3)
        self.assertListEqual(v.tolist(), v3.tolist())
        v *= 5
        v.copyto(v2)
        self.assertListEqual(v.tolist(), v2.tolist())


#  ___________________________________________________________________________
#
#  Pyomo: Python Optimization Modeling Objects
#  Copyright 2017 National Technology and Engineering Solutions of Sandia, LLC
#  Under the terms of Contract DE-NA0003525 with National Technology and 
#  Engineering Solutions of Sandia, LLC, the U.S. Government retains certain 
#  rights in this software.
#  This software is distributed under the 3-clause BSD License.
#  ___________________________________________________________________________
#
# Unit Tests for expression generation
#

import os
import re
import six
import sys
from os.path import abspath, dirname
currdir = dirname(abspath(__file__))+os.sep

import pyutilib.th as unittest
from pyutilib.th import nottest

from pyomo.environ import *
from pyomo.core.base import expr_common, expr as EXPR
from pyomo.core.base.var import SimpleVar
from pyomo.core.base.numvalue import potentially_variable, native_types

from pyomo.core.base.expr_pyomo5 import (
    EntangledExpressionError, _getrefcount_available, UNREFERENCED_EXPR_COUNT
)


class TestExpression_EvaluateNumericConstant(unittest.TestCase):

    def setUp(self):
        # Set the type of expression trees used in Pyomo to be Pyomo4 
        EXPR.set_expression_tree_format(expr_common.Mode.pyomo5_trees)
        # Do we expect arithmetic operations to return expressions?
        self.expectExpression = False
        # Do we expect relational tests to return constant expressions?
        self.expectConstExpression = True

    def tearDown(self):
        # Reset the type of expression trees used in Pyomo
        EXPR.set_expression_tree_format(expr_common._default_mode)

    def create(self, val, domain):
        # Create the type of expression term that we are testing
        return NumericConstant(val)

    @nottest
    def value_test(self, exp, val, expectExpression=None):
        """ Test the value of the expression. """
        #
        # Override the class value of 'expectExpression'
        #
        if expectExpression is None:
            expectExpression = self.expectExpression
        #
        # Confirm whether 'exp' is an expression
        #
        self.assertEqual(isinstance(exp,EXPR._ExpressionBase), expectExpression)
        #
        # Confirm that 'exp' has the expected value
        #
        self.assertEqual(value(exp), val)

    @nottest
    def relation_test(self, exp, val, expectConstExpression=None):
        """ Test a relationship expression. """
        #
        # Override the class value of 'expectConstExpression'
        #
        if expectConstExpression is None:
            expectConstExpression = self.expectConstExpression
        #
        # Confirm that this is a relational expression
        #
        self.assertTrue(isinstance(exp, EXPR._ExpressionBase))
        self.assertTrue(exp.is_relational())
        #
        # Check that the expression evaluates correctly
        #
        self.assertEqual(exp(), val)
        #
        # Check that the expression evaluates correctly in a Boolean context
        #
        try:
            if expectConstExpression:
                #
                # The relational expression should be a constant.
                #
                # Check that 'val' equals the boolean value of the expression.
                #
                self.assertEqual(bool(exp), val)
                #
                # The 'chainedInequality' value is None
                #
                self.assertIsNone(EXPR.generate_relational_expression.chainedInequality)
            else:
                #
                # The relational expression may not be constant
                #
                # Check that the expression evaluates to True
                #
                self.assertEqual(bool(exp), True)
                #
                # Check that the 'chainedInequality' value is the current expression
                #
                self.assertIs(exp,EXPR.generate_relational_expression.chainedInequality)
        finally:
            #
            # TODO: Why would we get here?  Because the expression isn't constant?
            #
            # Check that the 'chainedInequality' value is None
            #
            EXPR.generate_relational_expression.chainedInequality = None

    def test_lt(self):
        #
        # Test the 'less than' operator
        #
        a=self.create(1.3, Reals)
        b=self.create(2.0, Reals)
        self.relation_test(a<b, True)
        self.relation_test(a<a, False) 
        self.relation_test(b<a, False)
        self.relation_test(a<2.0, True)
        self.relation_test(a<1.3, False)
        self.relation_test(b<1.3, False)
        self.relation_test(1.3<b, True)
        self.relation_test(1.3<a, False)
        self.relation_test(2.0<a, False)

    def test_gt(self):
        #
        # Test the 'greater than' operator
        #
        a=self.create(1.3, Reals)
        b=self.create(2.0, Reals)
        self.relation_test(a>b, False)
        self.relation_test(a>a, False)
        self.relation_test(b>a, True)
        self.relation_test(a>2.0, False)
        self.relation_test(a>1.3, False)
        self.relation_test(b>1.3, True)
        self.relation_test(1.3>b, False)
        self.relation_test(1.3>a, False)
        self.relation_test(2.0>a, True)

    def test_eq(self):
        #
        # Test the 'equals' operator
        #
        a=self.create(1.3, Reals)
        b=self.create(2.0, Reals)
        self.relation_test(a==b, False, True)
        self.relation_test(a==a, True, True)
        self.relation_test(b==a, False, True)
        self.relation_test(a==2.0, False, True)
        self.relation_test(a==1.3, True, True)
        self.relation_test(b==1.3, False, True)
        self.relation_test(1.3==b, False, True)
        self.relation_test(1.3==a, True, True)
        self.relation_test(2.0==a, False, True)

    def test_arithmetic(self):
        #
        #
        # Test binary arithmetic operators
        #
        a=self.create(-0.5, Reals)
        b=self.create(2.0, Reals)
        self.value_test(a-b, -2.5)
        self.value_test(a+b, 1.5)
        self.value_test(a*b, -1.0)
        self.value_test(b/a, -4.0)
        self.value_test(a**b, 0.25)

        self.value_test(a-2.0, -2.5)
        self.value_test(a+2.0, 1.5)
        self.value_test(a*2.0, -1.0)
        self.value_test(b/(0.5), 4.0)
        self.value_test(a**2.0, 0.25)

        self.value_test(0.5-b, -1.5)
        self.value_test(0.5+b, 2.5)
        self.value_test(0.5*b, 1.0)
        self.value_test(2.0/a, -4.0)
        self.value_test((0.5)**b, 0.25)

        self.value_test(-a, 0.5)
        self.value_test(+a, -0.5, False)        # This doesn't generate an expression
        self.value_test(abs(-a), 0.5)


class TestExpression_EvaluateVarData(TestExpression_EvaluateNumericConstant):

    def setUp(self):
        import pyomo.core.base.var
        #
        # Create Model
        #
        TestExpression_EvaluateNumericConstant.setUp(self)
        #
        # Create model instance
        #
        self.expectExpression = True
        self.expectConstExpression = False

    def create(self, val, domain):
        tmp=pyomo.core.base.var._GeneralVarData()
        tmp.domain = domain
        tmp.value=val
        return tmp


class TestExpression_EvaluateVar(TestExpression_EvaluateNumericConstant):

    def setUp(self):
        import pyomo.core.base.var
        #
        # Create Model
        #
        TestExpression_EvaluateNumericConstant.setUp(self)
        #
        # Create model instance
        #
        self.expectExpression = True
        self.expectConstExpression = False

    def create(self, val, domain):
        tmp=Var(name="unknown",domain=domain)
        tmp.construct()
        tmp.value=val
        return tmp


class TestExpression_EvaluateFixedVar(TestExpression_EvaluateNumericConstant):

    def setUp(self):
        import pyomo.core.base.var
        #
        # Create Model
        #
        TestExpression_EvaluateNumericConstant.setUp(self)
        #
        # Create model instance
        #
        self.expectExpression = True
        self.expectConstExpression = False

    def create(self, val, domain):
        tmp=Var(name="unknown", domain=domain)
        tmp.construct()
        tmp.fixed=True
        tmp.value=val
        return tmp


class TestExpression_EvaluateImmutableParam(TestExpression_EvaluateNumericConstant):

    def setUp(self):
        import pyomo.core.base.var
        #
        # Create Model
        #
        TestExpression_EvaluateNumericConstant.setUp(self)
        #
        # Create model instance
        #
        self.expectExpression = False
        self.expectConstExpression = True

    def create(self, val, domain):
        tmp=Param(default=val, mutable=False, within=domain)
        tmp.construct()
        return tmp


class TestExpression_EvaluateMutableParam(TestExpression_EvaluateNumericConstant):

    def setUp(self):
        import pyomo.core.base.var
        #
        # Create Model
        #
        TestExpression_EvaluateNumericConstant.setUp(self)
        #
        # Create model instance
        #
        self.expectExpression = True
        self.expectConstExpression = False

    def create(self, val, domain):
        tmp=Param(default=val, mutable=True, within=domain)
        tmp.construct()
        return tmp


class TestNumericValue(unittest.TestCase):

    def setUp(self):
        # This class tests the Pyomo 5.x expression trees
        EXPR.set_expression_tree_format(expr_common.Mode.pyomo5_trees)

    def tearDown(self):
        EXPR.set_expression_tree_format(expr_common._default_mode)

    def test_asnum(self):
        try:
            as_numeric(None)
            self.fail("test_asnum - expected TypeError")
        except TypeError:
            pass

    def test_vals(self):
        #
        # If the user specifies a constant, we're assuming it is correct.  Thus,
        # we do not apply the following test.
        #
        ##try:
        ##    NumericConstant(None,None,value='a')
        ##    self.fail("Cannot initialize a constant with a non-numeric value")
        ##except ValueError:
        ##    pass

        #
        # Check that we can get the value from a numeric constant
        #
        a = NumericConstant(1.1)
        b = float(value(a))
        self.assertEqual(b,1.1)
        b = int(value(a))
        self.assertEqual(b,1)

    def test_ops(self):
        #
        # Verify that we can compare the value of numeric constants
        #
        a = NumericConstant(1.1)
        b = NumericConstant(2.2)
        c = NumericConstant(-2.2)
        #a <= b
        self.assertEqual(a() <= b(), True)
        self.assertEqual(a() >= b(), False)
        self.assertEqual(a() == b(), False)
        self.assertEqual(abs(a() + b()-3.3) <= 1e-7, True)
        self.assertEqual(abs(b() - a()-1.1) <= 1e-7, True)
        self.assertEqual(abs(b() * 3-6.6) <= 1e-7, True)
        self.assertEqual(abs(b() / 2-1.1) <= 1e-7, True)
        self.assertEqual(abs(abs(-b())-2.2) <= 1e-7, True)
        self.assertEqual(abs(c()), 2.2)
        #
        # Check that we can get the string representation for a numeric
        # constant.
        #
        self.assertEqual(str(c), "-2.2")


class TestGenerate_SumExpression(unittest.TestCase):

    def setUp(self):
        # This class tests the Pyomo 5.x expression trees
        EXPR.set_expression_tree_format(expr_common.Mode.pyomo5_trees)

    def tearDown(self):
        EXPR.set_expression_tree_format(expr_common._default_mode)

    def test_simpleSum(self):
        # a + b
        m = AbstractModel()
        m.a = Var()
        m.b = Var()
        e = m.a + m.b
        _e = EXPR.compress_expression(e)
        #
        self.assertIs(type(e), EXPR._SumExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], m.a)
        self.assertIs(e._args[1], m.b)
        self.assertEqual(e.size(), 3)
        #
        self.assertIs(type(_e), EXPR._CompressedSumExpression)
        self.assertEqual(len(_e._args), 3)
        self.assertIs(_e._args[0], 0)
        self.assertIs(_e._args[1], m.a)
        self.assertIs(_e._args[2], m.b)
        self.assertEqual(_e.size(), 4)

    def test_constSum(self):
        # a + 5
        m = AbstractModel()
        m.a = Var()
        e = m.a + 5
        _e = EXPR.compress_expression(e)
        #
        self.assertIs(type(e), EXPR._SumExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], 5)
        self.assertIs(e._args[1], m.a)
        self.assertEqual(e.size(), 3)
        #
        self.assertIs(type(_e), EXPR._CompressedSumExpression)
        self.assertEqual(len(_e._args), 2)
        self.assertIs(_e._args[0], 5)
        self.assertIs(_e._args[1], m.a)
        self.assertEqual(_e.size(), 3)

        e = 5 + m.a
        _e = EXPR.compress_expression(e)
        #
        self.assertIs(type(e), EXPR._SumExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], 5)
        self.assertIs(e._args[1], m.a)
        self.assertEqual(e.size(), 3)
        #
        self.assertIs(type(_e), EXPR._CompressedSumExpression)
        self.assertEqual(len(_e._args), 2)
        self.assertIs(_e._args[0], 5)
        self.assertIs(_e._args[1], m.a)
        self.assertEqual(_e.size(), 3)

    def test_nestedSum(self):
        #
        # Check the structure of nested sums
        #
        expectedType = EXPR._SumExpression

        m = AbstractModel()
        m.a = Var()
        m.b = Var()
        m.c = Var()
        m.d = Var()

        #           +
        #          / \
        #         +   5
        #        / \
        #       a   b
        e1 = m.a + m.b
        e = e1 + 5
        _e = EXPR.compress_expression(e)
        #
        self.assertIs(type(e), expectedType)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], 5)
        self.assertIs(e._args[1], e1)
        self.assertEqual(e.size(), 5)
        #
        self.assertIs(type(_e), EXPR._CompressedSumExpression)
        self.assertEqual(len(_e._args), 3)
        self.assertIs(_e._args[0], 5)
        self.assertIs(_e._args[1], m.a)
        self.assertIs(_e._args[2], m.b)
        self.assertEqual(_e.size(), 4)

        #       + 
        #      / \ 
        #     5   +
        #        / \
        #       a   b
        e1 = m.a + m.b
        e = 5 + e1
        _e = EXPR.compress_expression(e)
        #
        self.assertIs(type(e), expectedType)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], 5)
        self.assertIs(e._args[1], e1)
        self.assertEqual(e.size(), 5)
        #
        self.assertIs(type(_e), EXPR._CompressedSumExpression)
        self.assertEqual(len(_e._args), 3)
        self.assertIs(_e._args[0], 5)
        self.assertIs(_e._args[1], m.a)
        self.assertIs(_e._args[2], m.b)
        self.assertEqual(_e.size(), 4)

        #           +
        #          / \
        #         +   c
        #        / \
        #       a   b
        e1 = m.a + m.b
        e = e1 + m.c
        _e = EXPR.compress_expression(e)
        #
        self.assertIs(type(e), expectedType)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], e1)
        self.assertIs(e._args[1], m.c)
        self.assertEqual(e.size(), 5)
        #
        self.assertIs(type(_e), EXPR._CompressedSumExpression)
        self.assertEqual(len(_e._args), 4)
        self.assertIs(_e._args[0], 0)
        self.assertIs(_e._args[1], m.a)
        self.assertIs(_e._args[2], m.b)
        self.assertIs(_e._args[3], m.c)
        self.assertEqual(_e.size(), 5)

        #       + 
        #      / \ 
        #     c   +
        #        / \
        #       a   b
        e1 = m.a + m.b
        e = m.c + e1
        _e = EXPR.compress_expression(e)
        #
        self.assertIs(type(e), EXPR._SumExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], m.c)
        self.assertIs(e._args[1]._args[0], m.a)
        self.assertIs(e._args[1]._args[1], m.b)
        self.assertEqual(e.size(), 5)
        #
        self.assertIs(type(_e), EXPR._CompressedSumExpression)
        self.assertEqual(len(_e._args), 4)
        self.assertIs(_e._args[0], 0)
        self.assertIs(_e._args[1], m.a)
        self.assertIs(_e._args[2], m.b)
        self.assertIs(_e._args[3], m.c)
        self.assertEqual(_e.size(), 5)

        #            +
        #          /   \
        #         +     +
        #        / \   / \
        #       a   b c   d
        e1 = m.a + m.b
        e2 = m.c + m.d
        e = e1 + e2
        _e = EXPR.compress_expression(e)
        #
        self.assertIs(type(e), expectedType)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], e1)
        self.assertIs(e._args[1], e2)
        self.assertEqual(e.size(), 7)
        #
        self.assertIs(type(_e), EXPR._CompressedSumExpression)
        self.assertEqual(len(_e._args), 5)
        self.assertIs(_e._args[0], 0)
        self.assertIs(_e._args[1], m.a)
        self.assertIs(_e._args[2], m.b)
        self.assertIs(_e._args[3], m.c)
        self.assertIs(_e._args[4], m.d)
        self.assertEqual(_e.size(), 6)

    def test_nestedSum2(self):
        #
        # Check the structure of nested sums
        #
        expectedType = EXPR._SumExpression

        m = AbstractModel()
        m.a = Var()
        m.b = Var()
        m.c = Var()
        m.d = Var()

        #           +
        #          / \
        #         *   c
        #        / \
        #       2   +
        #          / \
        #         a   b 
        e1 = m.a + m.b
        e = 2*e1 + m.c
        _e = EXPR.compress_expression(e)

        self.assertIs(type(e), expectedType)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0]._args[1], e1)
        self.assertIs(e._args[1], m.c)
        self.assertEqual(e.size(), 7)

        self.assertIs(type(_e), EXPR._CompressedSumExpression)
        self.assertEqual(len(_e._args), 3)
        self.assertEqual(_e._args[0], 0.0)
        self.assertIs(_e._args[2], m.c)
        self.assertIs(type(_e._args[1]._args[1]), EXPR._MultiSumExpression)

        #         *
        #        / \
        #       3   +
        #          / \
        #         *   c
        #        / \
        #       2   +
        #          / \
        #         a   b 
        e1 = m.a + m.b
        e = 3*(2*e1 + m.c)

        self.assertIs(type(e._args[1]), expectedType)
        self.assertEqual(len(e._args[1]._args), 2)
        self.assertIs(e._args[1]._args[0]._args[1], e1)
        self.assertIs(e._args[1]._args[1], m.c)
        self.assertEqual(e.size(), 9)

        _e = EXPR.compress_expression(e)
        self.assertIs(type(_e), EXPR._ProductExpression)
        self.assertIs(type(_e._args[1]), EXPR._SumExpression)

        _e = EXPR.compress_expression(e, dive=True)
        self.assertIs(type(_e), EXPR._ProductExpression)
        self.assertIs(type(_e._args[1]), EXPR._MultiSumExpression)
        self.assertEqual(len(_e._args[1]._args), 3)
        self.assertEqual(_e._args[1]._args[0], 0.0)
        self.assertIs(_e._args[1]._args[2], m.c)
        self.assertIs(type(_e._args[1]._args[1]._args[1]), EXPR._MultiSumExpression)

    def test_trivialSum(self):
        #
        # Check that adding zero doesn't change the expression
        #
        m = AbstractModel()
        m.a = Var()
        e = m.a + 0
        self.assertIs(type(e), type(m.a))
        self.assertIs(e, m.a)

        e = 0 + m.a
        self.assertIs(type(e), type(m.a))
        self.assertIs(e, m.a)

    def test_sumOf_nestedTrivialProduct(self):
        #
        # Check sums with nested products
        #
        m = AbstractModel()
        m.a = Var()
        m.b = Var()
        m.c = Var()

        #       +
        #      / \
        #     *   b
        #    / \
        #   a   5
        e1 = m.a * 5
        e = e1 + m.b
        _e = EXPR.compress_expression(e)
        #
        self.assertIs(type(e), EXPR._SumExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0]._args[0], 5)
        self.assertIs(e._args[0]._args[1], m.a)
        self.assertIs(e._args[1], m.b)
        self.assertEqual(e.size(), 5)
        #
        self.assertIs(type(_e), EXPR._CompressedSumExpression)
        self.assertEqual(len(_e._args), 3)
        self.assertIs(_e._args[0], 0)
        self.assertIs(_e._args[1]._args[0], 5)
        self.assertIs(_e._args[1]._args[1], m.a)
        self.assertIs(_e._args[2], m.b)
        self.assertEqual(_e.size(), 6)

        #       +
        #      / \
        #     b   *
        #        / \
        #       a   5
        e = m.b + e1
        _e = EXPR.compress_expression(e)
        #
        self.assertIs(type(e), EXPR._SumExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], m.b)
        self.assertIs(e._args[1]._args[0], 5)
        self.assertIs(e._args[1]._args[1], m.a)
        self.assertEqual(e.size(), 5)
        #
        self.assertIs(type(_e), EXPR._CompressedSumExpression)
        self.assertEqual(len(_e._args), 3)
        self.assertIs(_e._args[0], 0)
        self.assertIs(_e._args[1], m.b)
        self.assertIs(_e._args[2]._args[0], 5)
        self.assertIs(_e._args[2]._args[1], m.a)
        self.assertEqual(_e.size(), 6)

        #            +
        #          /   \
        #         *     +
        #        / \   / \
        #       a   5 b   c
        e2 = m.b + m.c
        e = e1 + e2
        _e = EXPR.compress_expression(e)
        #
        self.assertIs(type(e), EXPR._SumExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(type(e._args[0]), EXPR._ProductExpression)
        self.assertIs(type(e._args[1]), EXPR._SumExpression)
        self.assertIs(e._args[0]._args[0], 5)
        self.assertIs(e._args[0]._args[1], m.a)
        self.assertIs(e._args[1]._args[0], m.b)
        self.assertIs(e._args[1]._args[1], m.c)
        self.assertEqual(e.size(), 7)
        #
        self.assertIs(type(_e), EXPR._CompressedSumExpression)
        self.assertEqual(len(_e._args), 4)
        self.assertIs(_e._args[0], 0)
        self.assertIs(_e._args[1], m.b)
        self.assertIs(_e._args[2], m.c)
        self.assertIs(_e._args[3]._args[0], 5)
        self.assertIs(_e._args[3]._args[1], m.a)
        self.assertEqual(_e.size(), 7)

        #            +
        #          /   \
        #         +     *
        #        / \   / \
        #       b   c a   5
        e2 = m.b + m.c
        e = e2 + e1
        _e = EXPR.compress_expression(e)
        #
        self.assertIs(type(e), EXPR._SumExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(type(e._args[0]), EXPR._SumExpression)
        self.assertIs(type(e._args[1]), EXPR._ProductExpression)
        self.assertIs(e._args[0]._args[0], m.b)
        self.assertIs(e._args[0]._args[1], m.c)
        self.assertIs(e._args[1]._args[0], 5)
        self.assertIs(e._args[1]._args[1], m.a)
        self.assertEqual(e.size(), 7)
        #
        self.assertIs(type(_e), EXPR._CompressedSumExpression)
        self.assertEqual(len(_e._args), 4)
        self.assertIs(_e._args[0], 0)
        self.assertIs(_e._args[1], m.b)
        self.assertIs(_e._args[2], m.c)
        self.assertIs(_e._args[3]._args[0], 5)
        self.assertIs(_e._args[3]._args[1], m.a)
        self.assertEqual(_e.size(), 7)

    def test_simpleDiff(self):
        #
        # Check the structure of a simple difference with two variables
        #
        m = AbstractModel()
        m.a = Var()
        m.b = Var()

        #    -
        #   / \
        #  a   b
        e = m.a - m.b
        self.assertIs(type(e), EXPR._SumExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], m.a)
        self.assertIs(type(e._args[1]), EXPR._NegationExpression)
        self.assertIs(e._args[1]._args[0], m.b)

    def test_constDiff(self):
        #
        # Check the structure of a simple difference with a constant
        #
        m = AbstractModel()
        m.a = Var()

        #    -
        #   / \
        #  a   5
        e = m.a - 5
        self.assertIs(type(e), EXPR._SumExpression)
        self.assertEqual(len(e._args), 2)
        self.assertEqual(e._args[0], -5)
        self.assertIs(e._args[1], m.a)
        self.assertEqual(e.size(), 3)

        #    -
        #   / \
        #  5   a
        e = 5 - m.a
        self.assertIs(type(e), EXPR._SumExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], 5)
        self.assertIs(type(e._args[1]), EXPR._NegationExpression)
        self.assertIs(e._args[1]._args[0], m.a)
        self.assertEqual(e.size(), 4)

    def test_nestedDiff(self):
        #
        # Check the structure of nested differences
        #
        m = AbstractModel()
        m.a = Var()
        m.b = Var()
        m.c = Var()
        m.d = Var()

        #       -
        #      / \
        #     -   5
        #    / \
        #   a   b
        e1 = m.a - m.b
        e = e1 - 5
        self.assertIs(type(e), EXPR._SumExpression)
        self.assertIs(e._args[0], -5)
        self.assertIs(e._args[1], e1)
        self.assertEqual(e.size(), 6)

        #       -
        #      / \
        #     5   -
        #        / \
        #       a   b
        e1 = m.a - m.b
        e = 5 - e1
        self.assertIs(type(e), EXPR._SumExpression)
        self.assertIs(e._args[0], 5)
        self.assertIs(type(e._args[1]), EXPR._NegationExpression)
        self.assertIs(e._args[1]._args[0], e1)
        self.assertEqual(e.size(), 7)

        #       -
        #      / \
        #     -   c
        #    / \
        #   a   b
        e1 = m.a - m.b
        e = e1 - m.c
        self.assertIs(type(e), EXPR._SumExpression)
        self.assertIs(e._args[0], e1)
        self.assertIs(type(e._args[1]), EXPR._NegationExpression)
        self.assertIs(e._args[1]._args[0], m.c)
        self.assertEqual(e.size(), 7)

        #       -
        #      / \
        #     c   -
        #        / \
        #       a   b
        e1 = m.a - m.b
        e = m.c - e1
        self.assertIs(type(e), EXPR._SumExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], m.c)
        self.assertIs(e._args[1]._args[0]._args[0], m.a)
        self.assertIs(e._args[1]._args[0]._args[1]._args[0], m.b)
        self.assertEqual(e.size(), 7)

        #            -
        #          /   \
        #         -     -
        #        / \   / \
        #       a   b c   d
        e1 = m.a - m.b
        e2 = m.c - m.d
        e = e1 - e2
        self.assertIs(type(e), EXPR._SumExpression)
        self.assertIs(e._args[0], e1)
        self.assertIs(type(e._args[1]), EXPR._NegationExpression)
        self.assertIs(e._args[1]._args[0], e2)
        self.assertEqual(e.size(), 10)

        #            -
        #          /   \
        #         -     -
        #        / \   / \
        #       c   d a   b
        e1 = m.a - m.b
        e2 = m.c - m.d
        e = e2 - e1
        self.assertIs(type(e), EXPR._SumExpression)
        self.assertIs(e._args[0], e2)
        self.assertIs(type(e._args[1]), EXPR._NegationExpression)
        self.assertIs(e._args[1]._args[0], e1)
        self.assertEqual(e.size(), 10)

    def test_trivialDiff(self):
        #
        # Check that subtracting zero doesn't change the expression
        #
        m = AbstractModel()
        m.a = Var()
        e = m.a - 0
        self.assertIs(type(e), type(m.a))
        self.assertIs(e, m.a)

        # 0 - a
        e = 0 - m.a
        self.assertIs(type(e), EXPR._NegationExpression)
        self.assertEqual(len(e._args), 1)
        self.assertIs(e._args[0], m.a)

    def test_sumOf_nestedTrivialProduct2(self):
        #
        # Check the structure of sum of products
        #
        m = AbstractModel()
        m.a = Var()
        m.b = Var()
        m.c = Var()

        #       -
        #      / \
        #     *   b
        #    / \
        #   a   5
        e1 = m.a * 5
        e = e1 - m.b
        self.assertIs(type(e), EXPR._SumExpression)
        self.assertIs(e._args[0], e1)
        self.assertIs(type(e._args[1]), EXPR._NegationExpression)
        self.assertIs(e._args[1]._args[0], m.b)
        self.assertEqual(e.size(), 6)

        #       -
        #      / \
        #     b   *
        #        / \
        #       a   5
        e1 = m.a * 5
        e = m.b - e1
        self.assertIs(type(e), EXPR._SumExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], m.b)
        self.assertIs(e._args[1]._args[0], e1)
        self.assertEqual(e.size(), 6)

        #            -
        #          /   \
        #         *     -
        #        / \   / \
        #       a   5 b   c
        e1 = m.a * 5
        e2 = m.b - m.c
        e = e1 - e2
        self.assertIs(type(e), EXPR._SumExpression)
        self.assertIs(e._args[0], e1)
        self.assertIs(type(e._args[1]), EXPR._NegationExpression)
        self.assertIs(e._args[1]._args[0], e2)
        self.assertEqual(e.size(), 9)

        #            -
        #          /   \
        #         -     *
        #        / \   / \
        #       b   c a   5
        e1 = m.a * 5
        e2 = m.b - m.c
        e = e2 - e1
        self.assertIs(type(e), EXPR._SumExpression)
        self.assertIs(e._args[0], e2)
        self.assertIs(type(e._args[1]), EXPR._NegationExpression)
        self.assertIs(e._args[1]._args[0], e1)
        self.assertEqual(e.size(), 9)


class TestGenerate_ProductExpression(unittest.TestCase):

    def setUp(self):
        # This class tests the Pyomo 5.x expression trees
        EXPR.set_expression_tree_format(expr_common.Mode.pyomo5_trees)

    def tearDown(self):
        EXPR.set_expression_tree_format(expr_common._default_mode)

    def test_simpleProduct(self):
        #
        # Check the structure of a simple product of variables
        #
        m = AbstractModel()
        m.a = Var()
        m.b = Var()

        #    *
        #   / \
        #  a   b
        e = m.a * m.b
        self.assertIs(type(e), EXPR._ProductExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], m.a)
        self.assertIs(e._args[1], m.b)
        self.assertEqual(e.size(), 3)
        #
        e_ = EXPR.compress_expression(e, dive=True, multiprod=True)
        self.assertIs(type(e_), EXPR._MultiProdExpression)
        self.assertEqual(len(e_._args), 3)
        self.assertEqual(e_._args[0], 1)
        self.assertIs(e_._args[1], m.a)
        self.assertIs(e_._args[2], m.b)
        self.assertEqual(e_.size(), 4)

    def test_constProduct(self):
        #
        # Check the structure of a simple product with a constant
        #
        m = AbstractModel()
        m.a = Var()

        #    *
        #   / \
        #  a   5
        e = m.a * 5
        self.assertIs(type(e), EXPR._ProductExpression)
        self.assertEqual(len(e._args), 2)
        self.assertEqual(e._args[0], 5)
        self.assertIs(e._args[1], m.a)
        self.assertEqual(e.size(), 3)
        #
        e_ = EXPR.compress_expression(e, dive=True, multiprod=True)
        self.assertIs(type(e_), EXPR._MultiProdExpression)
        self.assertEqual(len(e_._args), 2)
        self.assertEqual(e_._args[0], 5)
        self.assertIs(e_._args[1], m.a)
        self.assertEqual(e_.size(), 3)

        #    *
        #   / \
        #  5   a
        e = 5 * m.a
        self.assertIs(type(e), EXPR._ProductExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], 5)
        self.assertIs(e._args[1], m.a)
        self.assertEqual(e.size(), 3)
        #
        e_ = EXPR.compress_expression(e, dive=True, multiprod=True)
        self.assertIs(type(e_), EXPR._MultiProdExpression)
        self.assertEqual(len(e_._args), 2)
        self.assertEqual(e_._args[0], 5)
        self.assertIs(e_._args[1], m.a)
        self.assertEqual(e_.size(), 3)

    def test_nestedProduct(self):
        #
        # Check the structure of nested products
        #
        m = AbstractModel()
        m.a = Var()
        m.b = Var()
        m.c = Var()
        m.d = Var()

        #       *
        #      / \
        #     *   5
        #    / \
        #   a   b
        e1 = m.a * m.b
        e = e1 * 5
        self.assertIs(type(e), EXPR._ProductExpression)
        self.assertEqual(len(e._args), 2)
        self.assertEqual(e._args[0], 5)
        self.assertIs(type(e._args[1]), EXPR._ProductExpression)
        self.assertIs(e._args[1]._args[0], m.a)
        self.assertIs(e._args[1]._args[1], m.b)
        self.assertEqual(e.size(), 5)
        #
        e_ = EXPR.compress_expression(e, dive=True, multiprod=True)
        self.assertIs(type(e_), EXPR._MultiProdExpression)
        self.assertEqual(len(e_._args), 3)
        self.assertEqual(e_._args[0], 5)
        self.assertIs(e_._args[1], m.a)
        self.assertIs(e_._args[2], m.b)
        self.assertEqual(e_.size(), 4)

        #       *
        #      / \
        #     5   *
        #        / \
        #       a   b
        e1 = m.a * m.b
        e = 5 * e1
        self.assertIs(type(e), EXPR._ProductExpression)
        self.assertEqual(len(e._args), 2)
        self.assertEqual(e._args[0], 5)
        self.assertIs(type(e._args[1]), EXPR._ProductExpression)
        self.assertIs(e._args[1]._args[0], m.a)
        self.assertIs(e._args[1]._args[1], m.b)
        self.assertEqual(e.size(), 5)
        #
        e_ = EXPR.compress_expression(e, dive=True, multiprod=True)
        self.assertIs(type(e_), EXPR._MultiProdExpression)
        self.assertEqual(len(e_._args), 3)
        self.assertEqual(e_._args[0], 5)
        self.assertIs(e_._args[1], m.a)
        self.assertIs(e_._args[2], m.b)
        self.assertEqual(e_.size(), 4)

        #       *
        #      / \
        #     *   c
        #    / \
        #   a   b
        e1 = m.a * m.b
        e = e1 * m.c
        self.assertIs(type(e), EXPR._ProductExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[1], m.c)
        self.assertIs(type(e._args[0]), EXPR._ProductExpression)
        self.assertIs(e._args[0]._args[0], m.a)
        self.assertIs(e._args[0]._args[1], m.b)
        self.assertEqual(e.size(), 5)
        #
        e_ = EXPR.compress_expression(e, dive=True, multiprod=True)
        self.assertIs(type(e_), EXPR._MultiProdExpression)
        self.assertEqual(len(e_._args), 4)
        self.assertEqual(e_._args[0], 1)
        self.assertIs(e_._args[1], m.a)
        self.assertIs(e_._args[2], m.b)
        self.assertIs(e_._args[3], m.c)
        self.assertEqual(e_.size(), 5)

        #       *
        #      / \
        #     c   *
        #        / \
        #       a   b
        e1 = m.a * m.b
        e = m.c * e1
        self.assertIs(type(e), EXPR._ProductExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], m.c)
        self.assertIs(type(e._args[1]), EXPR._ProductExpression)
        self.assertIs(e._args[1]._args[0], m.a)
        self.assertIs(e._args[1]._args[1], m.b)
        self.assertEqual(e.size(), 5)
        #
        e_ = EXPR.compress_expression(e, dive=True, multiprod=True)
        self.assertIs(type(e_), EXPR._MultiProdExpression)
        self.assertEqual(len(e_._args), 4)
        self.assertEqual(e_._args[0], 1)
        self.assertIs(e_._args[1], m.c)
        self.assertIs(e_._args[2], m.a)
        self.assertIs(e_._args[3], m.b)
        self.assertEqual(e_.size(), 5)

        #            *
        #          /   \
        #         *     *
        #        / \   / \
        #       a   b c   d
        e1 = m.a * m.b
        e2 = m.c * m.d
        e = e1 * e2
        self.assertIs(type(e), EXPR._ProductExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(type(e._args[0]), EXPR._ProductExpression)
        self.assertIs(type(e._args[1]), EXPR._ProductExpression)
        self.assertIs(e._args[0]._args[0], m.a)
        self.assertIs(e._args[0]._args[1], m.b)
        self.assertIs(e._args[1]._args[0], m.c)
        self.assertIs(e._args[1]._args[1], m.d)
        self.assertEqual(e.size(), 7)
        #
        e_ = EXPR.compress_expression(e, dive=True, multiprod=True)
        self.assertIs(type(e_), EXPR._MultiProdExpression)
        self.assertEqual(len(e_._args), 5)
        self.assertEqual(e_._args[0], 1)
        self.assertIs(e_._args[1], m.a)
        self.assertIs(e_._args[2], m.b)
        self.assertIs(e_._args[3], m.c)
        self.assertIs(e_._args[4], m.d)
        self.assertEqual(e_.size(), 6)

    def test_nestedProduct2(self):
        #
        # Check the structure of nested products
        #
        m = AbstractModel()
        m.a = Var()
        m.b = Var()
        m.c = Var()
        m.d = Var()

        #
        # Check the structure of nested products
        #
        #            *
        #          /   \
        #         +     +
        #        / \   / \
        #       c    +    d
        #           / \
        #          a   b
        e1 = m.a + m.b
        e2 = m.c + e1
        e3 = e1 + m.d
        e = e2 * e3
        _e = EXPR.compress_expression(e)
        #
        self.assertIs(type(_e), EXPR._ProductExpression)
        self.assertEqual(len(_e._args), 2)

        self.assertIs(type(_e._args[0]), EXPR._SumExpression)
        self.assertIs(len(_e._args[0]._args), 2)
        self.assertIs(_e._args[0]._args[0], m.c)
        self.assertEqual(e.size(), 11)

        self.assertIs(type(_e._args[1]), EXPR._SumExpression)
        self.assertIs(len(_e._args[1]._args), 2)
        self.assertIs(_e._args[1]._args[1], m.d)
        self.assertEqual(e.size(), 11)

        #
        # Check the structure of nested products
        #
        #            *
        #          /   \
        #         *     *
        #        / \   / \
        #       c    +    d
        #           / \
        #          a   b
        e1 = m.a + m.b
        e2 = m.c * e1
        e3 = e1 * m.d
        e = e2 * e3
        _e = EXPR.compress_expression(e)
        #
        self.assertEqual(e.size(), 11)
        #
        self.assertIs(type(_e), EXPR._ProductExpression)
        self.assertEqual(len(_e._args), 2)

        self.assertIs(type(_e._args[0]), EXPR._ProductExpression)
        self.assertIs(len(_e._args[0]._args), 2)
        self.assertIs(_e._args[0]._args[0], m.c)

        self.assertIs(type(_e._args[0]._args[1]), EXPR._SumExpression)
        self.assertIs(len(_e._args[0]._args[1]._args), 2)
        self.assertIs(_e._args[0]._args[1]._args[0], m.a)
        self.assertIs(_e._args[0]._args[1]._args[1], m.b)

        self.assertIs(type(_e._args[1]), EXPR._ProductExpression)
        self.assertIs(len(_e._args[1]._args), 2)
        self.assertIs(_e._args[1]._args[1], m.d)

        self.assertIs(type(_e._args[1]._args[0]), EXPR._SumExpression)
        self.assertIs(len(_e._args[1]._args[0]._args), 2)
        self.assertIs(_e._args[1]._args[0]._args[0], m.a)
        self.assertIs(_e._args[1]._args[0]._args[1], m.b)
        self.assertEqual(_e.size(), 11)


    def test_trivialProduct(self):
        #
        # Check that multiplying by zero gives zero
        #
        m = ConcreteModel()
        m.a = Var()
        m.p = Param(initialize=0)
        m.q = Param(initialize=1)

        e = m.a * 0
        self.assertIs(type(e), int)
        self.assertEqual(e, 0)

        e = 0 * m.a
        self.assertIs(type(e), int)
        self.assertEqual(e, 0)

        e = m.a * m.p
        self.assertIs(type(e), int)
        self.assertEqual(e, 0)

        e = m.p * m.a
        self.assertIs(type(e), int)
        self.assertEqual(e, 0)

        #
        # Check that multiplying by one gives the original expression
        #
        e = m.a * 1
        self.assertIs(type(e), type(m.a))
        self.assertIs(e, m.a)

        e = 1 * m.a
        self.assertIs(type(e), type(m.a))
        self.assertIs(e, m.a)

        e = m.a * m.q
        self.assertIs(type(e), type(m.a))
        self.assertIs(e, m.a)

        e = m.q * m.a
        self.assertIs(type(e), type(m.a))
        self.assertIs(e, m.a)

        #
        # Check that numeric constants are simply muliplied out
        #
        e = NumericConstant(3) * NumericConstant(2)
        self.assertIs(type(e), int)
        self.assertEqual(e, 6)

    def test_simpleDivision(self):
        #
        # Check the structure of a simple division with variables
        #
        m = AbstractModel()
        m.a = Var()
        m.b = Var()

        #    /
        #   / \
        #  a   b
        e = m.a / m.b
        self.assertIs(type(e), EXPR._ProductExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], m.a)
        self.assertIs(type(e._args[1]), EXPR._ReciprocalExpression)
        self.assertIs(e._args[1]._args[0], m.b)
        self.assertEqual(e.size(), 4)
        #
        e_ = EXPR.compress_expression(e, dive=True, multiprod=True)
        self.assertIs(type(e_), EXPR._MultiProdExpression)
        self.assertEqual(len(e_._args), 3)
        self.assertEqual(e_._nnum, 2)
        self.assertEqual(e_._args[0], 1)
        self.assertIs(e_._args[1], m.a)
        self.assertIs(e_._args[2], m.b)
        self.assertEqual(e_.size(), 4)

    def test_constDivision(self):
        #
        # Check the structure of a simple division with a constant
        #
        m = AbstractModel()
        m.a = Var()

        #    /
        #   / \
        #  a   5
        e = m.a / 5
        self.assertIs(type(e), EXPR._ProductExpression)
        self.assertEqual(len(e._args), 2)
        self.assertAlmostEqual(e._args[0], 0.2)
        self.assertIs(e._args[1], m.a)
        self.assertEqual(e.size(), 3)
        #
        e_ = EXPR.compress_expression(e, dive=True, multiprod=True)
        self.assertIs(type(e_), EXPR._MultiProdExpression)
        self.assertEqual(len(e_._args), 2)
        self.assertEqual(e_._nnum, 2)
        self.assertEqual(e_._args[0], 0.2)
        self.assertIs(e_._args[1], m.a)
        self.assertEqual(e_.size(), 3)

        #    /
        #   / \
        #  5   a
        e = 5 / m.a
        self.assertIs(type(e), EXPR._ProductExpression)
        self.assertEqual(len(e._args), 2)
        self.assertEqual(e._args[0], 5)
        self.assertIs(type(e._args[1]), EXPR._ReciprocalExpression)
        self.assertIs(e._args[1]._args[0], m.a)
        self.assertEqual(e.size(), 4)
        #
        e_ = EXPR.compress_expression(e, dive=True, multiprod=True)
        self.assertIs(type(e_), EXPR._MultiProdExpression)
        self.assertEqual(len(e_._args), 2)
        self.assertEqual(e_._nnum, 1)
        self.assertEqual(e_._args[0], 5)
        self.assertIs(e_._args[1], m.a)
        self.assertEqual(e_.size(), 3)

    def test_nestedDivision(self):
        #
        # Check the structure of nested divisions
        #
        m = AbstractModel()
        m.a = Var()
        m.b = Var()
        m.c = Var()
        m.d = Var()

        #       /
        #      / \
        #     /   5
        #    / \
        #   a   b
        e1 = m.a / m.b
        e = e1 / 5
        self.assertIs(type(e), EXPR._ProductExpression)
        self.assertEqual(len(e._args), 2)
        self.assertEqual(e._args[0], 1./5)
        self.assertIs(type(e._args[1]), EXPR._ProductExpression)
        self.assertIs(e._args[1]._args[0], m.a)
        self.assertIs(type(e._args[1]._args[1]), EXPR._ReciprocalExpression)
        self.assertIs(e._args[1]._args[1]._args[0], m.b)
        self.assertEqual(e.size(), 6)
        #
        e_ = EXPR.compress_expression(e, dive=True, multiprod=True)
        self.assertIs(type(e_), EXPR._MultiProdExpression)
        self.assertEqual(len(e_._args), 3)
        self.assertEqual(e_._nnum, 2)
        self.assertEqual(e_._args[0], 0.2)
        self.assertIs(e_._args[1], m.a)
        self.assertIs(e_._args[2], m.b)
        self.assertEqual(e_.size(), 4)

        #       /
        #      / \
        #     5   /
        #        / \
        #       a   b
        e1 = m.a / m.b
        e = 5 / e1
        self.assertIs(type(e), EXPR._ProductExpression)
        self.assertEqual(len(e._args), 2)
        self.assertEqual(e._args[0], 5)
        self.assertIs(type(e._args[1]), EXPR._ReciprocalExpression)
        self.assertIs(type(e._args[1]._args[0]), EXPR._ProductExpression)
        self.assertIs(e._args[1]._args[0]._args[0], m.a)
        self.assertIs(e._args[1]._args[0]._args[1]._args[0], m.b)
        self.assertEqual(e.size(), 7)
        #
        e_ = EXPR.compress_expression(e, dive=True, multiprod=True)
        self.assertIs(type(e_), EXPR._MultiProdExpression)
        self.assertEqual(len(e_._args), 3)
        self.assertEqual(e_._nnum, 2)
        self.assertEqual(e_._args[0], 5)
        self.assertIs(e_._args[1], m.b)
        self.assertIs(e_._args[2], m.a)
        self.assertEqual(e_.size(), 4)

        #       /
        #      / \
        #     /   c
        #    / \
        #   a   b
        e1 = m.a / m.b
        e = e1 / m.c
        self.assertIs(type(e), EXPR._ProductExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(type(e._args[1]), EXPR._ReciprocalExpression)
        self.assertIs(e._args[1]._args[0], m.c)
        self.assertIs(type(e._args[0]), EXPR._ProductExpression)
        self.assertIs(e._args[0]._args[0], m.a)
        self.assertIs(type(e._args[0]._args[1]), EXPR._ReciprocalExpression)
        self.assertIs(e._args[0]._args[1]._args[0], m.b)
        self.assertEqual(e.size(), 7)
        #
        e_ = EXPR.compress_expression(e, dive=True, multiprod=True)
        self.assertIs(type(e_), EXPR._MultiProdExpression)
        self.assertEqual(len(e_._args), 4)
        self.assertEqual(e_._nnum, 2)
        self.assertEqual(e_._args[0], 1)
        self.assertIs(e_._args[1], m.a)
        self.assertIs(e_._args[2], m.b)
        self.assertIs(e_._args[3], m.c)
        self.assertEqual(e_.size(), 5)

        #       /
        #      / \
        #     c   /
        #        / \
        #       a   b
        e1 = m.a / m.b
        e = m.c / e1
        self.assertIs(type(e), EXPR._ProductExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], m.c)
        self.assertIs(type(e._args[1]), EXPR._ReciprocalExpression)
        self.assertIs(e._args[1]._args[0]._args[0], m.a)
        self.assertIs(e._args[1]._args[0]._args[1]._args[0], m.b)
        self.assertEqual(e.size(), 7)
        #
        e_ = EXPR.compress_expression(e, dive=True, multiprod=True)
        self.assertIs(type(e_), EXPR._MultiProdExpression)
        self.assertEqual(len(e_._args), 4)
        self.assertEqual(e_._nnum, 3)
        self.assertEqual(e_._args[0], 1)
        self.assertIs(e_._args[1], m.c)
        self.assertIs(e_._args[2], m.b)
        self.assertIs(e_._args[3], m.a)
        self.assertEqual(e_.size(), 5)

        #            /
        #          /   \
        #         /     /
        #        / \   / \
        #       a   b c   d
        e1 = m.a / m.b
        e2 = m.c / m.d
        e = e1 / e2
        self.assertIs(type(e), EXPR._ProductExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(type(e._args[0]), EXPR._ProductExpression)
        self.assertIs(type(e._args[1]), EXPR._ReciprocalExpression)
        self.assertIs(e._args[0]._args[0], m.a)
        self.assertIs(e._args[0]._args[1]._args[0], m.b)
        self.assertIs(e._args[1]._args[0]._args[0], m.c)
        self.assertIs(e._args[1]._args[0]._args[1]._args[0], m.d)
        self.assertEqual(e.size(), 10)
        #
        e_ = EXPR.compress_expression(e, dive=True, multiprod=True)
        self.assertIs(type(e_), EXPR._MultiProdExpression)
        self.assertEqual(len(e_._args), 5)
        self.assertEqual(e_._nnum, 3)
        self.assertEqual(e_._args[0], 1)
        self.assertIs(e_._args[1], m.a)
        self.assertIs(e_._args[2], m.d)
        self.assertIs(e_._args[3], m.b)
        self.assertIs(e_._args[4], m.c)
        self.assertEqual(e_.size(), 6)

    def test_trivialDivision(self):
        #
        # Check that dividing by zero generates an exception
        #
        m = AbstractModel()
        m.a = Var()
        self.assertRaises(ZeroDivisionError, m.a.__div__, 0)

        #
        # Check that dividing zero by anything non-zero gives zero
        #
        e = 0 / m.a
        self.assertIs(type(e), int)
        self.assertAlmostEqual(e, 0.0)

        #
        # Check that dividing by one 1 gives the original expression
        #
        e = m.a / 1
        self.assertIs(type(e), type(m.a))
        self.assertIs(e, m.a)

        #
        # Check the structure dividing 1 by an expression
        #
        e = 1 / m.a
        self.assertIs(type(e), EXPR._ReciprocalExpression)
        self.assertEqual(len(e._args), 1)
        self.assertIs(e._args[0], m.a)

        #
        # Check that dividing two non-zero constants gives a constant
        #
        e = NumericConstant(3) / NumericConstant(2)
        self.assertIs(type(e), float)
        self.assertEqual(e, 1.5)


class TestGenerate_RelationalExpression(unittest.TestCase):

    def setUp(self):
        # This class tests the Pyomo 5.x expression trees
        EXPR.set_expression_tree_format(expr_common.Mode.pyomo5_trees)

        m = AbstractModel()
        m.I = Set()
        m.a = Var()
        m.b = Var()
        m.c = Var()
        m.x = Var(m.I)
        self.m = m

    def tearDown(self):
        EXPR.set_expression_tree_format(expr_common._default_mode)
        self.m = None

    def test_simpleEquality(self):
        #
        # Check the structure of a simple equality statement
        #
        m = self.m
        e = m.a == m.b
        self.assertIs(type(e), EXPR._EqualityExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], m.a)
        self.assertIs(e._args[1], m.b)

    def test_equalityErrors(self):
        #
        # Check equality errors
        #
        m = self.m
        e = m.a == m.b
        #       =
        #      / \
        #     =   5
        #    / \
        #   a   b
        # Python 2.7 supports better testing of exceptions
        if sys.hexversion >= 0x02070000:
            self.assertRaisesRegexp(TypeError, "EqualityExpression .*"
                                   "sub-expressions is a relational",
                                   e.__eq__, m.a)
            self.assertRaisesRegexp(TypeError, "EqualityExpression .*"
                                   "sub-expressions is a relational",
                                   m.a.__eq__, e)

            # NB: cannot test the reverse here: _VarArray (correctly)
            # does not define __eq__
            self.assertRaisesRegexp(TypeError, "Argument .*"
                                    "is an indexed numeric value",
                                    m.a.__eq__, m.x)
        else:
            self.assertRaises(TypeError, e.__eq__, m.a)
            self.assertRaises(TypeError, m.a.__eq__, e)
            self.assertRaises(TypeError, m.a.__eq__, m.x)

        try:
            e == m.a
            self.fail("expected nested equality expression to raise TypeError")
        except TypeError:
            pass

        try:
            m.a == e
            self.fail("expected nested equality expression to raise TypeError")
        except TypeError:
            pass

        #
        # Test expression with an indexed variable
        #
        try:
            m.x == m.a
            self.fail("expected use of indexed variable to raise TypeError")
        except TypeError:
            pass

        try:
            m.a == m.x
            self.fail("expected use of indexed variable to raise TypeError")
        except TypeError:
            pass

    def test_simpleInequality(self):
        #
        # Check the structure of a simple inequality
        #
        m = self.m
        #    <
        #   / \
        #  a   b
        e = m.a < m.b
        self.assertIs(type(e), EXPR._InequalityExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], m.a)
        self.assertIs(e._args[1], m.b)
        self.assertEqual(len(e._strict), 1)
        self.assertEqual(e._strict[0], True)

        #    <=
        #   / \
        #  a   b
        e = m.a <= m.b
        self.assertIs(type(e), EXPR._InequalityExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], m.a)
        self.assertIs(e._args[1], m.b)
        self.assertEqual(len(e._strict), 1)
        self.assertEqual(e._strict[0], False)

        #    >
        #   / \
        #  a   b
        e = m.a > m.b
        self.assertIs(type(e), EXPR._InequalityExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], m.b)
        self.assertIs(e._args[1], m.a)
        self.assertEqual(len(e._strict), 1)
        self.assertEqual(e._strict[0], True)

        #    >=
        #   / \
        #  a   b
        e = m.a >= m.b
        self.assertIs(type(e), EXPR._InequalityExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], m.b)
        self.assertIs(e._args[1], m.a)
        self.assertEqual(len(e._strict), 1)
        self.assertEqual(e._strict[0], False)

    def test_compoundInequality(self):
        m = self.m
        #       <
        #      / \
        #     <   c
        #    / \
        #   a   b
        e = m.a < m.b < m.c
        self.assertIs(type(e), EXPR._InequalityExpression)
        self.assertEqual(len(e._args), 3)
        self.assertIs(e._args[0], m.a)
        self.assertIs(e._args[1], m.b)
        self.assertIs(e._args[2], m.c)
        self.assertEqual(len(e._strict), 2)
        self.assertEqual(e._strict[0], True)
        self.assertEqual(e._strict[1], True)

        #       <=
        #      / \
        #     <=  c
        #    / \
        #   a   b
        e = m.a <= m.b <= m.c
        self.assertIs(type(e), EXPR._InequalityExpression)
        self.assertEqual(len(e._args), 3)
        self.assertIs(e._args[0], m.a)
        self.assertIs(e._args[1], m.b)
        self.assertIs(e._args[2], m.c)
        self.assertEqual(len(e._strict), 2)
        self.assertEqual(e._strict[0], False)
        self.assertEqual(e._strict[1], False)

        #       >
        #      / \
        #     >   c
        #    / \
        #   a   b
        e = m.a > m.b > m.c
        self.assertIs(type(e), EXPR._InequalityExpression)
        self.assertEqual(len(e._args), 3)
        self.assertIs(e._args[0], m.c)
        self.assertIs(e._args[1], m.b)
        self.assertIs(e._args[2], m.a)
        self.assertEqual(len(e._strict), 2)
        self.assertEqual(e._strict[0], True)
        self.assertEqual(e._strict[1], True)

        #       >=
        #      / \
        #     >=  c
        #    / \
        #   a   b
        e = m.a >= m.b >= m.c
        self.assertIs(type(e), EXPR._InequalityExpression)
        self.assertEqual(len(e._args), 3)
        self.assertIs(e._args[0], m.c)
        self.assertIs(e._args[1], m.b)
        self.assertIs(e._args[2], m.a)
        self.assertEqual(len(e._strict), 2)
        self.assertEqual(e._strict[0], False)
        self.assertEqual(e._strict[1], False)

        #       <
        #      / \
        #     <=  1
        #    / \
        #   0   a
        e = 0 <= m.a < 1
        self.assertIs(type(e), EXPR._InequalityExpression)
        self.assertEqual(len(e._args), 3)
        self.assertEqual(e._args[0](), 0)
        self.assertIs(e._args[1], m.a)
        self.assertEqual(e._args[2](), 1)
        self.assertEqual(len(e._strict), 2)
        self.assertEqual(e._strict[0], False)
        self.assertEqual(e._strict[1], True)

        #       <=
        #      / \
        #     <=  0
        #    / \
        #   0   a
        e = 0 <= m.a <= 0
        self.assertIs(type(e), EXPR._EqualityExpression)
        self.assertEqual(len(e._args), 2)
        self.assertIs(e._args[0], m.a)
        self.assertEqual(e._args[1](), 0)

        #       >=
        #      / \
        #     >=  0
        #    / \
        #   0   a
        e = 0 >= m.a >= 0
        self.assertIs(type(e), EXPR._EqualityExpression)
        self.assertEqual(len(e._args), 2)
        self.assertEqual(e._args[0](), 0)
        self.assertIs(e._args[1], m.a)

        #       <=
        #      / \
        #     <   0
        #    / \
        #   0   a
        try:
            0 < m.a <= 0
            self.fail("expected construction of invalid compound inequality: "
                      "combining strict and nonstrict relationships in an "
                      "implicit equality.")
        except TypeError as e:
            self.assertIn(
                "Cannot create a compound inequality with identical upper and "
                "lower bounds using strict inequalities",
                re.sub('\s+',' ',str(e)) )

        #       <
        #      / \
        #     <=  0
        #    / \
        #   0   a
        try:
            0 <= m.a < 0
            self.fail("expected construction of invalid compound inequality: "
                      "combining strict and nonstrict relationships in an "
                      "implicit equality.")
        except TypeError as e:
            self.assertIn(
                "Cannot create a compound inequality with identical upper and "
                "lower bounds using strict inequalities",
                re.sub('\s+',' ',str(e)) )

        #       <
        #      / \
        #     <=  a
        #    / \
        #   0   1
        e = 0 <= 1 < m.a
        self.assertIs(type(e), EXPR._InequalityExpression)
        self.assertEqual(len(e._args), 2)
        self.assertEqual(e._args[0](), 1)
        self.assertIs(e._args[1], m.a)
        self.assertEqual(len(e._strict), 1)
        self.assertEqual(e._strict[0], True)

    def test_eval_compoundInequality(self):
        #
        # Evaluate a compound inequality
        #
        m = ConcreteModel()
        m.x = Var(initialize=0)

        self.assertTrue( 0 <= m.x <= 0 )
        self.assertIsNone(EXPR.generate_relational_expression.chainedInequality)
        self.assertFalse( 1 <= m.x <= 1 )
        self.assertIsNone(EXPR.generate_relational_expression.chainedInequality)
        self.assertFalse( -1 <= m.x <= -1 )
        self.assertIsNone(EXPR.generate_relational_expression.chainedInequality)

        self.assertTrue( 0 <= m.x <= 1 )
        self.assertIsNone(EXPR.generate_relational_expression.chainedInequality)
        self.assertFalse( 1 <= m.x <= 2 )
        self.assertIsNone(EXPR.generate_relational_expression.chainedInequality)
        self.assertTrue( -1 <= m.x <= 0 )
        self.assertIsNone(EXPR.generate_relational_expression.chainedInequality)

    def test_compoundInequality_errors(self):
        #
        # Evaluate errors in a compound inequality
        #
        m = ConcreteModel()
        m.x = Var()

        #       >=
        #      / \
        #     <=  0
        #    / \
        #   0   x
        try:
            0 <= m.x >= 0
            self.fail("expected construction of relational expression to "
                      "generate a TypeError")
        except TypeError as e:
            self.assertIn(
                "Relational expression used in an unexpected Boolean context.",
                str(e) )

        #       >=
        #      / \
        #     <=  1
        #    / \
        #   0   x
        try:
            0 <= m.x >= 1
            self.fail("expected construction of relational expression to "
                      "generate a TypeError")
        except TypeError as e:
            self.assertIn(
                "Attempting to form a compound inequality with two lower bounds",
                str(e) )

        #       <=
        #      / \
        #     >=  1
        #    / \
        #   0   x
        try:
            0 >= m.x <= 1
            self.fail("expected construction of relational expression to "
                      "generate a TypeError")
        except TypeError as e:
            self.assertIn(
                "Attempting to form a compound inequality with two upper bounds",
                str(e) )

        #
        # Confirm error when 
        self.assertTrue(m.x <= 0)
        self.assertIsNotNone(EXPR.generate_relational_expression.chainedInequality)
        try:
            m.x == 5
            self.fail("expected construction of relational expression to "
                      "generate a TypeError")
        except TypeError as e:
            self.assertIn(
                "Relational expression used in an unexpected Boolean context.",
                str(e) )

        self.assertTrue(m.x <= 0)
        self.assertIsNotNone(EXPR.generate_relational_expression.chainedInequality)
        try:
            m.x*2 <= 5
            self.fail("expected construction of relational expression to "
                      "generate a TypeError")
        except TypeError as e:
            self.assertIn(
                "Relational expression used in an unexpected Boolean context.",
                str(e) )

        #
        # Error because expression is being detected in an unusual context
        #
        self.assertTrue(m.x <= 0)
        self.assertIsNotNone(EXPR.generate_relational_expression.chainedInequality)
        try:
            m.x <= 0
            self.fail("expected construction of relational expression to "
                      "generate a TypeError")
        except TypeError as e:
            self.assertIn(
                "Relational expression used in an unexpected Boolean context.",
                str(e) )

    def test_inequalityErrors(self):
        #
        # Check inequality errors
        #
        m = self.m
        e = m.a <= m.b <= m.c
        e1 = m.a == m.b
        if sys.hexversion >= 0x02070000:
            # Python 2.7 supports better testing of exceptions
            #
            # Check error with indexed variable
            #
            self.assertRaisesRegexp(TypeError, "Argument .*"
                                    "is an indexed numeric value",
                                    m.a.__lt__, m.x)
            self.assertRaisesRegexp(TypeError, "Argument .*"
                                    "is an indexed numeric value",
                                    m.a.__gt__, m.x)

            #
            # Check error with more than two inequalities
            #
            self.assertRaisesRegexp(ValueError, "InequalityExpression .*"
                                   "more than 3 terms",
                                   e.__lt__, m.c)
            self.assertRaisesRegexp(ValueError, "InequalityExpression .*"
                                   "more than 3 terms",
                                   e.__gt__, m.c)

            #
            # Check error when both expressions are relational
            #
            self.assertRaisesRegexp(TypeError, "InequalityExpression .*"
                                   "both sub-expressions are also relational",
                                   e.__lt__, m.a < m.b)
            self.assertRaisesRegexp(TypeError, "InequalityExpression .*"
                                   "sub-expressions is an equality",
                                   m.a.__lt__, e1)
            self.assertRaisesRegexp(TypeError, "InequalityExpression .*"
                                   "sub-expressions is an equality",
                                   m.a.__gt__, e1)
        else:
            self.assertRaises(TypeError, m.a.__lt__, m.x)
            self.assertRaises(TypeError, m.a.__gt__, m.x)
            self.assertRaises(ValueError, e.__lt__, m.c)
            self.assertRaises(ValueError, e.__gt__, m.c)
            self.assertRaises(TypeError, e.__lt__, m.a < m.b)
            self.assertRaises(TypeError, m.a.__lt__, e1)
            self.assertRaises(TypeError, m.a.__gt__, e1)

        #
        # Check error with indexed variable
        #
        try:
            m.x < m.a
            self.fail("expected use of indexed variable to raise TypeError")
        except TypeError:
            pass
        try:
            m.a < m.x
            self.fail("expected use of indexed variable to raise TypeError")
        except TypeError:
            pass

        #
        # Check error with more than two relational expressions
        #
        try:
            e < m.c
            self.fail("expected 4-term inequality to raise ValueError")
        except ValueError:
            pass
        try:
            m.c < e
            self.fail("expected 4-term inequality to raise ValueError")
        except ValueError:
            pass
        try:
            e1 = m.a < m.b
            e < e1
            self.fail("expected inequality of inequalities to raise TypeError")
        except TypeError:
            pass
        try:
            m.a < (m.a == m.b)
            self.fail("expected equality within inequality to raise TypeError")
        except TypeError:
            pass
        try:
            m.a > (m.a == m.b)
            self.fail("expected equality within inequality to raise TypeError")
        except TypeError:
            pass


#class TestPrettyPrinter_oldStyle(unittest.TestCase):
class TestPrettyPrinter_oldStyle(object):

    _save = None

    def setUp(self):
        # This class tests the Pyomo 5.x expression trees
        EXPR.set_expression_tree_format(expr_common.Mode.pyomo5_trees)
        TestPrettyPrinter_oldStyle._save = pyomo.core.base.expr_common.TO_STRING_VERBOSE
        pyomo.core.base.expr_common.TO_STRING_VERBOSE = True

    def tearDown(self):
        EXPR.set_expression_tree_format(expr_common._default_mode)
        pyomo.core.base.expr_common.TO_STRING_VERBOSE = TestPrettyPrinter_oldStyle._save

    def test_sum(self):
        #
        # Print simple sum
        #
        model = ConcreteModel()
        model.a = Var()

        expr = 5 + model.a + model.a
        self.assertEqual("linear( 5 , 2*a )", str(expr))

        expr += 5
        self.assertEqual("linear( 10 , 2*a )", str(expr))

    def test_expr(self):
        #
        # Print simple expressions with products and divisions
        #
        model = ConcreteModel()
        model.a = Var()

        expr = 5 * model.a * model.a
        self.assertEqual("prod( linear( 5*a ) , a )", str(expr))

        # This returns an integer, which has no pprint().
        #expr = expr*0
        #buf = StringIO()
        #EXPR.pprint(ostream=buf)
        #self.assertEqual("0.0", buf.getvalue())

        expr = 5 * model.a / model.a
        self.assertEqual( "div( linear( 5*a ) , a )",
                          str(expr) )

        expr = expr / model.a
        self.assertEqual( "div( div( linear( 5*a ) , a ) , a )",
                          str(expr) )

        expr = 5 * model.a / model.a / 2
        self.assertEqual( "div( div( linear( 5*a ) , a ) , 2 )",
                          str(expr) )

    def test_inequality(self):
        #
        # Print inequalities
        #
        model = ConcreteModel()
        model.a = Var()

        expr = 5 < model.a
        self.assertEqual( "( 5.0  <  a )", str(expr) )

        expr = model.a >= 5
        self.assertEqual( "( 5.0  <=  a )", str(expr) )

        expr = expr < 10
        self.assertEqual( "( 5.0  <=  a  <  10.0 )", str(expr) )

        expr = 5 <= model.a + 5
        self.assertEqual( "( 5.0  <=  linear( 5 , a ) )", str(expr) )

        expr = expr < 10
        self.assertEqual( "( 5.0  <=  linear( 5 , a )  <  10.0 )", str(expr) )

    def test_equality(self):
        #
        # Print equality
        #
        model = ConcreteModel()
        model.a = Var()
        model.b = Param(initialize=5, mutable=True)

        expr = model.a == model.b
        self.assertEqual( "( a  ==  b )", str(expr) )

        expr = model.b == model.a
        self.assertEqual( "( b  ==  a )", str(expr) )

        # NB: since there is no "reverse equality" operator, explicit
        # constants will always show up second.
        expr = 5 == model.a
        self.assertEqual( "( a  ==  5.0 )", str(expr) )

        expr = model.a == 10
        self.assertEqual( "( a  ==  10.0 )", str(expr) )

        expr = 5 == model.a + 5
        self.assertEqual( "( linear( 5 , a )  ==  5.0 )", str(expr) )

        expr = model.a + 5 == 5
        self.assertEqual( "( linear( 5 , a )  ==  5.0 )", str(expr) )

    def test_small_expression(self):
        #
        # Print complex
        #
        model = AbstractModel()
        model.a = Var()
        model.b = Param(initialize=2, mutable=True)
        instance=model.create_instance()
        expr = instance.a+1
        expr = expr-1
        expr = expr*instance.a
        expr = expr/instance.a
        expr = expr**instance.b
        expr = 1-expr
        expr = 1+expr
        expr = 2*expr
        expr = 2/expr
        expr = 2**expr
        expr = - expr
        expr = + expr
        expr = abs(expr)
        self.assertEqual(
            "abs( neg( pow( 2 , div( 2 , prod( 2 , "
            "sum( 1 , neg( pow( div( prod( linear( a ) , a ) , a ) , b ) ) , 1"
            " ) ) ) ) ) )",
            str(expr) )


#class TestPrettyPrinter_newStyle(unittest.TestCase):
class TestPrettyPrinter_newStyle(object):

    _save = None

    def setUp(self):
        # This class tests the Pyomo 5.x expression trees
        EXPR.set_expression_tree_format(expr_common.Mode.pyomo5_trees)
        TestPrettyPrinter_oldStyle._save = pyomo.core.base.expr_common.TO_STRING_VERBOSE
        pyomo.core.base.expr_common.TO_STRING_VERBOSE = False

    def tearDown(self):
        EXPR.set_expression_tree_format(expr_common._default_mode)
        pyomo.core.base.expr_common.TO_STRING_VERBOSE = TestPrettyPrinter_oldStyle._save

    def test_sum(self):
        #
        # Print sum
        #
        model = ConcreteModel()
        model.a = Var()

        expr = 5 + model.a + model.a
        self.assertIs(type(expr), EXPR._SumExpression)
        self.assertEqual("5 + a + a", str(expr))

        expr += 5
        self.assertIs(type(expr), EXPR._SumExpression)
        self.assertEqual("5 + a + a + 5", str(expr))

    def test_prod(self):
        #
        # Print expressions
        #
        model = ConcreteModel()
        model.a = Var()

        expr = 5 * model.a * model.a
        self.assertEqual("5*a * a", str(expr))

        # This returns an integer, which has no pprint().
        #expr = expr*0
        #buf = StringIO()
        #EXPR.pprint(ostream=buf)
        #self.assertEqual("0.0", buf.getvalue())

        expr = 5 * model.a / model.a
        self.assertEqual( "( 5*a ) / a",
                          str(expr) )

        expr = expr / model.a
        self.assertEqual( "( 5*a ) / a / a",
                          str(expr) )

        expr = 5 * model.a / (model.a * model.a)
        self.assertEqual( "( 5*a ) / ( a * a )",
                          str(expr) )

        expr = 5 * model.a / model.a / 2
        self.assertEqual( "( 5*a ) / a / 2",
                          str(expr) )

    def test_inequality(self):
        #
        # Print inequalities
        #
        model = ConcreteModel()
        model.a = Var()

        expr = 5 < model.a
        self.assertEqual( "5.0  <  a", str(expr) )

        expr = model.a >= 5
        self.assertEqual( "5.0  <=  a", str(expr) )

        expr = expr < 10
        self.assertEqual( "5.0  <=  a  <  10.0", str(expr) )

        expr = 5 <= model.a + 5
        self.assertEqual( "5.0  <=  5 + a", str(expr) )

        expr = expr < 10
        self.assertEqual( "5.0  <=  5 + a  <  10.0", str(expr) )

    def test_equality(self):
        #
        # Print equalities
        #
        model = ConcreteModel()
        model.a = Var()
        model.b = Param(initialize=5, mutable=True)

        expr = model.a == model.b
        self.assertEqual( "a  ==  b", str(expr) )

        expr = model.b == model.a
        self.assertEqual( "b  ==  a", str(expr) )

        # NB: since there is no "reverse equality" operator, explicit
        # constants will always show up second.
        expr = 5 == model.a
        self.assertEqual( "a  ==  5.0", str(expr) )

        expr = model.a == 10
        self.assertEqual( "a  ==  10.0", str(expr) )

        expr = 5 == model.a + 5
        self.assertEqual( "5 + a  ==  5.0", str(expr) )

        expr = model.a + 5 == 5
        self.assertEqual( "5 + a  ==  5.0", str(expr) )

    def test_linear(self):
        #
        # Print linear
        #
        m = ConcreteModel()
        m.x = Var()
        m.y = Var()
        m.p = Param(initialize=2, mutable=True)

        expr = m.x - m.p*m.y
        self.assertEqual( "x - p*y", str(expr) )

        expr = m.x - m.p*m.y + 5
        self.assertIs(type(expr), EXPR._SumExpression)
        self.assertEqual( "x - p*y + 5", str(expr) )

        expr = m.x - m.p*m.y - 5
        self.assertIs(type(expr), EXPR._SumExpression)
        self.assertEqual( "x - p*y + -5", str(expr) )

        expr = m.x - m.p*m.y - 5 + m.p
        self.assertIs(type(expr), EXPR._SumExpression)
        self.assertEqual( "x - p*y + -5 + p", str(expr) )

    def test_small_expression(self):
        #
        # Print complex expression
        #
        model = AbstractModel()
        model.a = Var()
        model.b = Param(initialize=2, mutable=True)
        instance=model.create_instance()
        expr = instance.a+1
        expr = expr-1
        expr = expr*instance.a
        expr = expr/instance.a
        expr = expr**instance.b
        expr = 1-expr
        expr = 1+expr
        expr = 2*expr
        expr = 2/expr
        expr = 2**expr
        expr = - expr
        expr = + expr
        expr = abs(expr)
        self.assertEqual(
            "abs( - ( 2**( 2 / ( 2 * ( 1 - ( ( a * a ) / a )**b + 1 ) ) ) ) )",
            str(expr) )

    def test_large_expression(self):
        #
        # Diff against a large model
        #
        def c1_rule(model):
            return (1.0,model.b[1],None)
        def c2_rule(model):
            return (None,model.b[1],0.0)
        def c3_rule(model):
            return (0.0,model.b[1],1.0)
        def c4_rule(model):
            return (3.0,model.b[1])
        def c5_rule(model, i):
            return (model.b[i],0.0)

        def c6a_rule(model):
            return 0.0 <= model.c
        def c7a_rule(model):
            return model.c <= 1.0
        def c7b_rule(model):
            return model.c >= 1.0
        def c8_rule(model):
            return model.c == 2.0
        def c9a_rule(model):
            return model.A+model.A <= model.c
        def c9b_rule(model):
            return model.A+model.A >= model.c
        def c10a_rule(model):
            return model.c <= model.B+model.B
        def c11_rule(model):
            return model.c == model.A+model.B
        def c15a_rule(model):
            return model.A <= model.A*model.d
        def c16a_rule(model):
            return model.A*model.d <= model.B

        def c12_rule(model):
            return model.c == model.d
        def c13a_rule(model):
            return model.c <= model.d
        def c14a_rule(model):
            return model.c >= model.d

        def cl_rule(model, i):
            if i > 10:
                return ConstraintList.End
            return i* model.c >= model.d

        def o2_rule(model, i):
            return model.b[i]
        model=AbstractModel()
        model.a = Set(initialize=[1,2,3])
        model.b = Var(model.a,initialize=1.1,within=PositiveReals)
        model.c = Var(initialize=2.1, within=PositiveReals)
        model.d = Var(initialize=3.1, within=PositiveReals)
        model.e = Var(initialize=4.1, within=PositiveReals)
        model.A = Param(default=-1, mutable=True)
        model.B = Param(default=-2, mutable=True)
        #model.o1 = Objective()
        model.o2 = Objective(model.a,rule=o2_rule)
        model.o3 = Objective(model.a,model.a)
        model.c1 = Constraint(rule=c1_rule)
        model.c2 = Constraint(rule=c2_rule)
        model.c3 = Constraint(rule=c3_rule)
        model.c4 = Constraint(rule=c4_rule)
        model.c5 = Constraint(model.a,rule=c5_rule)

        model.c6a = Constraint(rule=c6a_rule)
        model.c7a = Constraint(rule=c7a_rule)
        model.c7b = Constraint(rule=c7b_rule)
        model.c8 = Constraint(rule=c8_rule)
        model.c9a = Constraint(rule=c9a_rule)
        model.c9b = Constraint(rule=c9b_rule)
        model.c10a = Constraint(rule=c10a_rule)
        model.c11 = Constraint(rule=c11_rule)
        model.c15a = Constraint(rule=c15a_rule)
        model.c16a = Constraint(rule=c16a_rule)

        model.c12 = Constraint(rule=c12_rule)
        model.c13a = Constraint(rule=c13a_rule)
        model.c14a = Constraint(rule=c14a_rule)

        model.cl = ConstraintList(rule=cl_rule)

        instance=model.create_instance()
        OUTPUT=open(currdir+"varpprint.out","w")
        instance.pprint(ostream=OUTPUT)
        OUTPUT.close()
        self.assertFileEqualsBaseline( currdir+"varpprint.out",
                                       currdir+"varpprint.txt" )


#
# TODO:What is this checking?
#
class TestInplaceExpressionGeneration(unittest.TestCase):

    def setUp(self):
        # This class tests the Pyomo 5.x expression trees
        EXPR.set_expression_tree_format(expr_common.Mode.pyomo5_trees)

        m = AbstractModel()
        m.a = Var()
        m.b = Var()
        self.m = m

    def tearDown(self):
        EXPR.set_expression_tree_format(expr_common._default_mode)
        self.m = None

    def test_iadd(self):
        m = self.m
        x = 0

        x += m.a
        self.assertIs(type(x), type(m.a))

        x += m.a
        self.assertIs(type(x), EXPR._SumExpression)
        self.assertEqual(len(x._args), 2)

        x += m.b
        self.assertIs(type(x), EXPR._SumExpression)
        self.assertEqual(len(x._args), 2)


    def test_isub(self):
        m = self.m

        x = m.a
        x -= 0
        self.assertIs(type(x), type(m.a))

        x = 0
        x -= m.a
        self.assertIs(type(x), EXPR._NegationExpression)
        self.assertEqual(len(x._args), 1)

        x -= m.a
        self.assertIs(type(x), EXPR._SumExpression)
        self.assertEqual(len(x._args), 2)

        x -= m.a
        self.assertIs(type(x), EXPR._SumExpression)
        self.assertEqual(len(x._args), 2)

        x -= m.b
        self.assertIs(type(x), EXPR._SumExpression)
        self.assertEqual(len(x._args), 2)

    def test_imul(self):
        m = self.m
        x = 1

        x *= m.a
        self.assertIs(type(x), type(m.a))

        x *= m.a
        self.assertIs(type(x), EXPR._ProductExpression)
        self.assertEqual(len(x._args), 2)

        x *= m.a
        self.assertIs(type(x), EXPR._ProductExpression)
        self.assertEqual(len(x._args), 2)

    def test_idiv(self):
        m = self.m
        x = 1

        x /= m.a
        self.assertIs(type(x), EXPR._ReciprocalExpression)
        self.assertIs(x._args[0], m.a)

        x /= m.a
        self.assertIs(type(x), EXPR._ProductExpression)
        self.assertIs(type(x._args[1]), EXPR._ReciprocalExpression)
        self.assertIs(x._args[1]._args[0], m.a)

    def test_ipow(self):
        m = self.m
        x = 1

        x **= m.a
        self.assertIs(type(x), EXPR._PowExpression)
        self.assertEqual(len(x._args), 2)
        self.assertEqual(value(x._args[0]), 1)
        self.assertIs(x._args[1], m.a)

        x **= m.b
        self.assertIs(type(x), EXPR._PowExpression)
        self.assertEqual(len(x._args), 2)
        self.assertIs(type(x._args[0]), EXPR._PowExpression)
        self.assertIs(x._args[1], m.b)
        self.assertEqual(len(x._args), 2)
        self.assertEqual(value(x._args[0]._args[0]), 1)
        self.assertIs(x._args[0]._args[1], m.a)

        # If someone else holds a reference to the expression, we still
        # need to clone it:
        x = 1 ** m.a
        y = x
        x **= m.b
        self.assertIs(type(y), EXPR._PowExpression)
        self.assertEqual(len(y._args), 2)
        self.assertEqual(value(y._args[0]), 1)
        self.assertIs(y._args[1], m.a)

        self.assertIs(type(x), EXPR._PowExpression)
        self.assertEqual(len(x._args), 2)
        self.assertIs(type(x._args[0]), EXPR._PowExpression)
        self.assertIs(x._args[1], m.b)
        self.assertEqual(len(x._args), 2)
        self.assertEqual(value(x._args[0]._args[0]), 1)
        self.assertIs(x._args[0]._args[1], m.a)


class TestGeneralExpressionGeneration(unittest.TestCase):

    def setUp(self):
        # This class tests the Pyomo 5.x expression trees
        EXPR.set_expression_tree_format(expr_common.Mode.pyomo5_trees)

    def tearDown(self):
        EXPR.set_expression_tree_format(expr_common._default_mode)

    def test_invalidIndexing(self):
        #
        # Check for errors when generating expressions with invalid indices
        #
        m = AbstractModel()
        m.A = Set()
        m.p = Param(m.A, mutable=True)
        m.x = Var(m.A)
        m.z = Var()

        try:
            m.p * 2
            self.fail("Expected m.p*2 to raise a TypeError")
        except TypeError:
            pass

        try:
            m.x * 2
            self.fail("Expected m.x*2 to raise a TypeError")
        except TypeError:
            pass

        try:
            2 * m.p
            self.fail("Expected 2*m.p to raise a TypeError")
        except TypeError:
            pass

        try:
            2 * m.x
            self.fail("Expected 2*m.x to raise a TypeError")
        except TypeError:
            pass

        try:
            m.z * m.p
            self.fail("Expected m.z*m.p to raise a TypeError")
        except TypeError:
            pass
        except ValueError:
            pass

        try:
            m.z * m.x
            self.fail("Expected m.z*m.x to raise a TypeError")
        except TypeError:
            pass

    def test_negation(self):
        #
        # Test negation logic for various expressions
        #
        m = AbstractModel()
        m.a = Var()
        m.b = Var()

        e = -m.a
        self.assertIs(type(e), EXPR._NegationExpression)
        self.assertEqual(len(e._args), 1)
        self.assertIs(e._args[0], m.a)

        e1 = m.a - m.b
        e = -e1
        self.assertIs(type(e), EXPR._NegationExpression)
        self.assertIs(e._args[0]._args[0], m.a)
        self.assertIs(type(e._args[0]._args[1]), EXPR._NegationExpression)
        self.assertIs(e._args[0]._args[1]._args[0], m.b)

        e1 = m.a * m.b
        e = -e1
        self.assertIs(type(e), EXPR._NegationExpression)
        self.assertIs(e._args[0]._args[0], m.a)
        self.assertIs(e._args[0]._args[1], m.b)

        e1 = sin(m.a)
        e = -e1
        self.assertIs(type(e), EXPR._NegationExpression)
        self.assertIs(type(e._args[0]), EXPR._UnaryFunctionExpression)


class TestExprConditionalContext(unittest.TestCase):

    def setUp(self):
        # This class tests the Pyomo 5.x expression trees
        EXPR.set_expression_tree_format(expr_common.Mode.pyomo5_trees)

    def tearDown(self):
        EXPR.set_expression_tree_format(expr_common._default_mode)
        # Make sure errors here don't bleed over to other tests
        EXPR.generate_relational_expression.chainedInequality = None

    def checkCondition(self, expr, expectedValue):
        try:
            if expr:
                if expectedValue != True:
                    self.fail("__nonzero__ returned the wrong condition value"
                              " (expected %s)" % expectedValue)
            else:
                if expectedValue != False:
                    self.fail("__nonzero__ returned the wrong condition value"
                              " (expected %s)" % expectedValue)
            if expectedValue is None:
                self.fail("Expected ValueError because component was undefined")
        except ValueError:
            if expectedValue is not None:
                raise
        finally:
            EXPR.generate_relational_expression.chainedInequality = None

    def test_immutable_paramConditional(self):
        model = AbstractModel()
        model.p = Param(initialize=1.0, mutable=False)
        #
        # TODO: Inequalities evaluate True when the parameter is unconstructed?
        #
        self.checkCondition(model.p > 0, True)
        self.checkCondition(model.p >= 0, True)
        self.checkCondition(model.p < 1, True)
        self.checkCondition(model.p <= 1, True)
        self.checkCondition(model.p == 0, None)

        instance = model.create_instance()
        #
        # Inequalities evaluate normally when the parameter is initialized
        #
        self.checkCondition(model.p > 0, True)
        self.checkCondition(model.p >= 0, True)
        self.checkCondition(model.p < 1, True)
        self.checkCondition(model.p <= 1, True)
        self.checkCondition(model.p == 0, None)

        instance = model.create_instance()
        self.checkCondition(instance.p > 0, True)
        self.checkCondition(instance.p > 2, False)
        self.checkCondition(instance.p >= 1, True)
        self.checkCondition(instance.p >= 2, False)
        self.checkCondition(instance.p < 2, True)
        self.checkCondition(instance.p < 0, False)
        self.checkCondition(instance.p <= 1, True)
        self.checkCondition(instance.p <= 0, False)
        self.checkCondition(instance.p == 1, True)
        self.checkCondition(instance.p == 2, False)

    def test_immutable_paramConditional_reversed(self):
        model = AbstractModel()
        model.p = Param(initialize=1.0, mutable=False)
        #
        # TODO: Inequalities evaluate True when the parameter is unconstructed?
        #
        self.checkCondition(0 < model.p, True)
        self.checkCondition(0 <= model.p, True)
        self.checkCondition(1 > model.p, True)
        self.checkCondition(1 >= model.p, True)
        self.checkCondition(0 == model.p, None)

        instance = model.create_instance()
        #
        # Inequalities evaluate normally when the parameter is initialized
        #
        self.checkCondition(0 < instance.p, True)
        self.checkCondition(2 < instance.p, False)
        self.checkCondition(1 <= instance.p, True)
        self.checkCondition(instance.p > 0, True)
        self.checkCondition(instance.p > 2, False)
        self.checkCondition(instance.p >= 1, True)
        self.checkCondition(instance.p >= 2, False)
        self.checkCondition(instance.p < 2, True)
        self.checkCondition(instance.p < 0, False)
        self.checkCondition(instance.p <= 1, True)
        self.checkCondition(instance.p <= 0, False)
        self.checkCondition(instance.p == 1, True)
        self.checkCondition(instance.p == 2, False)

    def test_immutable_paramConditional_reversed(self):
        model = AbstractModel()
        model.p = Param(initialize=1.0, mutable=False)
        #
        # TODO: Inequalities evaluate True when the parameter is unconstructed?
        #
        self.checkCondition(0 < model.p, True)
        self.checkCondition(0 <= model.p, True)
        self.checkCondition(1 > model.p, True)
        self.checkCondition(1 >= model.p, True)
        self.checkCondition(0 == model.p, None)

        instance = model.create_instance()
        #
        # Inequalities evaluate normally when the parameter is initialized
        #
        self.checkCondition(0 < instance.p, True)
        self.checkCondition(2 < instance.p, False)
        self.checkCondition(1 <= instance.p, True)
        self.checkCondition(2 <= instance.p, False)
        self.checkCondition(2 > instance.p, True)
        self.checkCondition(0 > instance.p, False)
        self.checkCondition(1 >= instance.p, True)
        self.checkCondition(0 >= instance.p, False)
        self.checkCondition(1 == instance.p, True)
        self.checkCondition(2 == instance.p, False)

    def test_mutable_paramConditional(self):
        model = AbstractModel()
        model.p = Param(initialize=1.0, mutable=True)
        #
        # TODO: Inequalities evaluate True when the parameter is unconstructed?
        #
        self.checkCondition(model.p > 0, True)
        self.checkCondition(model.p >= 0, True)
        self.checkCondition(model.p < 1, True)
        self.checkCondition(model.p <= 1, True)
        self.checkCondition(model.p == 0, None)

        instance = model.create_instance()
        #
        # Inequalities evaluate normally when the parameter is initialized
        #
        self.checkCondition(instance.p > 0, True)
        self.checkCondition(instance.p > 2, True)
        self.checkCondition(instance.p >= 1, True)
        self.checkCondition(instance.p >= 2, True)
        self.checkCondition(instance.p < 2, True)
        self.checkCondition(instance.p < 0, True)
        self.checkCondition(instance.p <= 1, True)
        self.checkCondition(instance.p <= 0, True)
        self.checkCondition(instance.p == 1, True)
        self.checkCondition(instance.p == 2, False)

    def test_mutable_paramConditional_reversed(self):
        model = AbstractModel()
        model.p = Param(initialize=1.0, mutable=True)
        #
        # TODO: Inequalities evaluate True when the parameter is unconstructed?
        #
        self.checkCondition(0 < model.p, True)
        self.checkCondition(0 <= model.p, True)
        self.checkCondition(1 > model.p, True)
        self.checkCondition(1 >= model.p, True)
        self.checkCondition(0 == model.p, None)

        instance = model.create_instance()
        #
        # Inequalities evaluate normally when the parameter is initialized
        #
        self.checkCondition(0 < instance.p, True)
        self.checkCondition(2 < instance.p, True)
        self.checkCondition(1 <= instance.p, True)
        self.checkCondition(2 <= instance.p, True)
        self.checkCondition(2 > instance.p, True)
        self.checkCondition(0 > instance.p, True)
        self.checkCondition(1 >= instance.p, True)
        self.checkCondition(0 >= instance.p, True)
        self.checkCondition(1 == instance.p, True)
        self.checkCondition(2 == instance.p, False)

    def test_varConditional(self):
        model = AbstractModel()
        model.v = Var(initialize=1.0)
        #
        # TODO: Inequalities evaluate True when the variable is unconstructed?
        #
        self.checkCondition(model.v > 0, True)
        self.checkCondition(model.v >= 0, True)
        self.checkCondition(model.v < 1, True)
        self.checkCondition(model.v <= 1, True)
        self.checkCondition(model.v == 0, None)

        instance = model.create_instance()
        #
        # Inequalities evaluate normally when the variable is initialized
        #
        self.checkCondition(instance.v > 0, True)
        self.checkCondition(instance.v > 2, True)
        self.checkCondition(instance.v >= 1, True)
        self.checkCondition(instance.v >= 2, True)
        self.checkCondition(instance.v < 2, True)
        self.checkCondition(instance.v < 0, True)
        self.checkCondition(instance.v <= 1, True)
        self.checkCondition(instance.v <= 0, True)
        self.checkCondition(instance.v == 1, True)
        self.checkCondition(instance.v == 2, False)

    def test_varConditional_reversed(self):
        model = AbstractModel()
        model.v = Var(initialize=1.0)
        #
        # TODO: Inequalities evaluate True when the variable is unconstructed?
        #
        self.checkCondition(0 < model.v, True)
        self.checkCondition(0 <= model.v, True)
        self.checkCondition(1 > model.v, True)
        self.checkCondition(1 >= model.v, True)
        self.checkCondition(0 == model.v, None)

        instance = model.create_instance()
        #
        # Inequalities evaluate normally when the variable is initialized
        #
        self.checkCondition(0 < instance.v, True)
        self.checkCondition(2 < instance.v, True)
        self.checkCondition(1 <= instance.v, True)
        self.checkCondition(2 <= instance.v, True)
        self.checkCondition(2 > instance.v, True)
        self.checkCondition(0 > instance.v, True)
        self.checkCondition(1 >= instance.v, True)
        self.checkCondition(0 >= instance.v, True)
        self.checkCondition(1 == instance.v, True)
        self.checkCondition(2 == instance.v, False)

    def test_eval_sub_varConditional(self):
        model = AbstractModel()
        model.v = Var(initialize=1.0)
        #
        # The value() function generates an exception when the variable is unconstructed!
        #
        try:
            self.checkCondition(value(model.v) > 0, None)
            self.fail("Expected ValueError because component was undefined")
        except ValueError:
            pass
        try:
            self.checkCondition(value(model.v) >= 0, None)
            self.fail("Expected ValueError because component was undefined")
        except ValueError:
            pass
        try:
            self.checkCondition(value(model.v) < 1, None)
            self.fail("Expected ValueError because component was undefined")
        except ValueError:
            pass
        try:
            self.checkCondition(value(model.v) <= 1, None)
            self.fail("Expected ValueError because component was undefined")
        except ValueError:
            pass
        try:
            self.checkCondition(value(model.v) == 0, None)
            self.fail("Expected ValueError because component was undefined")
        except ValueError:
            pass

        instance = model.create_instance()
        #
        # Inequalities evaluate normally when the variable is initialized
        #
        self.checkCondition(value(instance.v) > 0, True)
        self.checkCondition(value(instance.v) > 2, False)
        self.checkCondition(value(instance.v) >= 1, True)
        self.checkCondition(value(instance.v) >= 2, False)
        self.checkCondition(value(instance.v) < 2, True)
        self.checkCondition(value(instance.v) < 0, False)
        self.checkCondition(value(instance.v) <= 1, True)
        self.checkCondition(value(instance.v) <= 0, False)
        self.checkCondition(value(instance.v) == 1, True)
        self.checkCondition(value(instance.v) == 2, False)

    def test_eval_sub_varConditional_reversed(self):
        model = AbstractModel()
        model.v = Var(initialize=1.0)
        #
        # The value() function generates an exception when the variable is unconstructed!
        #
        try:
            self.checkCondition(0 < value(model.v), None)
            self.fail("Expected ValueError because component was undefined")
        except ValueError:
            pass
        try:
            self.checkCondition(0 <= value(model.v), None)
            self.fail("Expected ValueError because component was undefined")
        except ValueError:
            pass
        try:
            self.checkCondition(1 > value(model.v), None)
            self.fail("Expected ValueError because component was undefined")
        except ValueError:
            pass
        try:
            self.checkCondition(1 >= value(model.v), None)
            self.fail("Expected ValueError because component was undefined")
        except ValueError:
            pass
        try:
            self.checkCondition(0 == value(model.v), None)
            self.fail("Expected ValueError because component was undefined")
        except ValueError:
            pass

        instance = model.create_instance()
        #
        # Inequalities evaluate normally when the variable is initialized
        #
        self.checkCondition(0 < value(instance.v), True)
        self.checkCondition(2 < value(instance.v), False)
        self.checkCondition(1 <= value(instance.v), True)
        self.checkCondition(2 <= value(instance.v), False)
        self.checkCondition(2 > value(instance.v), True)
        self.checkCondition(0 > value(instance.v), False)
        self.checkCondition(1 >= value(instance.v), True)
        self.checkCondition(0 >= value(instance.v), False)
        self.checkCondition(1 == value(instance.v), True)
        self.checkCondition(2 == value(instance.v), False)

    def test_eval_varConditional(self):
        model = AbstractModel()
        model.v = Var(initialize=1.0)
        #
        # The value() function generates an exception when the variable is unconstructed!
        #
        try:
            self.checkCondition(value(model.v > 0), None)
            self.fail("Expected ValueError because component was undefined")
        except ValueError:
            pass
        try:
            self.checkCondition(value(model.v >= 0), None)
            self.fail("Expected ValueError because component was undefined")
        except ValueError:
            pass
        try:
            self.checkCondition(value(model.v == 0), None)
            self.fail("Expected ValueError because component was undefined")
        except ValueError:
            pass

        instance = model.create_instance()
        self.checkCondition(value(instance.v > 0), True)
        self.checkCondition(value(instance.v > 2), False)
        self.checkCondition(value(instance.v >= 1), True)
        self.checkCondition(value(instance.v >= 2), False)
        self.checkCondition(value(instance.v == 1), True)
        self.checkCondition(value(instance.v == 2), False)

    def test_eval_varConditional_reversed(self):
        model = AbstractModel()
        model.v = Var(initialize=1.0)
        #
        # The value() function generates an exception when the variable is unconstructed!
        #
        try:
            self.checkCondition(value(0 < model.v), None)
            self.fail("Expected ValueError because component was undefined")
        except ValueError:
            pass
        try:
            self.checkCondition(value(0 <= model.v), None)
            self.fail("Expected ValueError because component was undefined")
        except ValueError:
            pass
        try:
            self.checkCondition(value(0 == model.v), None)
            self.fail("Expected ValueError because component was undefined")
        except ValueError:
            pass

        instance = model.create_instance()
        #
        # Inequalities evaluate normally when the variable is initialized
        #
        self.checkCondition(value(0 < instance.v), True)
        self.checkCondition(value(2 < instance.v), False)
        self.checkCondition(value(1 <= instance.v), True)
        self.checkCondition(value(2 <= instance.v), False)
        self.checkCondition(value(1 == instance.v), True)
        self.checkCondition(value(2 == instance.v), False)


class TestPolynomialDegree(unittest.TestCase):

    def setUp(self):
        # This class tests the Pyomo 5.x expression trees
        EXPR.set_expression_tree_format(expr_common.Mode.pyomo5_trees)
        def d_fn(model):
            return model.c+model.c
        self.model = AbstractModel()
        self.model.a = Var(initialize=1.0)
        self.model.b = Var(initialize=2.0)
        self.model.c = Param(initialize=0, mutable=True)
        self.model.d = Param(initialize=d_fn, mutable=True)
        self.instance = self.model.create_instance()

    def tearDown(self):
        EXPR.set_expression_tree_format(expr_common._default_mode)
        self.model = None
        self.instance = None

    def test_param(self):
        #
        # Check that a parameter has degree 0
        #
        self.assertEqual(self.model.d.polynomial_degree(), 0)

    def test_var(self):
        #
        # Check that a non-fixed variable has degree 1
        #
        self.model.a.fixed = False
        self.assertEqual(self.model.a.polynomial_degree(), 1)
        #
        # Check that a fixed variable has degree 0
        #
        self.model.a.fixed = True
        self.assertEqual(self.model.a.polynomial_degree(), 0)

    def test_simple_sum(self):
        #
        # A sum of parameters has degree 0
        #
        expr = self.model.c + self.model.d
        self.assertEqual(expr.polynomial_degree(), 0)
        #
        # A sum of variables has degree 1
        #
        expr = self.model.a + self.model.b
        self.assertEqual(expr.polynomial_degree(), 1)
        self.model.a.fixed = True
        self.assertEqual(expr.polynomial_degree(), 1)
        self.model.a.fixed = False
        #
        # A sum of fixed variables has degree 0
        #
        expr = self.model.a + self.model.c
        self.assertEqual(expr.polynomial_degree(), 1)
        self.model.a.fixed = True
        self.assertEqual(expr.polynomial_degree(), 0)

    def test_relational_ops(self):
        #
        # TODO: Should a relational expression have a polynomial degree?
        #
        # A relational expression with parameters has degree 0
        #
        expr = self.model.c < self.model.d
        self.assertEqual(expr.polynomial_degree(), 0)
        #
        # A relational expression with variables has degree 1
        #
        expr = self.model.a <= self.model.d
        self.assertEqual(expr.polynomial_degree(), 1)
        #
        # A relational expression with variable products has degree 2
        #
        expr = self.model.a * self.model.a >= self.model.b
        self.assertEqual(expr.polynomial_degree(), 2)
        self.model.a.fixed = True
        self.assertEqual(expr.polynomial_degree(), 1)
        self.model.a.fixed = False
        #
        expr = self.model.a > self.model.a * self.model.b
        self.assertEqual(expr.polynomial_degree(), 2)
        self.model.b.fixed = True
        self.assertEqual(expr.polynomial_degree(), 1)
        self.model.b.fixed = False
        #
        expr = self.model.a == self.model.a * self.model.b
        self.assertEqual(expr.polynomial_degree(), 2)
        self.model.b.fixed = True
        self.assertEqual(expr.polynomial_degree(), 1)

    def test_simple_product(self):
        #
        # A product of parameters has degree 0
        #
        expr = self.model.c * self.model.d
        self.assertEqual(expr.polynomial_degree(), 0)
        #
        # A product of variables has degree 2
        #
        expr = self.model.a * self.model.b
        self.assertEqual(expr.polynomial_degree(), 2)
        #
        # A product of a variable and parameter has degree 1
        #
        expr = self.model.a * self.model.c
        self.assertEqual(expr.polynomial_degree(), 1)
        self.model.a.fixed = True
        self.assertEqual(expr.polynomial_degree(), 0)
        self.model.a.fixed = False
        #
        # A fraction with a variable and parameter has degree 1
        #
        expr = self.model.a / self.model.c
        self.assertEqual(expr.polynomial_degree(), 1)
        #
        # A fraction with a variable in the denominator has degree None.
        # This indicates that it is not a polyomial.
        #
        expr = self.model.c / self.model.a
        self.assertEqual(expr.polynomial_degree(), None)
        self.model.a.fixed = True
        self.assertEqual(expr.polynomial_degree(), 0)
        self.model.a.fixed = False

    def test_nested_expr(self):
        #
        # Verify that nested expressions compute polynomial degrees appropriately
        #
        expr1 = self.model.c * self.model.d
        expr2 = expr1 + expr1
        self.assertEqual(expr2.polynomial_degree(), 0)

        expr1 = self.model.a * self.model.b
        expr2 = expr1 + expr1
        self.assertEqual(expr2.polynomial_degree(), 2)
        self.model.a.fixed = True
        self.assertEqual(expr2.polynomial_degree(), 1)
        self.model.a.fixed = False

        expr1 = self.model.c + self.model.d
        expr2 = expr1 * expr1
        self.assertEqual(expr2.polynomial_degree(), 0)

        expr1 = self.model.a + self.model.b
        expr2 = expr1 * expr1
        self.assertEqual(expr2.polynomial_degree(), 2)
        self.model.a.fixed = True
        self.assertEqual(expr2.polynomial_degree(), 2)
        self.model.b.fixed = True
        self.assertEqual(expr2.polynomial_degree(), 0)

    def test_misc_operators(self):
        #
        # Check that polynomial checks work with Negation
        #
        expr = -(self.model.a * self.model.b)
        self.assertEqual(expr.polynomial_degree(), 2)

    def test_nonpolynomial_abs(self):
        #
        # Check that an expression containing abs() is not a polynomial
        #
        expr1 = abs(self.model.a * self.model.b)
        self.assertEqual(expr1.polynomial_degree(), None)

        expr2 = self.model.a + self.model.b * abs(self.model.b)
        self.assertEqual(expr2.polynomial_degree(), None)

        expr3 = self.model.a * ( self.model.b + abs(self.model.b) )
        self.assertEqual(expr3.polynomial_degree(), None)
        #
        # Fixing variables should turn intrinsic functions into constants
        #
        # Fixing 'a' still leaves a non-constant expression
        #
        self.model.a.fixed = True
        self.assertEqual(expr1.polynomial_degree(), None)
        self.assertEqual(expr2.polynomial_degree(), None)
        self.assertEqual(expr3.polynomial_degree(), None)
        #
        # Fixing 'a' and 'b' creates a constant expression
        #
        self.model.b.fixed = True
        self.assertEqual(expr1.polynomial_degree(), 0)
        self.assertEqual(expr2.polynomial_degree(), 0)
        self.assertEqual(expr3.polynomial_degree(), 0)
        #
        # Fixing 'b' still leaves a non-constant expression for expr1
        #
        self.model.a.fixed = False
        self.assertEqual(expr1.polynomial_degree(), None)
        self.assertEqual(expr2.polynomial_degree(), 1)
        self.assertEqual(expr3.polynomial_degree(), 1)

    def test_nonpolynomial_pow(self):
        m = self.instance
        #
        # A power with a variable exponent is not a polynomial
        #
        expr = pow(m.a, m.b)
        self.assertEqual(expr.polynomial_degree(), None)
        #
        # A power with a constant exponent is not a polynomial
        #
        m.b.fixed = True
        self.assertEqual(expr.polynomial_degree(), 2)
        #
        # A power with a constant base and exponent is a constant
        #
        m.a.fixed = True
        self.assertEqual(expr.polynomial_degree(), 0)
        #
        # A power with a constant base and variable exponent is not a polynomial
        #
        m.b.fixed = False
        self.assertEqual(expr.polynomial_degree(), None)
        #
        # Confirm that pow() expresses the correct degree
        #
        m.a.fixed = False

        expr = pow(m.a, 1)
        self.assertEqual(expr.polynomial_degree(), 1)

        expr = pow(m.a, 2)
        self.assertEqual(expr.polynomial_degree(), 2)

        expr = pow(m.a*m.a, 2)
        self.assertEqual(expr.polynomial_degree(), 4)
        #
        # A non-integer exponent is not a polynomial
        #
        expr = pow(m.a*m.a, 2.1)
        self.assertEqual(expr.polynomial_degree(), None)
        #
        # A negative exponent is not a polynomial
        #
        expr = pow(m.a*m.a, -1)
        self.assertEqual(expr.polynomial_degree(), None)
        #
        # A nonpolynomial base is not a polynomial if the exponent is nonzero
        #
        expr = pow(2**m.a, 1)
        self.assertEqual(expr.polynomial_degree(), None)

        expr = pow(2**m.a, 0)
        self.assertEqual(expr, 1)
        self.assertEqual(as_numeric(expr).polynomial_degree(), 0)

    def test_Expr_if(self):
        m = self.instance
        #
        # When IF conditional is constant, then polynomial degree is propigated
        #
        expr = EXPR.Expr_if(1,m.a,m.a**2)
        self.assertEqual(expr.polynomial_degree(), 1)
        m.a.fixed = True
        self.assertEqual(expr.polynomial_degree(), 0)
        m.a.fixed = False

        expr = EXPR.Expr_if(0,m.a,m.a**2)
        self.assertEqual(expr.polynomial_degree(), 2)
        m.a.fixed = True
        self.assertEqual(expr.polynomial_degree(), 0)
        m.a.fixed = False
        #
        # When IF conditional is variable, then polynomial degree is propagated
        #
        expr = EXPR.Expr_if(m.a,m.b,m.b**2)
        self.assertEqual(expr.polynomial_degree(), None)
        m.a.fixed = True
        m.a.value = 1
        self.assertEqual(expr.polynomial_degree(), 1)


#
# TODO: Confirm that this checks for entangled expressions.
#
class EntangledExpressionErrors(unittest.TestCase):

    def setUp(self):
        # This class tests the Coopr 3.x expression trees
        EXPR.set_expression_tree_format(expr_common.Mode.pyomo5_trees)

    def tearDown(self):
        EXPR.set_expression_tree_format(expr_common._default_mode)

    def test_sumexpr_add_entangled(self):
        x = Var()
        e = x*2 + 1
        e + 1
        #try:
        #    self.fail("Expected EntangledExpressionError")
        #except EntangledExpressionError as exc:
        #    self.assertIn(str(e), str(exc))

    def test_entangled_test1(self):
        self.m = ConcreteModel()
        self.m.a = Var()
        self.m.b = Var()
        self.m.c = Var()
        self.m.d = Var()

        e1 = self.m.a + self.m.b
        e1_ = EXPR.compress_expression(e1)

        #print(e1)
        #print(e1_)
        #print("--")
        e2 = self.m.c + e1_
        e2_ = EXPR.compress_expression(e2)

        #print(e1)
        #print(e1_)
        #print(e2)
        #print(e2_)
        #print("--")
        e3 = self.m.d + e1_
        e3_ = EXPR.compress_expression(e3)

        #print(e1_)
        #print(e2_)
        #print(e3_)
        self.assertEqual( len(e1_._args), 3)
        self.assertEqual( len(e2_._args), 4)
        self.assertEqual( len(e3_._args), 4)


class TestSummationExpression(unittest.TestCase):

    def setUp(self):
        # This class tests the Pyomo 5.x expression trees
        EXPR.set_expression_tree_format(expr_common.Mode.pyomo5_trees)

        self.m = ConcreteModel()
        self.m.I = RangeSet(5)
        self.m.a = Var(self.m.I, initialize=5)
        self.m.b = Var(self.m.I, initialize=10)
        self.m.p = Param(self.m.I, initialize=1, mutable=True)
        self.m.q = Param(self.m.I, initialize=3, mutable=False)

    def tearDown(self):
        EXPR.set_expression_tree_format(expr_common._default_mode)
        self.m = None

    def test_summation1(self):
        e = summation(self.m.a)
        self.assertEqual( e(), 25 )
        self.assertIs(type(e), EXPR._StaticMultiSumExpression)
        self.assertEqual( id(self.m.a[1]), id(e._args[1]) )
        self.assertEqual( id(self.m.a[2]), id(e._args[2]) )
        self.assertEqual(e.size(), 7)

    def test_summation2(self):
        e = summation(self.m.p, self.m.a)
        self.assertEqual( e(), 25 )
        self.assertIs(type(e), EXPR._StaticMultiSumExpression)
        self.assertEqual( id(self.m.a[1]), id(e._args[1]._args[1]) )
        self.assertEqual( id(self.m.a[2]), id(e._args[2]._args[1]) )
        self.assertEqual(e.size(), 17)

    def test_summation3(self):
        e = summation(self.m.q, self.m.a)
        self.assertEqual( e(), 75 )
        self.assertIs(type(e), EXPR._StaticMultiSumExpression)
        self.assertEqual( id(self.m.a[1]), id(e._args[1]._args[1]) )
        self.assertEqual( id(self.m.a[2]), id(e._args[2]._args[1]) )
        self.assertEqual(e.size(), 17)

    def test_summation4(self):
        e = summation(self.m.a, self.m.b)
        self.assertEqual( e(), 250 )
        self.assertIs(type(e), EXPR._StaticMultiSumExpression)
        self.assertEqual( id(self.m.a[1]), id(e._args[1]._args[0]) )
        self.assertEqual( id(self.m.a[2]), id(e._args[2]._args[0]) )
        self.assertEqual(e.size(), 17)

    def test_summation5(self):
        e = summation(self.m.b, denom=self.m.a)
        self.assertEqual( e(), 10 )
        self.assertIs(type(e), EXPR._SumExpression)
        self.assertEqual(e.size(False), 24)

    def test_summation6(self):
        e = summation(self.m.a, denom=self.m.p)
        self.assertEqual( e(), 25 )
        self.assertIs(type(e), EXPR._StaticMultiSumExpression)
        self.assertEqual( id(self.m.a[1]), id(e._args[1]._args[0]) )
        self.assertEqual( id(self.m.a[2]), id(e._args[2]._args[0]) )
        self.assertEqual(e.size(), 22)

    def test_summation7(self):
        e = summation(self.m.p, self.m.q, index=self.m.I)
        self.assertEqual( e(), 15 )
        self.assertIs(type(e), EXPR._StaticMultiSumExpression)
        self.assertEqual( len(e._args), 1)
        self.assertEqual(e.size(False), 20)

    def test_summation_compression(self):
        e1 = summation(self.m.a)
        e2 = summation(self.m.b)
        e = e1+e2
        e_ = EXPR.compress_expression(e)
        self.assertEqual( e_(), 75 )
        self.assertIs(type(e_), EXPR._CompressedSumExpression)
        self.assertEqual( len(e_._args), 3)
        self.assertEqual(e_.size(False), 16)



class TestCloneExpression(unittest.TestCase):

    def setUp(self):
        # This class tests the Pyomo 5.x expression trees
        EXPR.set_expression_tree_format(expr_common.Mode.pyomo5_trees)

        self.m = ConcreteModel()
        self.m.a = Var(initialize=5)
        self.m.b = Var(initialize=10)
        self.m.p = Param(initialize=1, mutable=True)

    def tearDown(self):
        EXPR.set_expression_tree_format(expr_common._default_mode)
        self.m = None

    def test_SumExpression(self):
        expr1 = self.m.a + self.m.b
        expr2 = expr1.clone()
        self.assertEqual( expr1(), 15 )
        self.assertEqual( expr2(), 15 )
        self.assertNotEqual( id(expr1),       id(expr2) )
        self.assertNotEqual( id(expr1._args), id(expr2._args) )
        self.assertEqual( id(expr1._args[0]), id(expr2._args[0]) )
        self.assertEqual( id(expr1._args[1]), id(expr2._args[1]) )
        expr1 += self.m.b
        self.assertEqual( expr1(), 25 )
        self.assertEqual( expr2(), 15 )
        self.assertNotEqual( id(expr1),       id(expr2) )
        self.assertNotEqual( id(expr1._args), id(expr2._args) )
        self.assertEqual( id(expr1._args[1]), id(expr2._args[1]) )
        self.assertEqual( id(expr1._args[1]), id(expr2._args[1]) )

    def test_ProductExpression_mult(self):
        expr1 = self.m.a * self.m.b
        expr2 = expr1.clone()
        self.assertEqual( expr1(), 50 )
        self.assertEqual( expr2(), 50 )
        self.assertNotEqual( id(expr1),      id(expr2) )
        self.assertNotEqual( id(expr1._args),    id(expr2._args) )
        self.assertEqual( id(expr1._args[0]), id(expr2._args[0]) )
        self.assertEqual( id(expr1._args[1]), id(expr2._args[1]) )

        expr1 *= self.m.b
        self.assertEqual( expr1(), 500 )
        self.assertEqual( expr2(), 50 )
        self.assertNotEqual( id(expr1),                 id(expr2) )
        self.assertNotEqual( id(expr1._args),           id(expr2._args) )
        self.assertNotEqual( id(expr1._args[0]._args),     id(expr2._args) )
        self.assertEqual( id(expr1._args[1]),           id(expr2._args[1]) )
        self.assertEqual( id(expr1._args[0]._args[0]),  id(expr2._args[0]) )
        self.assertEqual( id(expr1._args[0]._args[1]),  id(expr2._args[1]) )

        expr1 = self.m.a * (self.m.b + self.m.a)
        expr2 = expr1.clone()
        self.assertEqual( expr1(), 75 )
        self.assertEqual( expr2(), 75 )
        # Note that since one of the args is a sum expression, the _args
        # in the sum is a *list*, which will be duplicated by deepcopy.
        # This will cause the two args in the Product to be different.
        self.assertNotEqual( id(expr1),      id(expr2) )
        self.assertNotEqual( id(expr1._args), id(expr2._args) )
        self.assertEqual( id(expr1._args[0]), id(expr2._args[0]) )
        self.assertNotEqual( id(expr1._args[1]), id(expr2._args[1]) )


    def test_ProductExpression_div(self):
        expr1 = self.m.a / self.m.b
        expr2 = expr1.clone()
        self.assertEqual( expr1(), 0.5 )
        self.assertEqual( expr2(), 0.5 )
        self.assertNotEqual( id(expr1),       id(expr2) )
        self.assertNotEqual( id(expr1._args),    id(expr2._args) )
        self.assertEqual( id(expr1._args[0]), id(expr2._args[0]) )
        self.assertEqual( id(expr1._args[1]._args[0]), id(expr2._args[1]._args[0]) )

        expr1 /= self.m.b
        self.assertEqual( expr1(), 0.05 )
        self.assertEqual( expr2(), 0.5 )
        self.assertNotEqual( id(expr1),                 id(expr2) )
        self.assertNotEqual( id(expr1._args),           id(expr2._args) )
        self.assertNotEqual( id(expr1._args[0]._args),  id(expr2._args) )
        self.assertEqual( id(expr1._args[1]._args[0]),  id(expr2._args[1]._args[0]) )
        self.assertEqual( id(expr1._args[0]._args[0]),  id(expr2._args[0]) )
        self.assertEqual( id(expr1._args[0]._args[1]._args[0]),  id(expr2._args[1]._args[0]) )

        expr1 = self.m.a / (self.m.b + self.m.a)
        expr2 = expr1.clone()
        self.assertEqual( expr1(), 1/3. )
        self.assertEqual( expr2(), 1/3. )
        # Note that since one of the args is a sum expression, the _args
        # in the sum is a *list*, which will be duplicated by deepcopy.
        # This will cause the two args in the Product to be different.
        self.assertNotEqual( id(expr1),      id(expr2) )
        self.assertNotEqual( id(expr1._args), id(expr2._args) )
        self.assertEqual( id(expr1._args[0]), id(expr2._args[0]) )
        self.assertNotEqual( id(expr1._args[1]), id(expr2._args[1]) )

    def test_sumOfExpressions(self):
        expr1 = self.m.a * self.m.b + self.m.a * self.m.a
        expr2 = expr1.clone()
        self.assertEqual(expr1(), 75)
        self.assertEqual(expr2(), 75)
        self.assertNotEqual(id(expr1), id(expr2))
        self.assertNotEqual(id(expr1._args), id(expr2._args))
        self.assertEqual(expr1._args[0](), expr2._args[0]())
        self.assertEqual(expr1._args[1](), expr2._args[1]())
        self.assertNotEqual(id(expr1._args[0]), id(expr2._args[0]))
        self.assertNotEqual(id(expr1._args[1]), id(expr2._args[1]))
        expr1 += self.m.b
        self.assertEqual(expr1(), 85)
        self.assertEqual(expr2(), 75)
        self.assertNotEqual(id(expr1), id(expr2))
        self.assertNotEqual(id(expr1._args), id(expr2._args))
        self.assertEqual(len(expr1._args), 2)
        self.assertEqual(len(expr2._args), 2)
        self.assertEqual(expr1._args[0](), expr2())
        self.assertEqual(expr1._args[1](), 10)
        self.assertNotEqual(id(expr1._args[0]), id(expr2._args[0]))
        self.assertNotEqual(id(expr1._args[1]), id(expr2._args[1]))

    def test_productOfExpressions(self):
        expr1 = (self.m.a + self.m.b) * (self.m.a + self.m.a)
        expr2 = expr1.clone()
        self.assertEqual(expr1(), 150)
        self.assertEqual(expr2(), 150)
        self.assertNotEqual(id(expr1), id(expr2))
        self.assertNotEqual(id(expr1._args), id(expr2._args))
        self.assertNotEqual(id(expr1._args[0]), id(expr2._args[0]))
        self.assertNotEqual(id(expr1._args[1]), id(expr2._args[1]))
        self.assertEqual(expr1._args[0](), expr2._args[0]())
        self.assertEqual(expr1._args[1](), expr2._args[1]())

        self.assertEqual(len(expr1._args[0]._args), 2)
        self.assertEqual(len(expr2._args[0]._args), 2)
        self.assertEqual(len(expr1._args[1]._args), 2)
        self.assertEqual(len(expr2._args[1]._args), 2)

        self.assertIs( expr1._args[0]._args[0],
                       expr2._args[0]._args[0] )
        self.assertIs( expr1._args[0]._args[1],
                       expr2._args[0]._args[1] )
        self.assertIs( expr1._args[1]._args[0],
                       expr2._args[1]._args[0] )

        expr1 *= self.m.b
        self.assertEqual(expr1(), 1500)
        self.assertEqual(expr2(), 150)
        self.assertNotEqual(id(expr1), id(expr2))
        self.assertNotEqual(id(expr1._args[0]), id(expr2._args[0]))
        self.assertNotEqual(id(expr1._args[1]), id(expr2._args[1]))

        self.assertIs(type(expr1._args[0]), type(expr2))
        self.assertEqual(expr1._args[0](), expr2())

        self.assertEqual(len(expr1._args), 2)
        self.assertEqual(len(expr2._args), 2)

    def test_productOfExpressions_div(self):
        expr1 = (self.m.a + self.m.b) / (self.m.a + self.m.a)
        expr2 = expr1.clone()

        self.assertNotEqual(id(expr1), id(expr2))
        self.assertNotEqual(id(expr1._args), id(expr2._args))
        self.assertNotEqual(id(expr1._args[0]), id(expr2._args[0]))
        self.assertNotEqual(id(expr1._args[1]), id(expr2._args[1]))
        self.assertEqual(expr1._args[0](), expr2._args[0]())
        self.assertEqual(expr1._args[1](), expr2._args[1]())

        self.assertEqual(len(expr1._args[0]._args), 2)
        self.assertEqual(len(expr2._args[0]._args), 2)
        self.assertEqual(len(expr1._args[1]._args), 1)
        self.assertEqual(len(expr2._args[1]._args), 1)

        self.assertIs( expr1._args[0]._args[0], expr2._args[0]._args[0] )
        self.assertIs( expr1._args[0]._args[1], expr2._args[0]._args[1] )
        self.assertIs( expr1._args[1]._args[0]._args[0], expr2._args[1]._args[0]._args[0] )
        self.assertIs( expr1._args[1]._args[0]._args[1], expr2._args[1]._args[0]._args[1] )

        expr1 /= self.m.b
        self.assertAlmostEqual(expr1(), .15)
        self.assertAlmostEqual(expr2(), 1.5)
        self.assertNotEqual(id(expr1._args[0]), id(expr2._args[0]))
        self.assertNotEqual(id(expr1._args[1]), id(expr2._args[1]))

        self.assertIs(type(expr1._args[0]), type(expr2))
        self.assertAlmostEqual(expr1._args[0](), expr2())

        self.assertEqual(len(expr1._args), 2)
        self.assertEqual(len(expr2._args), 2)

    def test_Expr_if(self):
        expr1 = EXPR.Expr_if(IF=self.m.a + self.m.b < 20, THEN=self.m.a, ELSE=self.m.b)
        expr2 = expr1.clone()
        self.assertNotEqual(id(expr1), id(expr2))
        self.assertEqual(expr1(), value(self.m.a))
        self.assertEqual(expr2(), value(self.m.a))
        self.assertNotEqual(id(expr1._if), id(expr2._if))
        self.assertEqual(id(expr1._then), id(expr2._then))
        self.assertEqual(id(expr1._else), id(expr2._else))
        self.assertEqual(expr1._if(), expr2._if())
        self.assertEqual(expr1._then(), expr2._then())
        self.assertEqual(expr1._else(), expr2._else())


#
# Fixed               - Expr has a fixed value
# Constant            - Expr only contains constants and immutable parameters
# PotentiallyVariable - Expr contains one or more variables
#
class TestIsFixedIsConstant(unittest.TestCase):

    def setUp(self):
        # This class tests the Pyomo 5.x expression trees
        EXPR.set_expression_tree_format(expr_common.Mode.pyomo5_trees)

        def d_fn(model):
            return model.c+model.c
        self.model = AbstractModel()
        self.model.a = Var(initialize=1.0)
        self.model.b = Var(initialize=2.0)
        self.model.c = Param(initialize=1, mutable=True)
        self.model.d = Param(initialize=d_fn, mutable=True)
        self.model.e = Param(initialize=d_fn, mutable=False)
        self.instance = self.model.create_instance()

    def tearDown(self):
        EXPR.set_expression_tree_format(expr_common._default_mode)
        self.model = None
        self.instance = None

    def test_simple_sum(self):
        #
        # Sum of mutable parameters:  fixed, not constant, not pvar
        #
        expr = self.instance.c + self.instance.d
        self.assertEqual(expr.is_fixed(), True)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), False)
        #
        # Sum of mutable and immutable parameters:  fixed, not constant, not pvar
        #
        expr = self.instance.e + self.instance.d
        self.assertEqual(expr.is_fixed(), True)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), False)
        #
        # Sum of immutable parameters:  fixed, constant, not pvar
        #
        expr = self.instance.e + self.instance.e
        self.assertEqual(is_fixed(expr), True)
        self.assertEqual(is_constant(expr), True)
        self.assertEqual(potentially_variable(expr), False)
        #
        # Sum of unfixed variables:  not fixed, not constant, pvar
        #
        expr = self.instance.a + self.instance.b
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)
        #
        # Sum of fixed and unfixed variables:  not fixed, not constant, pvar
        #
        self.instance.a.fixed = True
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)
        #
        # Sum of fixed variables:  fixed, not constant, pvar
        #
        self.instance.b.fixed = True
        self.assertEqual(expr.is_fixed(), True)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)

    def test_relational_ops(self):
        #
        # Relation of mutable parameters:  fixed, not constant, pvar
        #
        expr = self.instance.c < self.instance.d
        self.assertEqual(expr.is_fixed(), True)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), False)
        #
        # Relation of unfixed variable and mutable parameters:  not fixed, not constant, pvar
        #
        expr = self.instance.a <= self.instance.d
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)
        #
        # Relation of unfixed variables:  not fixed, not constant, pvar
        #
        expr = self.instance.a * self.instance.a >= self.instance.b
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)
        #
        # Relation of fixed and unfixed variables:  not fixed, not constant, pvar
        #
        self.instance.a.fixed = True
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)
        #
        # Relation of fixed variables:  fixed, not constant, pvar
        #
        self.instance.b.fixed = True
        self.assertEqual(expr.is_fixed(), True)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)

    def test_simple_product(self):
        #
        # Product of mutable parameters:  fixed, not constant, not pvar
        #
        expr = self.instance.c * self.instance.d
        self.assertEqual(expr.is_fixed(), True)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), False)
        #
        # Product of unfixed variable and mutable parameter:  not fixed, not constant, pvar
        #
        expr = self.instance.a * self.instance.c
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)
        #
        # Product of unfixed variables:  not fixed, not constant, pvar
        #
        expr = self.instance.a * self.instance.b
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)
        #
        # Product of fixed and unfixed variables:  not fixed, not constant, pvar
        #
        self.instance.a.fixed = True
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)
        #
        # Product of fixed variables:  fixed, not constant, pvar
        #
        self.instance.b.fixed = True
        self.assertEqual(expr.is_fixed(), True)
        self.assertEqual(expr.is_constant(), False)
        self.instance.a.fixed = False
        self.assertEqual(expr._potentially_variable(), True)

        #
        # Fraction of unfixed variable and mutable parameter:  not fixed, not constant, pvar
        #
        expr = self.instance.a / self.instance.c
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)
        #
        # Fraction of fixed variable and mutable parameter:  fixed, not constant, pvar
        #
        self.instance.a.fixed = True
        self.assertEqual(expr.is_fixed(), True)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)
        self.instance.a.fixed = False
        #
        # Fraction of unfixed variable and mutable parameter:  not fixed, not constant, pvar
        #
        expr = self.instance.c / self.instance.a
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)
        #
        # Fraction of fixed variable and mutable parameter:  fixed, not constant, pvar
        #
        self.instance.a.fixed = True
        self.assertEqual(expr.is_fixed(), True)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)

    def test_misc_operators(self):
        #
        # Negation of product of unfixed variables:  not fixed, not constant, pvar
        #
        expr = -(self.instance.a * self.instance.b)
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)

    def test_nonpolynomial_abs(self):
        #
        # abs() is fixed or constant depending on its arguments
        #
        expr1 = abs(self.instance.a * self.instance.b)
        self.assertEqual(expr1.is_fixed(), False)
        self.assertEqual(expr1.is_constant(), False)
        self.assertEqual(expr1._potentially_variable(), True)

        expr2 = self.instance.a + self.instance.b * abs(self.instance.b)
        self.assertEqual(expr2.is_fixed(), False)
        self.assertEqual(expr2.is_constant(), False)
        self.assertEqual(expr2._potentially_variable(), True)

        expr3 = self.instance.a * ( self.instance.b + abs(self.instance.b) )
        self.assertEqual(expr3.is_fixed(), False)
        self.assertEqual(expr3.is_constant(), False)
        self.assertEqual(expr3._potentially_variable(), True)

        #
        # Fixing variables should turn intrinsic functions into constants
        #
        self.instance.a.fixed = True
        self.assertEqual(expr1.is_fixed(), False)
        self.assertEqual(expr1.is_constant(), False)
        self.assertEqual(expr1._potentially_variable(), True)
        self.assertEqual(expr2.is_fixed(), False)
        self.assertEqual(expr2.is_constant(), False)
        self.assertEqual(expr2._potentially_variable(), True)
        self.assertEqual(expr3.is_fixed(), False)
        self.assertEqual(expr3.is_constant(), False)
        self.assertEqual(expr3._potentially_variable(), True)

        self.instance.b.fixed = True
        self.assertEqual(expr1.is_fixed(), True)
        self.assertEqual(expr1.is_constant(), False)
        self.assertEqual(expr1._potentially_variable(), True)
        self.assertEqual(expr2.is_fixed(), True)
        self.assertEqual(expr2.is_constant(), False)
        self.assertEqual(expr2._potentially_variable(), True)
        self.assertEqual(expr3.is_fixed(), True)
        self.assertEqual(expr3.is_constant(), False)
        self.assertEqual(expr3._potentially_variable(), True)

        self.instance.a.fixed = False
        self.assertEqual(expr1.is_fixed(), False)
        self.assertEqual(expr1.is_constant(), False)
        self.assertEqual(expr1._potentially_variable(), True)
        self.assertEqual(expr2.is_fixed(), False)
        self.assertEqual(expr2.is_constant(), False)
        self.assertEqual(expr2._potentially_variable(), True)
        self.assertEqual(expr3.is_fixed(), False)
        self.assertEqual(expr3.is_constant(), False)
        self.assertEqual(expr3._potentially_variable(), True)

    def test_nonpolynomial_pow(self):
        m = self.instance
        #
        # A power with a mutable base and exponent: fixed, not constant, not pvar
        #
        expr = pow(m.d, m.e)
        self.assertEqual(expr.is_fixed(), True)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), False)
        #
        # A power with a variable exponent: not fixed, not constant, pvar
        #
        expr = pow(m.a, m.b)
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)
        #
        # A power with a constant exponent: not fixed, not constant, pvar
        #
        m.b.fixed = True
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)

        m.a.fixed = True
        self.assertEqual(expr.is_fixed(), True)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)

        m.b.fixed = False
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)

        m.a.fixed = False

        expr = pow(m.a, 1)
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)

        expr = pow(m.a, 2)
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)

        expr = pow(m.a*m.a, 2)
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)

        expr = pow(m.a*m.a, 2.1)
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)

        expr = pow(m.a*m.a, -1)
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)

        expr = pow(2**m.a, 1)
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)

        expr = pow(2**m.a, 0)
        self.assertEqual(is_fixed(expr), True)
        self.assertEqual(is_constant(expr), True)
        self.assertEqual(expr, 1)
        self.assertEqual(as_numeric(expr).polynomial_degree(), 0)

    def test_Expr_if(self):
        m = self.instance

        expr = EXPR.Expr_if(1,m.a,m.e)
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)
        m.a.fixed = True
        self.assertEqual(expr.is_fixed(), True)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)
        m.a.fixed = False

        expr = EXPR.Expr_if(0,m.a,m.e)
        self.assertEqual(expr.is_fixed(), True)
        self.assertEqual(expr.is_constant(), True)
        # BUG
        #self.assertEqual(expr._potentially_variable(), False)
        m.a.fixed = True
        self.assertEqual(expr.is_fixed(), True)
        self.assertEqual(expr.is_constant(), True)
        # BUG
        #self.assertEqual(expr._potentially_variable(), False)
        m.a.fixed = False

        expr = EXPR.Expr_if(m.a,m.b,m.b)
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)
        m.a.fixed = True
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)
        m.a.fixed = False

    def test_LinearExpr(self):
        m = self.instance

        expr = m.a + m.b
        self.assertIs(type(expr), EXPR._SumExpression)
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)

        m.a.fix(1)
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)

        m.b.fix(1)
        self.assertEqual(expr.is_fixed(), True)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)

        m.a.unfix()
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)

        m.a.unfix()

        expr -= m.a
        self.assertEqual(expr.is_fixed(), False)   # With a simple tree, the terms do not cancel
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)

        expr -= m.b
        self.assertEqual(expr.is_fixed(), False)
        self.assertEqual(expr.is_constant(), False)
        self.assertEqual(expr._potentially_variable(), True)

    def test_expression(self):
        m = ConcreteModel()
        m.x = Expression()
        e = m.x
        self.assertEqual(e._potentially_variable(), True)
        self.assertEqual(potentially_variable(e), True)

        e = m.x + 1
        self.assertEqual(e._potentially_variable(), True)
        self.assertEqual(potentially_variable(e), True)

        e = m.x**2
        self.assertEqual(e._potentially_variable(), True)
        self.assertEqual(potentially_variable(e), True)

        e = m.x**2/(m.x + 1)
        self.assertEqual(e._potentially_variable(), True)
        self.assertEqual(potentially_variable(e), True)

    def test_misc(self):
        self.assertEqual(potentially_variable(0), False)
        self.assertEqual(potentially_variable('a'), False)
        self.assertEqual(potentially_variable(None), False)


class TestExpressionUtilities(unittest.TestCase):

    def setUp(self):
        # This class tests the Pyomo 5.x expression trees
        EXPR.set_expression_tree_format(expr_common.Mode.pyomo5_trees)

    def tearDown(self):
        EXPR.set_expression_tree_format(expr_common._default_mode)

    def test_identify_vars_numeric(self):
        #
        # There are no variables in a constant expression
        #
        self.assertEqual( list(EXPR.identify_variables(5)), [] )

    def test_identify_vars_params(self):
        m = ConcreteModel()
        m.I = RangeSet(3)
        m.a = Param(initialize=1)
        m.b = Param(m.I, initialize=1, mutable=True)
        #
        # There are no variables in expressions with only parameters
        #
        self.assertEqual( list(EXPR.identify_variables(m.a)), [] )
        self.assertEqual( list(EXPR.identify_variables(m.b[1])), [] )
        self.assertEqual( list(EXPR.identify_variables(m.a+m.b[1])), [] )
        self.assertEqual( list(EXPR.identify_variables(m.a**m.b[1])), [] )
        self.assertEqual( list(EXPR.identify_variables(
            m.a**m.b[1] + m.b[2])), [] )
        self.assertEqual( list(EXPR.identify_variables(
            m.a**m.b[1] + m.b[2]*m.b[3]*m.b[2])), [] )

    def test_identify_vars_vars(self):
        m = ConcreteModel()
        m.I = RangeSet(3)
        m.a = Var(initialize=1)
        m.b = Var(m.I, initialize=1)
        m.x = ExternalFunction(library='foo.so', function='bar')
        #
        # Identify variables in various algebraic expressions
        #
        self.assertEqual( list(EXPR.identify_variables(m.a)), [m.a] )
        self.assertEqual( list(EXPR.identify_variables(m.b[1])), [m.b[1]] )
        self.assertEqual( list(EXPR.identify_variables(m.a+m.b[1])),
                          [ m.a, m.b[1] ] )
        self.assertEqual( list(EXPR.identify_variables(m.a**m.b[1])),
                          [ m.a, m.b[1] ] )
        self.assertEqual( list(EXPR.identify_variables(m.a**m.b[1] + m.b[2])),
                          [ m.a, m.b[1], m.b[2] ] )
        self.assertEqual( list(EXPR.identify_variables(
            m.a**m.b[1] + m.b[2]*m.b[3]*m.b[2])),
                          [ m.a, m.b[1], m.b[2], m.b[3] ] )
        self.assertEqual( list(EXPR.identify_variables(
            m.a**m.b[1] + m.b[2]/m.b[3]*m.b[2])),
                          [ m.a, m.b[1], m.b[2], m.b[3] ] )
        #
        # Identify variables in the arguments to functions
        #
        self.assertEqual( list(EXPR.identify_variables(
            m.x(m.a, 'string_param', 1)*m.b[1] )),
                          [ m.a, m.b[1] ] )
        self.assertEqual( list(EXPR.identify_variables(
            tanh(m.a)*m.b[1] )), [ m.a, m.b[1] ] )
        self.assertEqual( list(EXPR.identify_variables(
            abs(m.a)*m.b[1] )), [ m.a, m.b[1] ] )
        #
        # Check logic for allowing duplicates
        #
        self.assertEqual( list(EXPR.identify_variables(m.a**m.a + m.a)),
                          [ m.a ] )
        self.assertEqual( list(EXPR.identify_variables(m.a**m.a + m.a, allow_duplicates=True)),
                          [ m.a, m.a, m.a,  ] )


class TestMultiArgumentExpressions(unittest.TestCase):

    def setUp(self):
        # This class tests the Pyomo 4 expression trees
        EXPR.set_expression_tree_format(expr_common.Mode.pyomo5_trees)

    def tearDown(self):
        EXPR.set_expression_tree_format(expr_common._default_mode)

    def test_double_sided_ineq(self):
        m = ConcreteModel()
        m.s = Set(initialize=[1.0,2.0,3.0,4.0,5.0])

        m.vmin = Param(m.s, initialize=lambda m,i: i)
        m.vmax = Param(m.s, initialize=lambda m,i: i**2)

        m.v = Var(m.s)

        def _con(m, i):
            return m.vmin[i]**2 <= m.v[i] <= m.vmax[i]**2
        m.con = Constraint(m.s, rule=_con)

        OUT = six.StringIO()
        for i in m.s:
            OUT.write(str(_con(m,i)))
            OUT.write("\n")
        display(m.con, ostream=OUT)

        reference="""v[1.0]  ==  1.0
4.0  <=  v[2.0]  <=  16.0
9.0  <=  v[3.0]  <=  81.0
16.0  <=  v[4.0]  <=  256.0
25.0  <=  v[5.0]  <=  625.0
con : Size=5
    Key : Lower : Body : Upper
    1.0 :   1.0 : None :   1.0
    2.0 :   4.0 : None :  16.0
    3.0 :   9.0 : None :  81.0
    4.0 :  16.0 : None : 256.0
    5.0 :  25.0 : None : 625.0
"""
        self.assertEqual(OUT.getvalue(), reference)


if __name__ == "__main__":
    unittest.main()
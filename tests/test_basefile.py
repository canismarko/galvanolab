from unittest import TestCase

import numpy as np
import pandas as pd
import pint_pandas

from galvanolab.basefile import calculate_capacity
from galvanolab import ureg


class CapacityTestCase(TestCase):
    def test_relative_capacity(self):
        time = np.array([0., 0.5, 1])
        current = np.array([10., 15., 10.])
        capacity = calculate_capacity(time=time, current=current)
        np.testing.assert_array_equal(capacity, [0, 6.25, 12.5])
        # Test with pandas series
        time = pd.Series(time)
        current = pd.Series(current)
        capacity = calculate_capacity(time=time, current=current)
        self.assertIsInstance(capacity, pd.Series)
        np.testing.assert_array_equal(capacity, [0, 6.25, 12.5])
        np.testing.assert_array_equal(capacity.index, current.index)
        # Test with pandas series and units
        time = pd.Series(pint_pandas.PintArray(time, dtype=ureg.second))
        current = pd.Series(pint_pandas.PintArray(current, dtype=ureg.ampere))
        expected_capacity = pd.Series(pint_pandas.PintArray([0, 6.25, 12.5],
                                                            dtype=ureg.coulomb))
        capacity = calculate_capacity(time=time, current=current)
        np.testing.assert_array_equal(capacity, expected_capacity)
        units = capacity.pint.units
        expected_units = expected_capacity.pint.units
        self.assertTrue(
            units.is_compatible_with(expected_units),
            f"Incorrect units: {units} (expected {expected_units}).")

class CapacityTestCase(TestCase):
    def test_absolute_capacity(self):
        time = np.array([0., 0.5, 1])
        current = np.array([10., -15., 10.])
        capacity = calculate_capacity(time=time, current=current, absolute=True)
        np.testing.assert_array_equal(capacity, [0, 6.25, 12.5])
        # Test with pandas series
        time = pd.Series(time)
        current = pd.Series(current)
        capacity = calculate_capacity(time=time, current=current, absolute=True)
        self.assertIsInstance(capacity, pd.Series)
        np.testing.assert_array_equal(capacity, [0, 6.25, 12.5])
        np.testing.assert_array_equal(capacity.index, current.index)
        # Test with pandas series and units
        time = pd.Series(pint_pandas.PintArray(time, dtype=ureg.second))
        current = pd.Series(pint_pandas.PintArray(current, dtype=ureg.ampere))
        expected_capacity = pd.Series(pint_pandas.PintArray([0, 6.25, 12.5],
                                                            dtype=ureg.coulomb))
        capacity = calculate_capacity(time=time, current=current, absolute=True)
        np.testing.assert_array_equal(capacity, expected_capacity)
        units = capacity.pint.units
        expected_units = expected_capacity.pint.units
        self.assertTrue(
            units.is_compatible_with(expected_units),
            f"Incorrect units: {units} (expected {expected_units}).")

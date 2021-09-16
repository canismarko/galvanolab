from typing import Union

import pandas as pd
import numpy as np
import pint_pandas

from .electrochem_units import ureg


Array = Union[pd.Series, np.ndarray]


def calculate_capacity(time: Array, current: Array, absolute: bool=True) -> Array:
    """Calculate capacity based on the total charge passed.
    
    Parameters
    ==========
    time
      The times of the data points.
    current
      The current applied at each data point.
    absolute
      If true, calculate the total charge passed, otherwise calculate
      the charge transferred relative to t0.
    
    Returns
    =======
    capacity
      The calculate capacity with same shape as *time* and *current*.
    
    """
    capacity = cumsumz(current, x=time, absolute_y=absolute)
    return capacity


def cumsumz(y: Array, x: Array, axis=-1, absolute_y: bool=False) -> Array:
    """Cumulative sum along the given axis using the composite trapezoidal rule.
    
    Parameters
    ----------
    y
      1D input array to integrate.
    x
      The sample points corresponding to the `y` values.
    absolute_y
      If true, only the absolute magnitude of the y values will be
      used.
    
    Returns
    -------
    trapz
      Multiplication as approximated by trapezoidal rule, with shape
      matching *y*.

    """
    # Determine if we have units via pint
    index = getattr(y, 'index', None)
    y_units = y.pint.units if hasattr(y, 'pint') else 1.
    x_units = x.pint.units if hasattr(x, 'pint') else 1.
    # Strip off pandas series to we can avoid index problems
    y = getattr(y, 'values', y)
    x = getattr(x, 'values', x)
    # Strip off units if provided
    y = y.quantity.magnitude if hasattr(y, 'quantity') else y
    x = x.quantity.magnitude if hasattr(x, 'quantity') else x
    if x.ndim == 1:
        d = np.diff(x)
        # reshape to correct shape
        shape = [1]*y.ndim
        shape[axis] = d.shape[0]
        d = d.reshape(shape)
    else:
        d = np.diff(x, axis=axis)
    nd = y.ndim
    slice1 = [slice(None)]*nd
    slice2 = [slice(None)]*nd
    slice1[axis] = slice(1, None)
    slice2[axis] = slice(None, -1)
    if absolute_y:
        y = np.abs(y)
    ret = (d * (y[tuple(slice1)] + y[tuple(slice2)]) / 2.0)
    # Add zeros to the beginning
    ret = np.insert(ret, 0, 0., axis=axis)
    # Cumulative sum
    ret = np.cumsum(ret, axis=axis)
    # Add units back in if necessary
    has_units = (y_units != 1.) or (x_units != 1.)
    if has_units:
        ret = pint_pandas.PintArray(ret, dtype=y_units * x_units)
    # Convert back to a pandas series if necessary
    if index is not None:
        ret = pd.Series(ret, index=index)
    return ret


def fix_df_column(df: pd.DataFrame, old: str, new: str, unit: str=None, replace: bool=True, inplace: bool=True):

    """Helper function to rename dataframe columns.
    
    Also allows the inclusion of units.
    
    Parameters
    ==========
    df
      The pandas dataframe to operate on.
    old
      Name of the existing column.
    new
      Name of the new column to be created.
    replace
      If true, the *old* column will be dropped.
    inplace
      If true, *df* will be operated on directly.

    Returns
    =======
    df
      The modified original dataframe, or a copy, depending on the
      value of *inplace*)

    """
    # Prepare the dtype
    if unit is None:
        dtype = None
    else:
        dtype = 'pint[%s]' % unit
    # Set the pint registry to we're always consistent
    pint_pandas.PintType.ureg = ureg
    # Replace the column
    try:
        df[new] = pd.Series(df[old], dtype=dtype)
    except KeyError:
        pass
    else:
        if replace:
            df.drop([old], axis=1, inplace=inplace)
    return df


class BaseFile():
    dataframe = pd.DataFrame()
    
    def __init__(self, filename):
        self.filename = filename

    def active_mass(self):
        raise NotImplementedError()

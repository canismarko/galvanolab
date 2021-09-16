# -*- coding: utf-8 -*-
#
# Copyright © 2016 Mark Wolf
#
# This file is part of scimap.
#
# Scimap is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Scimap is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Scimap.  If not, see <http://www.gnu.org/licenses/>.

import numpy as np

from . import electrochem_units


class Cycle():
    """Data from one charge-discharge cycle."""
    
    def __init__(self, number, df):
        self.number = int(number)
        self.df = df

    @property
    def data(self):
        return self.df
    
    def charge_capacity(self):
        """Calculate difference between discharged and charged state"""
        max_capacity = np.max(self.df['capacity'])
        min_idx = self.df['capacity'].first_valid_index()
        min_capacity = self.df['capacity'][min_idx]
        return max_capacity - min_capacity
    
    def discharge_capacity(self):
        """Calculate the difference between charged and discharged state"""
        max_capacity = np.max(self.df['capacity'])
        discharge_df = self.df[self.df['<I>/mA'] < 0]
        min_capacity = np.min(discharge_df['capacity'])
        return max_capacity - min_capacity
    
    def plot_cycle(self, xcolumn, ycolumn, ax, label=None, marker='None', linestyle='-', *args, **kwargs):
        # Default label for plot
        if label is None:
            label = "Cycle {}".format(self.number)
        # Check that the columns given exist in the dataframe
        error_msg = "Cannot find {dim}column. Choices are {choices}"
        if xcolumn not in self.df.columns:
            msg = error_msg.format(dim='x', choices=self.df.columns)
            raise KeyError(msg)
        if ycolumn not in self.df.columns:
            msg = error_msg.format(dim='y', choices=self.df.columns)
            raise KeyError(msg)
        # Drop missing data
        df = self.df.dropna(subset=[xcolumn, ycolumn])
        # Plot remaining values
        units_ = {
            'capacity': electrochem_units.capacity,
        }
        xdata = df[xcolumn] / units_.get(xcolumn, 1)
        ydata = df[ycolumn] / units_.get(ycolumn, 1)
        xdata = xdata.astype(float)
        ydata = ydata.astype(float)
        artist = ax.plot(xdata, ydata, label=label, marker=marker, linestyle=linestyle, *args, **kwargs)
        return artist

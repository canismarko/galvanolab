# -*- coding: utf-8 -*-
#
# Copyright © 2018 Mark Wolf
#
# This file is part of galvanolab.
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
# along with Galvanolab.  If not, see <http://www.gnu.org/licenses/>.

import logging
log = logging.getLogger(__name__)

import os
from time import time
import math
import re
import io

from . import biologic
from . import exceptions_
from . import electrochem_units
from .cycle import Cycle
from .plots import new_axes


def requires_dataframe(func):
    """Decorator to make sure the dataframe is loaded before running."""
    def run_with_dataframe(self, *args, **kwargs):
        if self._df is None:
            self._load_data()
        return func(self, *args, **kwargs)
    return run_with_dataframe


def axis_label(key):
    axis_labels = {
        'Ewe/V': r'$E\ /V$',
        'capacity': r'$Capacity\ / mAhg^{-1}$',
    }
    # Look for label translation or return original key
    return axis_labels.get(key, key)


class Experiment():
    """Electrochemical experiment cycling on one channel.
    
    Will most likely be a base class for other child classes.
    
    """
    cycles = []
    _df = None
    
    def __init__(self, filename: str, mass=None, nmax: int=5000):
        """Parameters
        ----------
        filename :
          Filename for the .mpt file with exported data.
        mass : optional
          Mass of active material used. If ``None`` (default), an
          attempt will be made to read the mass from the file. This
          should be wrapped in a unit using the ``pint`` library.
        nmax : optional
          A cap on how many data points will be included in the
          dataframe. Experiments can get out of hand, so if working
          with the data is too slow, set this parameter to a smaller
          value.
        
        """
        self.filename = filename
        path, ext = os.path.splitext(filename)
        file_readers = {
            '.mpr': biologic.MPRFile,
            '.mpt': biologic.MPTFile,
        }
        if ext in file_readers.keys():
            FileReader = file_readers[ext]
            log.debug('Using file reader "%s"', FileReader)
        else:
            msg = "Unrecognized format {}".format(ext)
            raise exceptions_.FileFormatError(msg)
        self.datafile = FileReader(filename)
        self._mass = mass
        self.nmax = nmax
    
    @property
    @requires_dataframe
    def data(self):
        """Retrieve the data as pandas dataframe."""
        return self._df

    @property
    def mass(self):
        """Retrieve the characteristic active material mass."""
        if self._mass is None:
            # Get mass from eclab file
            mass = self.datafile.active_mass()
            if mass is not None:
                mass = mass.to(electrochem_units.mass)
        else:
            # User provided the mass
            mass = self._mass
        return mass
    
    def _load_data(self):
        """Read data from disk and save it for later use."""
        logstart = time()
        # Get the raw data from disk
        df = self.datafile.dataframe
        # Check if there are too many values and reduce if necessary
        if self.nmax is not None and len(df) > self.nmax:
            step = math.ceil(len(df) / self.nmax)
            self._df = df.iloc[::step].copy()
        else:
            # Save full dataframe
            self._df = df
        del df
        # Calculate capacity from charge and mass
        delta_Q = self._df.loc[:, '(Q-Qo)/mA.h'] * electrochem_units.mAh
        if self.mass is not None:
            self._df.loc[:, 'capacity'] = delta_Q / self.mass
        else:
            self._df.loc[:, 'capacity'] = delta_Q
        # Add time in hours as a column
        self._df.loc[:, 'time/h'] = self._df['time/s'] / 3600.
        log.info("Loaded %d datapoints from %s in %f seconds.",
                 len(self._df), self.filename, time() - logstart)
    
    @property
    def charge_current(self):
        # Get currents from eclab file
        try:
            currents = self.datafile.currents()
            charge_current, discharge_current = currents
        except exceptions_.ReadCurrentError:
            charge_current = None
        return charge_current
    
    @property
    def discharge_current(self):
        # Get currents from eclab file
        try:
            currents = self.datafile.currents()
            charge_current, discharge_current = currents
        except exceptions_.ReadCurrentError:
            discharge_current = None
        return discharge_current
    
    @property
    def theoretical_capacity(self):
        """Return the calculate capacity for this experiment."""
        theoretical_capacity = self.capacity_from_file()
        return theoretical_capacity

    @property
    def start_time(self):
        return self.datafile.start_time()
    
    @property
    @requires_dataframe
    def cycles(self):
        """Return a list of ``Cycle`` objects for the run."""
        cycles_df = list(self._df.groupby('cycle number'))
        cycles = []
        # Create Cycle objects for each cycle
        for cycle in cycles_df:
            new_cycle = Cycle(cycle[0], cycle[1])
            cycles.append(new_cycle)
        return cycles
    
    def capacity_from_file(self):
        """Read the mpt file and extract the theoretical capacity."""
        regexp = re.compile('^for DX = [0-9]+, DQ = ([0-9.]+) ([kmµ]?A.h)')
        capacity = None
        with io.open(self.filename, encoding='latin-1') as f:
            for line in f:
                match = regexp.match(line)
                if match:
                    cap_num, cap_unit = match.groups()
                    cap_unit = cap_unit.replace('.', '')
                    cap_unit = getattr(electrochem_units, cap_unit)
                    # We found the match now save it
                    capacity = cap_unit * float(cap_num)
                    break
        return capacity
    
    def closest_datum(self, value, label: str):
        """Retrieve the datapoint that is closest to a given data-point.
        
        Works best for linear columns, like time.
        
        Parameters
        ----------
        value :
          The value being sought.
        label :
          The column name along which to look for the value.
        
        Returns
        -------
        datum
          A pandas series with all the parameters closest to the one
          requested.
        
        """
        df = self.data
        distance = (df[label] - value).abs()
        idx = df.iloc[distance.argsort()].first_valid_index()
        datum = df.loc[idx]
        return datum
    
    def plot_cycles(self, xcolumn='time/s', ycolumn='Ewe/V',
                    ax=None, *args, **kwargs):
        """
        Plot each electrochemical cycle. Additional arguments gets passed
        on to matplotlib's plot function.
        """
        if not ax:
            ax = new_axes()
        ax.set_xlabel(axis_label(xcolumn))
        ax.set_ylabel(axis_label(ycolumn))
        legend = []
        for cycle in self.cycles:
            ax = cycle.plot_cycle(xcolumn, ycolumn, ax, *args, **kwargs)
            legend.append(cycle.number)
        ax.legend(legend)
        return ax

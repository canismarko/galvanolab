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
import re
import io

from . import biologic
from . import exceptions_
from . import electrochem_units
from .cycle import Cycle
from .plots import new_axes


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
    
    def __init__(self, filename, mass=None):
        """Parameters
        ----------
        filename : str
          Filename for the .mpt file with exported data.
        mass : optional
          Mass of active material used. If ``None`` (default), and
          attempt will be made to read the mass from the file. This
          should be wrapped in a unit using the ``units`` library.
        
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
        # self.load_csv(filename)
        run = FileReader(filename)
        self._df = run.dataframe
        logstart = time()
        log.debug(time() - logstart)
        self.cycles = []
        # Get theoretical capacity from eclab file
        self.theoretical_capacity = self.capacity_from_file()
        log.debug(time() - logstart)
        log.debug("Found theoretical capacity {}".format(self.theoretical_capacity))
        # Get currents from eclab file
        try:
            currents = self.currents_from_file()
            self.charge_current, self.discharge_current = currents
        except exceptions_.ReadCurrentError:
            pass
        log.debug(time() - logstart)
        # Calculate capacity from charge and mass
        if mass:
            # User provided the mass
            self.mass = mass
        else:
            # Get mass from eclab file
            self.mass = run.active_mass()
            if self.mass is not None:
                self.mass = self.mass.to(electrochem_units.mass)
        log.debug("First one {}".format(time() - logstart))
        delta_Q = self._df.loc[:, '(Q-Qo)/mA.h'] * electrochem_units.mAh
        log.debug("Next one: {}".format(time() - logstart))
        idx = 1646
        if self.mass is not None:
            self._df.loc[:, 'capacity'] = delta_Q / self.mass
        else:
            self._df.loc[:, 'capacity'] = delta_Q
        # Process other metadata
        self.start_time = run.metadata.get('start_time', None)
        # Split the data into cycles, except the initial resting phase
        cycles = list(self._df.groupby('cycle number'))
        # Create Cycle objects for each cycle
        for cycle in cycles:
            new_cycle = Cycle(cycle[0], cycle[1])
            self.cycles.append(new_cycle)
        log.debug(time() - logstart)
    
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
    
    def currents_from_file(self):
        """Read the mpt file and extract the theoretical capacity."""
        current_regexp = re.compile('^Is\s+[0-9.]+\s+([-0-9.]+)\s+([-0-9.]+)')
        unit_regexp = re.compile(
            '^unit Is\s+[kmuµ]?A\s+([kmuµ]?A)\s+([kmuµ]?A)'
        )
        data_found = False
        with io.open(self.filename, encoding='latin-1') as f:
            for line in f:
                # Check if this line has either the currents or the units
                current_match = current_regexp.match(line)
                unit_match = unit_regexp.match(line)
                if current_match:
                    charge_num, discharge_num = current_match.groups()
                    charge_num = float(charge_num)
                    discharge_num = float(discharge_num)
                if unit_match:
                    charge_unit, discharge_unit = unit_match.groups()
                    data_found = True
                    break
        if data_found:
            # Get the sympy units objects
            charge_unit = getattr(electrochem_units, charge_unit.replace("µ", 'u'))
            discharge_unit = getattr(electrochem_units, discharge_unit.replace("µ", 'u'))
            charge_current = charge_unit * charge_num
            discharge_current = discharge_unit * discharge_num
            return charge_current, discharge_current
        else:
            # Current data could not be extracted from file
            msg = "Could not read currents from file {filename}."
            msg = msg.format(filename=self.filename)
            raise exceptions_.ReadCurrentError(msg)
    
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
        df = self._df
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

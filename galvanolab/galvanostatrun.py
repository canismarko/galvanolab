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

import re
import os
import io
import warnings
import logging
from time import time

import numpy as np
from sympy.physics import units
import pytz

from . import exceptions_
from .cycle import Cycle
from .plots import new_axes
from . import electrochem_units
from . import biologic


log = logging.getLogger(__name__)


def axis_label(key):
    axis_labels = {
        'Ewe/V': r'$E\ /V$',
        'capacity': r'$Capacity\ / mAhg^{-1}$',
    }
    # Look for label translation or return original key
    return axis_labels.get(key, key)


class GalvanostatRun():
    """
    Electrochemical experiment cycling on one channel.  Galvanostatic
    control potential limited (GPLC). Mass is assumed to be in grams.
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
        log.debug("First one {}".format(time() - logstart))
        # mass_g = electrochem_units.mass(self.mass).num
        delta_Q = self._df.loc[:, '(Q-Qo)/mA.h'] * electrochem_units.mAh
        log.debug("Next one: {}".format(time() - logstart))
        self._df.loc[:, 'capacity'] = delta_Q / self.mass
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

    def discharge_capacity(self, cycle_idx=-1):
        """
        Return the discharge capacity of the given cycle (default last).
        """
        return self.cycles[cycle_idx].discharge_capacity()

    def charge_capacity(self, cycle_idx=-1):
        """
        Return the charge capacity of the given cycle (default last).
        """
        return self.cycles[cycle_idx].charge_capacity()
    
    def closest_datum(self, value, label):
        """Retrieve the datapoint that is closest to the given value along the
        given label. Works best for linear columns, like time."""
        df = self._df
        distance = (df[label] - value).abs()
        idx = df.iloc[distance.argsort()].first_valid_index()
        series = df.ix[idx]
        return series
    
    def plot_cycles(self, xcolumn='capacity', ycolumn='Ewe/V',
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
    
    def plot_state_of_charge(self, framesets, ax, text="",
                             timezone='US/Central', convert_to="capacity"):
        """Plot an horizontal box with the state of charge based on the range
        of timestamps in the operando framesets. "text" will be
        plotted at the top of the box.
        """
        starttime = min([fs.starttime() for fs in framesets])
        endtime = max([fs.endtime() for fs in framesets])
        tzinfo = pytz.timezone(timezone)
        charge_start_time = self.start_time.replace(tzinfo=tzinfo)
        timemin = (starttime - charge_start_time).total_seconds()
        timemax = (endtime - charge_start_time).total_seconds()

        # Convert units from time to capacity
        capmin = self.closest_datum(value=timemin, label="time/s")[convert_to]
        capmax = self.closest_datum(value=timemax, label="time/s")[convert_to]

        # Plot a box highlighting the range of capacities
        artist = ax.axvspan(capmin,
                            capmax,
                            zorder=1,
                            facecolor="green",
                            alpha=0.15)
        
        # Add text label
        x = (capmin + capmax) / 2
        ylim = ax.get_ylim()
        y = ylim[1] - 0.03 * (ylim[1] - ylim[0])
        ax.text(x, y, text, horizontalalignment="center",
                verticalalignment="top")
        return artist
    
    def discharge_capacities(self):
        capacities = np.array([cycle.discharge_capacity()
                               for cycle in self.cycles])
        return capacities
    
    def charge_capacities(self):
        capacities = np.array([cycle.charge_capacity()
                               for cycle in self.cycles])
        return capacities
    
    def plot_discharge_capacity(self, *args, **kwargs):
        with warnings.catch_warnings():
            warnings.filterwarnings("once")
            warnings.warn("Use `plot_capacities(direction='discharge')` instead",
                          DeprecationWarning)
        kwargs['direction'] = kwargs.get('direction', "discharge")
        return self.plot_capacities(*args, **kwargs)
    
    def plot_capacities(self, ax=None, ax2=None,
                        direction="discharge", plot_efficiences=True):
        """Plot capacity of each cycle versus cycle number.

        Arguments
        ---------
        - ax : Matplotlib axes for plotting capacities.
        - ax2 : Matplotlib axes for plotting coulombic efficiences
        - direction : whether to plot "charge" capcity or "discharge"
          capacity.
        - plot_efficiences : Whether to plot the coulombic efficiency
          as well
        """
        # Calculate relevant plotting values
        discharge = self.discharge_capacities()
        charge = self.charge_capacities()
        if direction == "discharge":
            capacities = discharge
        elif direction == "charge":
            capacities = charge
        else:
            raise ValueError("direction '{}' not recognized.")
        cycle_numbers = [c.number for c in self.cycles]
        # Plot cycle capacities
        if ax is None:
            ax = new_axes()
        # Convert to standard units
        capacities = (capacities / electrochem_units.mAh * electrochem_units.gram)
        capacities = capacities.astype(float)
        ax.plot(cycle_numbers,
                capacities,
                marker='o',
                linestyle='--',
                label="%s capacity" % direction)
        if plot_efficiences:
            efficiencies = discharge / charge * 100
            if ax2 is None:
                ax2 = ax.twinx()
            ax2.plot(cycle_numbers,
                     efficiencies,
                     marker='^',
                     linestyle='--',
                     label="Coulombic efficiency")
            ax2.set_ylim(0, 105)
            ax2.legend(loc='lower right')
            ax2.set_ylabel('Coulombic efficiency (%)')
            ax2.spines['right'].set_visible(True)
        # Format axes
        if max(cycle_numbers) < 20:
            # Only show all of the ticks if there are less than 20
            ax.set_xticks(cycle_numbers)
        ax.set_xlim(0, 1 + max(cycle_numbers))
        ax.set_ylim(0, 1.1 * max(capacities))
        ax.set_xlabel('Cycle')
        ax.set_ylabel('%s capacity $/mAhg^{-1}$' % direction)
        ax.legend(loc='lower left')
        return ax, ax2
    
    def plot_differential_capacity(self, ax=None, ax2=None, cycle=None):
        if not ax:
            ax = new_axes()
        if not ax2:
            ax2 = ax.twiny()
        # Let the user specify a cycle by index
        if cycle is None:
            cycles = self.cycles
        else:
            cycles = [self.cycles[cycle]]
        for cycle in cycles:
            # Plot regular charge/discharge curve
            cycle.plot_cycle(xcolumn='capacity',
                             ycolumn='Ewe/V',
                             ax=ax)
            # Plot differential capacity (sideways)
            cycle.plot_cycle(xcolumn='d(Q-Qo)/dE/mA.h/V',
                             ycolumn='Ewe/V',
                             ax=ax2,
                             linestyle='-.')
        # Annotate plot
        ax.set_xlabel('Capacity $/mAh\ g^{-1}$')
        ax2.set_xlabel('Capacity differential $/mAh\ g^{-1}V^{-1}$')
        ax.set_ylabel('Cathode potential vs $ Li/Li^+$')
        return ax, ax2

# -*- coding: utf-8 -*-
#
# Copyright © 2016 Mark Wolf
#
# This file is part of galvanolab.
#
# Galvanolab is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Galvanolab is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Galvanolab.  If not, see <http://www.gnu.org/licenses/>.

import re
import os
import io
import warnings
import logging
from time import time

import numpy as np
import pytz

from . import exceptions_
from .cycle import Cycle
from .plots import new_axes
from . import electrochem_units
from .experiment import Experiment
from . import biologic


log = logging.getLogger(__name__)


class GalvanostatRun(Experiment):
    """Electrochemical experiment cycling on one channel.  Galvanostatic
    control potential limited (GPLC). Mass is assumed to be in grams.
    
    """
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
    
    def plot_cycles(self, xcolumn='capacity', ycolumn='potential',
                    ax=None, *args, **kwargs):
        return super().plot_cycles(xcolumn=xcolumn, ycolumn=ycolumn,
                                   ax=ax, *args, **kwargs)
    
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
                        direction: str="both", plot_efficiences: bool=True,
                        legend_loc='best'):
        """Plot capacity of each cycle versus cycle number.
        
        Arguments
        ---------
        ax : optional
          Matplotlib axes for plotting capacities.
        ax2 : optional
          Matplotlib axes for plotting coulombic efficiences
        direction : optional
          whether to plot "charge" capcity, "discharge" capacity, or
          "both" (default).
        plot_efficiences : optional
          Whether to plot the coulombic efficiency as well
        legend_loc : optional
          Position specifier for matplotlib legend used in the axes.
        """
        # Calculate relevant plotting values
        discharge = self.discharge_capacities()
        charge = self.charge_capacities()
        if direction not in ('charge', 'discharge', 'both'):
            raise ValueError("direction '{}' not recognized.".format(direction))
        cycle_numbers = [c.number for c in self.cycles]
        # Set up plotting environment
        if ax is None:
            ax = new_axes()
        lines = []
        # Convert to standard units
        discharge = (discharge / electrochem_units.capacity).astype(float)
        charge = (charge / electrochem_units.capacity).astype(float)
        # Plot charge and discharge capacities
        if direction in ("charge", "both"):
            ln = ax.plot(cycle_numbers, charge, marker='o',
                         linestyle='--', color="C1", label="Charge")
            lines.extend(ln)
        if direction in ("discharge", "both"):
            ln = ax.plot(cycle_numbers, discharge, marker='x',
                    linestyle='--', color="C1", label="Discharge")
            lines.extend(ln)
        # Plot coulombic efficiencies, if asked for
        if plot_efficiences:
            efficiencies = discharge / charge * 100
            if ax2 is None:
                ax2 = ax.twinx()
            ln = ax2.plot(cycle_numbers, efficiencies, marker='^',
                          linestyle='--', color='C2',
                          label="Coul. eff.")
            ax2.set_ylim(0, 105)
            ax2.legend().remove()
            ax2.set_ylabel('Coulombic efficiency (%)')
            ax2.spines['right'].set_visible(True)
            lines.extend(ln)
        # Format axes
        if max(cycle_numbers) < 20:
            # Only show all of the ticks if there are less than 20
            ax.set_xticks(cycle_numbers)
        ax.set_xlim(0, 1 + max(cycle_numbers))
        ax.set_ylim(0, 1.1 * max((max(charge), max(discharge))))
        ax.set_xlabel('Cycle')
        ax.set_ylabel('Capacity $/mAhg^{-1}$')
        # Color code the axes for different plotting types
        if plot_efficiences:
            ax2.spines['left'].set_color('C1')
            ax.tick_params(axis='y', colors="C1")
            ax.yaxis.label.set_color('C1')
            ax2.spines['right'].set_color('C2')
            ax2.tick_params(axis='y', colors="C2")
            ax2.yaxis.label.set_color('C2')
        # Put all the legends on one axis
        ax.legend(lines, (ln.get_label() for ln in lines), loc=legend_loc)
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
        ax.set_xlabel(r'Capacity $/mAh\ g^{-1}$')
        ax2.set_xlabel(r'Capacity differential $/mAh\ g^{-1}V^{-1}$')
        ax.set_ylabel(r'Cathode potential vs $ Li/Li^+$')
        return ax, ax2

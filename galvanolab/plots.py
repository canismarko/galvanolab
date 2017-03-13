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

import matplotlib.pyplot as plt

from . import electrochem_units

def remove_extra_spines(ax):
    """Removes the right and top borders from the axes."""
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')
    return ax


def new_axes(height=5, width=None):
    """Create a new set of matplotlib axes for plotting. Height in inches."""
    # Adjust width to accomodate colorbar
    if width is None:
        width = height / 0.8
    fig = plt.figure(figsize=(width, height))
    # Set background to be transparent
    fig.patch.set_alpha(0)
    # Create axes
    ax = plt.gca()
    # Remove borders
    remove_extra_spines(ax)
    return ax


def plot_rate_capacities(runs, ax=None, cycle_idx=0):
    """Plot the discharge capacity as a function of charge-rate for a set
    of runs. Similar in spirit to a ragone plot."""
    if ax is None:
        ax = new_axes()
    # Arrays for holding data to be plotted
    capacities = []
    rates = []
    # Fill arrays with data
    for run in runs:
        # Determine capacity
        capacity = run.charge_capacity(cycle_idx=cycle_idx)
        capacities.append(capacity)
        # Determine C-rate (with units)
        time = run.theoretical_capacity / abs(run.charge_current)
        rate = 1 / (electrochem_units.hour(time))
        rates.append(rate)
    # Plot resulting data
    ax.plot(rates, capacities, marker='o')
    ax.set_xscale('log')
    ax.set_ylim(bottom=0)
    ax.set_xlabel('C-rate / $h^{-1}$')
    ax.set_ylabel('Charge capacity / $mAhg^{-1}$')
    ax.set_title('Rate-capacities during cycle {}'.format(cycle_idx + 1))
    return ax

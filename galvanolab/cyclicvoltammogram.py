# -*- coding: utf-8 -*-
#
# Copyright © 2018 Mark Wolf
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


from .experiment import Experiment

class CyclicVoltammogram(Experiment):
    """Electrochemical experiment cycling on one channel, with cyclic
    voltammetry data possibly over multiple cycles.
    
    """
    def plot_cycles(self, xcolumn='Ewe/V', ycolumn='<I>/mA',
                    ax=None, *args, **kwargs):
        return super().plot_cycles(xcolumn=xcolumn, ycolumn=ycolumn,
                                   ax=ax, *args, **kwargs)

# -*- coding: utf-8 -*-
#
# Copyright © 2016 Mark Wolf
#
# This file is part of Galvanolab.
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

from . import electrochem_units
from .electrochem_units import ureg
setup_matplotlib = ureg.setup_matplotlib

from .galvanostatrun import GalvanostatRun
from .chinstruments import CHFile
from .maccor import MaccorTextFile
from .cyclicvoltammogram import CyclicVoltammogram
from .electrode import CathodeLaminate, CoinCellElectrode
from .cycle import Cycle

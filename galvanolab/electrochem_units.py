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

# from units import unit, named_unit, named_composed_unit, scaled_unit
from sympy.physics import units

# Prepare some composite units specific to electrochemistry
# mAh = named_unit('mAh', ['A', 's'], [], multiplier=3.6)
mAh = units.milli * units.ampere * units.hour
uAh = units.micro * units.ampere * units.hour
# uAh = scaled_unit('µAh', 'mAh', 10**-3)
# uA = named_unit('µA', ['uA'], [])
uA = units.micro * units.ampere
mA = units.milli * units.ampere

## Default units defined below
electrode_loading = units.mg * units.cm**-2
mass = units.g

units

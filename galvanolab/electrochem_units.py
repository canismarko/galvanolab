# -*- coding: utf-8 -*-
#
# Copyright © 2016 Mark Wolfman
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


import logging

from pint import UnitRegistry, set_application_registry
import pint_pandas

log = logging.getLogger(__name__)

# Create a universal unit registry
ureg = UnitRegistry()
set_application_registry(ureg)
pint_pandas.PintType.ureg = ureg

log.debug("Instantiating registry: %s", repr(ureg))

# Prepare some composite units specific to electrochemistry
mAh = ureg.milliampere * ureg.hour
uAh = ureg.microampere * ureg.hour
uA = ureg.microampere
mA = ureg.milliampere

# Default units defined below
mg = ureg.milligram
electrode_loading = mg / ureg.centimeter**2
mass = ureg.gram
capacity = mAh / ureg.gram
coulomb = ureg.coulomb

# -*- coding: utf-8 -*-
#
# Copyright © 2017 Mark Wolf
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

# flake8: noqa

import math
import datetime as dt
from unittest import TestCase, expectedFailure, main
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

# from units import unit, predefined, named_unit, named_composed_unit
from sympy.physics import units
# predefined.define_units()

from galvanolab.electrode import CathodeLaminate, CoinCellElectrode
from galvanolab.galvanostatrun import GalvanostatRun
from galvanolab import electrochem_units
from galvanolab import biologic


testdir = os.path.join(os.path.dirname(__file__))
mptfile = os.path.join(testdir, 'eclab-test-data.mpt')
mprfile = os.path.join(testdir, 'NEI-C10_4cycles_C14.mpr')


class ElectrochemUnitsTest(TestCase):
    """Check that various values for current, capacity, etc are compatible."""
    def setUp(self):
        self.mAh = electrochem_units.mAh
        self.mA = units.milli * units.A
        self.uA = units.micro * units.A

    def test_milli_micro_amps(self):
        # Check that a mAh is really a scaled amp-second
        mAh = 1 * electrochem_units.mAh
        As = 3.6 * units.A * units.s
        self.assertEqual(mAh, As)
        # Check that mAh division works
        mAh = 10 * electrochem_units.mAh
        uA = 200 * self.uA
        hours = mAh / uA / 3600 / units.s
        self.assertAlmostEqual(hours, 10 / 0.2, msg=hours)


class ElectrodeTest(TestCase):
    def setUp(self):
        self.laminate = CathodeLaminate(mass_active_material=0.9,
                                        mass_carbon=0.05,
                                        mass_binder=0.05,
                                        name="LMO-NEI")
        self.electrode = CoinCellElectrode(total_mass=15 * units.mg,
                                           substrate_mass=5 * units.mg,
                                           laminate=self.laminate,
                                           name="DummyElectrode",
                                           diameter=12.7 * units.mm)

    def test_area(self):
        diameter = 1.27 * units.cm
        expected_area = math.pi * (diameter / 2)**2
        self.assertAlmostEqual(self.electrode.area() / expected_area, 1)

    def test_mass_loading(self):
        """Ensure the electrode can calculate the loading in mg/cm^2."""
        loading_units = electrochem_units.electrode_loading
        area = math.pi * (1.27/2)**2
        expected = (15-5) * 0.9 * loading_units / area
        self.assertAlmostEqual(self.electrode.mass_loading() / expected, 1)


class CycleTest(TestCase):
    def setUp(self):
        self.run = GalvanostatRun(mptfile, mass=0.022563)
        self.cycle = self.run.cycles[0]

    def test_discharge_capacity(self):
        self.assertAlmostEqual(
            self.cycle.discharge_capacity() / electrochem_units.mAh,
            99.736007823354,
        )


class GalvanostatRunTest(TestCase):
    # Currently just tests import statement
    def test_import(self):
        GalvanostatRun(mptfile)

    def test_read_mass(self):
        run = GalvanostatRun(mptfile)
        self.assertEqual(run.mass, float('22.53') * units.mg)

    def test_read_capacity(self):
        run = GalvanostatRun(mptfile)
        mAh = electrochem_units.mAh
        self.assertEqual(run.theoretical_capacity, 3.340 * mAh)
        # self.assertEqual(run.theoretical_capacity, elec('mAh')(3.340))

    def test_read_date(self):
        run = GalvanostatRun(mptfile)
        self.assertEqual(
            run.start_time,
            dt.datetime(2015, 2, 9, 16, 20, 24)
        )

    def test_read_current(self):
        run = GalvanostatRun(mptfile)
        # These are practically equal but assertEqual fails due to rounding in units package
        uA = units.micro * units.ampere
        self.assertEqual(
            run.charge_current,
            float('334.00') * uA,
            
        )
        self.assertEqual(
            run.discharge_current,
            float('-334.00') * uA,
        )

    def test_capacity_from_time(self):
        run = GalvanostatRun(mptfile)
        datum = run.closest_datum(value=77067, label="time/s")
        dQ = 1.97891703009079 * units.milli * units.A * units.h # Read from file
        expected = dQ / 0.02253 / units.grams
        self.assertAlmostEqual(datum.capacity / expected, 1)


if __name__ == '__main__':
    main()

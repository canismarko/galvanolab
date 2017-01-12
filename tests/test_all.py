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

from units import unit, predefined, named_unit, named_composed_unit
predefined.define_units()

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
        self.hour = electrochem_units.hour
        self.mA = unit('mA')
        self.uA = unit('uA')

    def test_milli_micro_amps(self):
        # Check that a mAh is really a scaled amp-second
        mAh = self.mAh(1)
        As = unit('A') * unit('s')
        self.assertEqual(mAh, unit('A')(3.6) * unit('s')(1))
        # Check that mAh division works
        hours = self.mAh(10) / unit('uA')(1000)
        hours = self.hour(hours)
        self.assertAlmostEqual(hours.num, 10, msg=hours)


class ElectrodeTest(TestCase):
    def setUp(self):
        self.laminate = CathodeLaminate(mass_active_material=0.9,
                                        mass_carbon=0.05,
                                        mass_binder=0.05,
                                        name="LMO-NEI")
        self.electrode = CoinCellElectrode(total_mass=unit('mg')(15),
                                           substrate_mass=unit('mg')(5),
                                           laminate=self.laminate,
                                           name="DummyElectrode",
                                           diameter=unit('mm')(12.7))

    def test_area(self):
        area_unit = unit('cm') * unit('cm')
        expected_area = area_unit(math.pi * (1.27/2)**2)
        self.assertEqual(self.electrode.area(), expected_area)

    def test_mass_loading(self):
        """Ensure the electrode can calculate the loading in mg/cm^2."""
        loading_units = unit('mg')/(unit('cm')*unit('cm'))
        area = math.pi * (1.27/2)**2
        expected = loading_units((15-5)*0.9 / area)
        self.assertEqual(self.electrode.mass_loading(), expected)


class CycleTest(TestCase):
    def setUp(self):
        self.run = GalvanostatRun(mptfile, mass=0.022563)
        self.cycle = self.run.cycles[0]

    def test_discharge_capacity(self):
        self.assertEqual(
            round(self.cycle.discharge_capacity(), 3),
            99.736
        )


class GalvanostatRunTest(TestCase):
    # Currently just tests import statement
    def test_import(self):
        GalvanostatRun(mptfile)

    def test_read_mass(self):
        run = GalvanostatRun(mptfile)
        self.assertEqual(run.mass, unit('g')(0.02253))

    def test_read_capacity(self):
        run = GalvanostatRun(mptfile)
        self.assertEqual(run.theoretical_capacity, unit('mAh')(3.340))

    def test_read_date(self):
        run = GalvanostatRun(mptfile)
        self.assertEqual(
            run.start_time,
            dt.datetime(2015, 2, 9, 16, 20, 24)
        )

    def test_read_current(self):
        run = GalvanostatRun(mptfile)
        # These are practically equal but assertEqual fails due to rounding in units package
        mA = unit('mA')
        self.assertAlmostEqual(
            mA(run.charge_current).num,
            mA(0.334).num,
            places=7,
        )
        self.assertAlmostEqual(
            mA(run.discharge_current).num,
            mA(-0.334).num,
            places=7,
        )

    def test_capacity_from_time(self):
        run = GalvanostatRun(mptfile)
        datum = run.closest_datum(value=77067, label="time/s")
        dQ = 1.97891703009079  # Read from file
        expected = dQ / 0.02253
        self.assertAlmostEqual(datum.capacity, expected)


if __name__ == '__main__':
    main()

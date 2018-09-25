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

from galvanolab.electrode import CathodeLaminate, CoinCellElectrode
from galvanolab.galvanostatrun import GalvanostatRun
from galvanolab.experiment import Experiment
from galvanolab import electrochem_units, CyclicVoltammogram
from galvanolab import biologic


testdir = os.path.join(os.path.dirname(__file__))
mptfile = os.path.join(testdir, 'eclab-test-data.mpt')
mprfile = os.path.join(testdir, 'NEI-C10_4cycles_C14.mpr')
cv_mptfile = os.path.join(testdir, 'eclab-cv-test-data.mpt')


ureg = electrochem_units.ureg


class ElectrochemUnitsTest(TestCase):
    """Check that various values for current, capacity, etc are compatible."""
    def setUp(self):
        self.mAh = electrochem_units.mAh
        self.mA = ureg.milliampere
        self.uA = ureg.microampere

    def test_milli_micro_amps(self):
        # Check that a mAh is really a scaled amp-second
        mAh = 1 * electrochem_units.mAh
        As = 3.6 * ureg.ampere * ureg.second
        self.assertEqual(mAh, As)
        # Check that mAh division works
        mAh = 10 * electrochem_units.mAh
        uA = 200 * self.uA
        hours = mAh / uA / 3600 / ureg.second
        self.assertAlmostEqual(hours, 10 / 0.2, msg=hours)


class ElectrodeTest(TestCase):
    def setUp(self):
        self.laminate = CathodeLaminate(mass_active_material=0.9,
                                        mass_carbon=0.05,
                                        mass_binder=0.05,
                                        name="LMO-NEI")
        self.electrode = CoinCellElectrode(total_mass=15 * ureg.mg,
                                           substrate_mass=5 * ureg.mg,
                                           laminate=self.laminate,
                                           name="DummyElectrode",
                                           diameter=12.7 * ureg.mm)
    
    def test_area(self):
        diameter = 1.27 * ureg.cm
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
        self.run = GalvanostatRun(mptfile, mass=0.022563 * electrochem_units.ureg.gram,
                                  nmax=None)
        self.cycle = self.run.cycles[0]
    
    def test_discharge_capacity(self):
        self.assertAlmostEqual(
            self.cycle.discharge_capacity(),
            99.736007823354,
        )


class CyclicVoltammogramTest(TestCase):
    def test_import(TestCase):
        CyclicVoltammogram(cv_mptfile)


class ExperimentTest(TestCase):
    """Tests for experiments in general, not specific to eg. galvanostatic
    or CV experiments.
    
    """
    def test_nmax(self):
        """Check that the user can limit the number of data points."""
        # First test with a valid number
        exp = Experiment(mptfile, nmax=1000)
        df = exp.data
        self.assertLessEqual(len(df), 1000)
        # Now test with "None" for no limit
        exp = Experiment(mptfile, nmax=None)
        df = exp.data
        self.assertEqual(len(df), 5274)


class GalvanostatRunTest(TestCase):
    # Currently just tests import statement
    def test_import(self):
        GalvanostatRun(mptfile)
    
    def test_read_mass(self):
        run = GalvanostatRun(mptfile)
        self.assertEqual(run.mass, 22.53 * ureg.mg)
    
    def test_read_capacity(self):
        run = GalvanostatRun(mptfile)
        mAh = electrochem_units.mAh
        self.assertEqual(run.theoretical_capacity, 3.340 * mAh)
    
    def test_read_date(self):
        run = GalvanostatRun(mptfile)
        self.assertEqual(
            run.start_time,
            dt.datetime(2015, 2, 9, 16, 20, 24)
        )
    
    def test_read_current(self):
        run = GalvanostatRun(mptfile)
        uA = ureg.microampere
        self.assertEqual(
            run.charge_current,
            float('334.00') * uA,
        )
        self.assertEqual(
            run.discharge_current,
            float('-334.00') * uA,
        )
    
    def test_capacity_from_time(self):
        run = GalvanostatRun(mptfile, nmax=None)
        datum = run.closest_datum(value=77067, label="time/s")
        DQ = 1.9789170300907912 * ureg.milliampere * ureg.hour # Read from file
        mass = 0.02253 * ureg.gram
        expected = DQ / mass
        # Check the loaded values
        self.assertEqual(datum['(Q-Qo)/mA.h'], (DQ / ureg.milliampere / ureg.hour).magnitude)
        self.assertEqual(datum.capacity * electrochem_units.capacity, expected)


class BiologicMptTestCase(TestCase):
    def test_currents(self):
        reader = biologic.MPTFile(mptfile)
        charge_current, discharge_current = reader.currents()
        self.assertEqual(charge_current, 0.334 * ureg.milliampere)
        self.assertEqual(discharge_current, -0.334 * ureg.milliampere)


if __name__ == '__main__':
    main()

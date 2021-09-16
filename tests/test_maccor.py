from unittest import TestCase
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import pint

from galvanolab.electrochem_units import ureg
from galvanolab.maccor import MaccorTextFile


test_dir = Path(__file__).resolve().parent


class MaccorTextFileTests(TestCase):
    test_file_A = test_dir / "20210407_Pg19-8_form_4cycles.008.txt"
    test_file_B = test_dir / "cell4_dschrg_1mm.005.txt"
    def test_simple_file(self):
        maccorfile = MaccorTextFile(self.test_file_A)
        df = maccorfile.dataframe
        self.assertIsInstance(df, pd.DataFrame)
        # Check that the  current and potential are properly inserted
        self.assertEqual(df.iloc[0]['current'], 0.0)
        self.assertEqual(df.loc[3076]['current'], -0.00039994 * ureg.ampere)
        self.assertEqual(df.iloc[0]['potential'], 0.0172 * ureg.volt)
        self.assertEqual(df.loc[3076]['potential'], 3.1588 * ureg.volt)
        self.assertEqual(df.iloc[0]['time'], 0)
        self.assertEqual(df.loc[3076]['time'], 878.778333 * 60 * ureg.seconds)
        # Check that capacity is calculated properly
        self.assertIn("capacity_net", df.columns)
        self.assertIn("capacity_total", df.columns)

    def test_simple_file_versionB(self):
        """Tests for a second file that doesn't import properly."""
        maccorfile = MaccorTextFile(self.test_file_B)
        df = maccorfile.dataframe
        self.assertIsInstance(df, pd.DataFrame)
        # Check that the  current and potential are properly inserted
        self.assertEqual(df.iloc[0]['current'], 0.0)
        self.assertEqual(df.loc[8]["time"], 0.583333 * ureg.minute)
        # Check that capacity is calculated properly
        self.assertIn("capacity_net", df.columns)
        self.assertIn("capacity_total", df.columns)
    
    def test_multiple_files(self):
        chfile = MaccorFile([self.test_file_A, self.test_file_B])
        df = chfile.dataframe
        self.assertIsInstance(df, pd.DataFrame)
        # Check that the potential is properly insert during the hold

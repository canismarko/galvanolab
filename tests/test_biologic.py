from unittest import TestCase
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from galvanolab.biologic import MPTFile
from galvanolab.electrochem_units import ureg


test_dir = Path(__file__).resolve().parent


class MaccorTextFileTests(TestCase):
    test_file_A = test_dir / "eclab-test-data.mpt"
    def test_simple_file(self):
        biologicfile = MPTFile(self.test_file_A)
        df = biologicfile.dataframe
        self.assertIsInstance(df, pd.DataFrame)
        # Check that the  current and potential are properly inserted
        self.assertEqual(df.iloc[0]['current'], 0.0)
        self.assertEqual(df.loc[3076]['current'], -0.000334347813332657 * ureg.ampere)
        self.assertEqual(df.iloc[0]['potential'], 3.14639711 * ureg.volt)
        self.assertEqual(df.loc[3076]['potential'], 3.03747201 * 1000 * ureg.millivolt)
    
    def test_multiple_files(self):
        chfile = Biologicfile([self.test_file_A, self.test_file_B])
        df = chfile.dataframe
        self.assertIsInstance(df, pd.DataFrame)
        # Check that the potential is properly insert during the hold

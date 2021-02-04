from unittest import TestCase
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from galvanolab.chinstruments import CHFile


test_dir = Path(__file__).resolve().parent


class CHInstrumentsFileTests(TestCase):
    test_file_A = test_dir / "Cylindrical_2_formation.txt"
    test_file_B = test_dir / "Cylindrical_2_cycling.txt"
    def test_simple_file(self):
        chfile = CHFile(self.test_file_B)
        df = chfile.dataframe
        self.assertIsInstance(df, pd.DataFrame)
        # Check that the  current and potential are properly inserted
        self.assertEqual(df.iloc[0]['Current/A'], -1.4e-4)
        self.assertEqual(df.iloc[-1]['Potential/V'], 1.7)
        plt.plot(df['Current/A'])
        ax2 = plt.twinx()
        ax2.plot(df['Potential/V'], color="C2")
        plt.show()
    
    def test_multiple_files(self):
        chfile = CHFile([self.test_file_A, self.test_file_B])
        df = chfile.dataframe
        self.assertIsInstance(df, pd.DataFrame)
        # Check that the potential is properly insert during the hold

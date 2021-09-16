"""Tools for reading files from Maccor cyclers."""

import pandas as pd
import pint_pandas

from galvanolab.basefile import BaseFile, fix_df_column, calculate_capacity


class MaccorTextFile(BaseFile):
    """A text file exported from Maccor MIMS software."""
    def __init__(self, filename):
        super().__init__(filename=filename)
        self.load_csv(filename=self.filename)

    def load_csv(self, filename):
        """Wrapper around pandas read_csv."""
        df = pd.read_csv(filename,
                         skiprows=(*range(13), 14),
                         index_col=False,
                         sep='\t')
        # Rename columns to be consistent with other formats
        df.set_index('Rec', inplace=True)
        fix_df_column(df, 'Current [A]', 'current', unit='A')
        fix_df_column(df, 'Voltage [V]', 'potential', unit='V')
        fix_df_column(df, 'TestTime', 'time', unit='minute')
        fix_df_column(df, 'Cycle C', 'cycle', replace=False)
        # Convert currents to negative when discharging
        if "D" in df['Md'].values:
            df['current'][df['Md'] == 'D'] *= -1.
        # Calculate capacity
        df['capacity_net'] = calculate_capacity(time=df['time'], current=df['current'], absolute=False)
        df['capacity_total'] = calculate_capacity(time=df['time'], current=df['current'], absolute=True)
        # Store and return
        self.dataframe = df
        return df

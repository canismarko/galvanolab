import datetime as dt
import re
from pathlib import Path
from typing import Sequence, Union

import pandas as pd
import numpy as np

from galvanolab.basefile import BaseFile
from galvanolab.experiment import Experiment

# Type definitions
Filepath = Union[str, Path]
Filenames = Union[Filepath, Sequence[Filepath]]

class CHFile(BaseFile):
    def __init__(self, filename: Filenames):
        """
        
        Parameters
        ==========
        filename
          A file to import, a sequence of such files. If a sequence is
          given, the data will be concatenated.
        
        """
        # Check if we have a single file or multiple files
        if isinstance(filename, str) or isinstance(filename, Path):
            # Single file, so make it a list
            self.files = [filename]
        else:
            # Assume it's a sequence of files
            self.files = filename
        super().__init__(filename=filename)
    
    @property
    def dataframe(self) -> pd.DataFrame:
        df = pd.concat([self.load_echem_file(f) for f in self.files])
        df.sort_values('timestamp', inplace=True)
        return df
    
    def load_echem_file(self, fname: Filepath):
        """Load a single CH instrument e-chem file from disk."""
        with open(fname) as fp:
            timestamp = fp.readline().strip()
            timestamp_fmt = "%b. %d, %Y   %H:%M:%S"
            timestamp = np.datetime64(dt.datetime.strptime(timestamp, timestamp_fmt))
            technique = fp.readline()
            line = fp.readline()
            while line != "":
                line = fp.readline().strip()
            metadata = {}
            line = fp.readline().strip()
            while line != "":
                key, val = line.split("=")
                val = val.strip()
                try:
                    val = float(val)
                except ValueError:
                    pass
                metadata[key.strip()] = val
                line = fp.readline().strip()
            # Separate out the segments
            segments = []
            all_lines = iter(fp.readlines())
            header_re = re.compile("([a-z ]+/[a-z]+,? ?)+", flags=re.I)
            for line in all_lines:
                if header_re.match(line):
                    segments.append({"header": line.strip(), "body": []})
                elif line.strip() != "":
                    segments[-1]['body'].append(line.strip())
            # Convert each block to a dataframe
            last_timestamp = timestamp
            dfs = []
            is_charging = metadata['Init P/N'] == 'P'
            for segment in segments:
                new_df = self.parse_echem_segment(segment, last_timestamp)
                if len(new_df) > 0:
                    last_timestamp = new_df['timestamp'].max()
                # Fill in missing current/potential
                if "Current/A" not in new_df.columns:
                    current = metadata[f"{'Anodic' if is_charging else 'Cathodic'} Current (A)"]
                    # Make discharge currents negative
                    if not is_charging:
                        current *= -1
                    new_df['Current/A'] = current
                if "Potential/V" not in new_df.columns:
                    potential = metadata[f"{'High' if is_charging else 'Low'} E Limit (V)"]
                    new_df['Potential/V'] = potential
                    # Swap the polarity since now we go in the other direction
                    is_charging = not is_charging
                dfs.append(new_df)
            df = pd.concat(dfs)
            df.set_index('timestamp', inplace=True)
            # It seems that the timestamp at the top of the file is
            # actually the end of the experiment, so we need to adjust
            # all the timestamps
            duration = df.index.max() - df.index.min()
            df.set_index(df.index - duration, inplace=True)
            return df
    
    @staticmethod
    def parse_echem_segment(segment, time_0):
        # Prepare header columns
        header = segment['header'].replace("Hold Time/sec", "Time/sec")
        header = [h.strip() for h in header.split(',')]
        # Loop through the segment rows
        rows = []
        for line in segment['body']:
            row = {key.strip(): float(val.strip()) for key, val in zip(header, line.split(','))}
            rows.append(row)
        df = pd.DataFrame(rows)
        if len(df) > 0:
            df['timestamp'] = np.datetime64(time_0) + df['Time/sec'].astype("timedelta64[s]")
        return df

"""
ihmt/__init__.py
Copyright (C) 2026  Timothy Anderson

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from ihmt.meta import (
    Signal,
    Duration,
    Frequency,
    AngularFrequency,
    Angle,
    CompositeDictionary,
)
from ihmt.pulse import Tukey
from ihmt.system import System
from ihmt.sequence import Sequence
from ihmt.simulator import Simulator
from ihmt.corrector import Corrector
from ihmt.trajector import Trajector
from ihmt.run import SingleRun, GridRuns, SampledRuns

from ihmt.vectorized.pulse import TukeyVector

# Check if update available
current = 'undefined'
try:
    from importlib.metadata import version
    from requests import get, codes
    from tomllib import loads
    current = version('ihmt')
    response = get("https://raw.githubusercontent.com/SirTwinkleberry/ihMT/refs/heads/master/pyproject.toml")
    if response.status_code == codes.ok:
        head = loads(response.text)['project']['version']
        if head == current:
            print(f"You are running the latest version of the `ihmt` package. Version: {current}")
        else:
            print(f"Your version of the `ihmt` package is not up-to-date. Current version: {current}")
            print("Check https://github.com/SirTwinkleberry/ihMT for information on updating.")
    response.raise_for_status()
except Exception as e:
    print("Could not check if current `ihmt` package version is up-to-date.")
    print("You can check for yourself over at: https://github.com/SirTwinkleberry/ihMT")
    print(f"Current version: {current}")
    print(e)

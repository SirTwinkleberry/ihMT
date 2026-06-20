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

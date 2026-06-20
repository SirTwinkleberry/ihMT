"""
tests/test_meta.py
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

from ihmt.meta import _Event, Signal

from unittest import TestCase, skip

from numpy import set_printoptions
from sys import maxsize

set_printoptions(precision=maxsize)


@skip
class TestSignal(TestCase):
    def test_CM_in_ALT(self):
        self.assertFalse(Signal.CM in Signal.ALT)

    def test_ALT_in_CM(self):
        self.assertFalse(Signal.ALT in Signal.CM)

    def test_BP_in_ALT(self):
        self.assertFalse(Signal.BP in Signal.ALT)

    def test_BP_in_CM(self):
        self.assertFalse(Signal.BP in Signal.CM)

    def test_ALT_in_BP(self):
        self.assertTrue(Signal.ALT in Signal.BP)

    def test_CM_in_BP(self):
        self.assertTrue(Signal.CM in Signal.BP)


class TestMeta(TestCase): ...

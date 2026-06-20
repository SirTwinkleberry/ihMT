"""
tests/test_vectorized_pulse.py
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

from ihmt.vectorized.pulse import _PulseVector, TukeyVector

from unittest import TestCase, skip

from numpy import set_printoptions, atleast_1d
from sys import maxsize

set_printoptions(precision=maxsize)

CONFIG_TUKEY = {
    "init": {
        "duration": atleast_1d([1e-3]),
        "shape": atleast_1d([0.3]),
        "flipAngle": atleast_1d([299]),
        "offset": atleast_1d([7e3]),
    },
    "compute": {
        "amplitudeIntegral": atleast_1d([0.85]),
        "powerIntegral": atleast_1d([0.8125]),
        "b1peak": atleast_1d([2.2950108256258665e-05]),
        "omegaRMS": atleast_1d([5534.02752670352]),
    },
}


class TestPulse(TestCase):
    @skip(
        "Changing implementation to adapt to self.onChange / self._reset_computed_attributes"
    )
    def test___init__(self):
        with self.assertRaises(NotImplementedError):
            _PulseVector()

    @skip("Pulse constructor will raise NotImplementedError")
    def test_value(self):
        mock_pulse = _PulseVector()
        with self.assertRaises(NotImplementedError):
            mock_pulse.value(0)


class TestTukeyVector(TestCase):
    def test___init___Duration(self):
        pulse = TukeyVector(**CONFIG_TUKEY["init"])
        self.assertEqual(CONFIG_TUKEY["init"]["duration"], pulse.duration)

    def test___init___Shape(self):
        pulse = TukeyVector(**CONFIG_TUKEY["init"])
        self.assertEqual(CONFIG_TUKEY["init"]["shape"], pulse.shape)

    def test___init___FlipAngle(self):
        pulse = TukeyVector(**CONFIG_TUKEY["init"])
        self.assertEqual(CONFIG_TUKEY["init"]["flipAngle"], pulse.flipAngle)

    def test___init___Offset(self):
        pulse = TukeyVector(**CONFIG_TUKEY["init"])
        self.assertEqual(CONFIG_TUKEY["init"]["offset"], pulse.offset)

    def test__init__GyromagneticFactor(self):
        pulse = TukeyVector(**CONFIG_TUKEY["init"])
        self.assertEqual(267513000, pulse.gyromagneticFactor)

    def test__init__AmplitudeIntegral(self):
        pulse = TukeyVector(**CONFIG_TUKEY["init"])
        self.assertEqual(
            CONFIG_TUKEY["compute"]["amplitudeIntegral"], pulse.amplitudeIntegral
        )

    def test__init__PowerIntegral(self):
        pulse = TukeyVector(**CONFIG_TUKEY["init"])
        self.assertEqual(CONFIG_TUKEY["compute"]["powerIntegral"], pulse.powerIntegral)

    def test__init__B1peak(self):
        pulse = TukeyVector(**CONFIG_TUKEY["init"])
        self.assertEqual(CONFIG_TUKEY["compute"]["b1peak"], pulse.b1peak)

    def test__init__OmegaRMS(self):
        pulse = TukeyVector(**CONFIG_TUKEY["init"])
        self.assertEqual(CONFIG_TUKEY["compute"]["omegaRMS"], pulse.omegaRMS)

    def test_value_outside_bounds(self):
        pulse = TukeyVector(**CONFIG_TUKEY["init"])
        duration: float = CONFIG_TUKEY["init"]["duration"]
        for t in [-0.1 * duration, 0, duration, 1.1 * duration]:
            with self.subTest(number=t):
                self.assertEqual(pulse.value(t), 0)

    def test_value_ramping_up(self):
        pulse = TukeyVector(**CONFIG_TUKEY["init"])
        duration: float = CONFIG_TUKEY["init"]["duration"]
        shape: float = CONFIG_TUKEY["init"]["shape"]
        self.assertEqual(pulse.value(0.25 * shape * duration), 0.5)

    def test_value_ramping_down(self):
        pulse = TukeyVector(**CONFIG_TUKEY["init"])
        duration: float = CONFIG_TUKEY["init"]["duration"]
        shape: float = CONFIG_TUKEY["init"]["shape"]
        self.assertEqual(pulse.value(duration - 0.25 * shape * duration), 0.5)

    def test_value_plateau(self):
        pulse = TukeyVector(**CONFIG_TUKEY["init"])
        duration: float = CONFIG_TUKEY["init"]["duration"]
        shape: float = CONFIG_TUKEY["init"]["shape"]
        self.assertEqual(pulse.value(0.5 * shape * duration), 1)

    def test__reset_computed_attributes(self):
        pulse = TukeyVector(**CONFIG_TUKEY["init"])
        pulse.amplitudeIntegral
        pulse.powerIntegral
        pulse.b1peak
        pulse.omegaRMS
        pulse._onChanges = {}
        self.assertDictEqual(
            pulse.__dict__,
            {
                "_onChanges": {},
                "_gyromagneticFactor": 267513000,
                "_shape": 0.3,
                "_duration": 0.001,
                "_flipAngle": 299,
                "_offset": 7000.0,
                "_amplitudeIntegral": 0.85,
                "_powerIntegral": 0.8125,
                "_b1peak": 2.2950108256258665e-05,
                "_omegaRMS": 5534.02752670352,
            },
        )
        pulse._reset_computed_attributes(
            ["amplitudeIntegral", "powerIntegral", "b1peak", "omegaRMS"]
        )
        self.assertDictEqual(
            pulse.__dict__,
            {
                "_onChanges": {},
                "_gyromagneticFactor": 267513000,
                "_shape": 0.3,
                "_duration": 0.001,
                "_flipAngle": 299,
                "_offset": 7000.0,
            },
        )

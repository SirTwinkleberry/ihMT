"""
ihmt/pulse.py
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

from logging import getLogger, NullHandler
from abc import ABC
from numpy import cos, pi, sqrt
from scipy.integrate import quad
from operator import le, lt, gt
from typing import Any

from ihmt.meta import _Event, check_value_is_valid, _deg2rad

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug("`pulse` module loaded successfully")


class _Pulse(ABC, _Event):
    """_Abstraction class for pulses_

    Raises
    ------
    RuntimeError
        _raised when user calls `_Pulse().value` directly instead of through a daughter class
    """

    _gyromagneticFactor: float  # rad / s / T

    _duration: float  # s
    _flipAngle: float  # °
    _offset: float  # Hz

    _amplitudeIntegral: float
    _powerIntegral: float
    _b1peak: float
    _omegaRMS: float

    _classAttributes = (
        "gyromagneticFactor",
        "duration",
        "flipAngle",
        "offset",
        "amplitudeIntegral",
        "powerIntegral",
        "b1peak",
        "omegaRMS",
    )

    def __init__(self, *args: Any, **kwargs: Any):
        self.onChange(
            "gyromagneticFactor",
            [lambda: self._reset_computed_attributes(["b1peak", "omegaRMS"])],
        )
        self.onChange(
            "duration",
            [
                lambda: self._reset_computed_attributes(
                    ["amplitudeIntegral", "powerIntegral", "b1peak", "omegaRMS"]
                )
            ],
        )
        self.onChange(
            "flipAngle", [lambda: self._reset_computed_attributes(["b1peak"])]
        )
        self.onChange(
            "amplitudeIntegral", [lambda: self._reset_computed_attributes(["b1peak"])]
        )
        self.onChange(
            "powerIntegral", [lambda: self._reset_computed_attributes(["omegaRMS"])]
        )
        self.onChange("b1peak", [lambda: self._reset_computed_attributes(["omegaRMS"])])

    def value(self, t: float) -> float:
        error = "Method `_Pulse.value` should not be called directly. Use daughter class' `value` method instead."
        logger.critical(error)
        raise NotImplementedError(error)

    def copy(self) -> "_Pulse":
        return self.__class__(**self.__dict__)

    #####
    # BELOW: property getters and setters
    #####
    @property
    def gyromagneticFactor(self) -> float:
        if not hasattr(self, "_gyromagneticFactor"):
            self._gyromagneticFactor = 267513000.0
        return self._gyromagneticFactor

    @gyromagneticFactor.setter
    def gyromagneticFactor(self, val: float):
        check_value_is_valid(self, val, float, None, "gyromagneticFactor")
        self._gyromagneticFactor = float(val)
        self._changed("gyromagneticFactor")

    @property
    def duration(self) -> float:
        return self._duration

    @duration.setter
    def duration(self, val: float):
        check_value_is_valid(self, val, float, [(le, 0)], "duration")
        self._duration = float(val)
        self._changed("duration")

    @property
    def flipAngle(self) -> float:
        return self._flipAngle

    @flipAngle.setter
    def flipAngle(self, val: float):
        check_value_is_valid(self, val, float, [(le, 0)], "flipAngle")
        self._flipAngle = float(val)
        self._changed("flipAngle")

    @property
    def offset(self) -> float:
        return self._offset

    @offset.setter
    def offset(self, val: float):
        check_value_is_valid(self, val, float, None, "offset")
        self._offset = float(val)
        self._changed("offset")

    @property
    def amplitudeIntegral(self) -> float:
        if not hasattr(self, "_amplitudeIntegral"):
            self.amplitudeIntegral = (
                quad(self.value, 0, self.duration)[0] / self.duration
            )
        return self._amplitudeIntegral

    @amplitudeIntegral.setter
    def amplitudeIntegral(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0), (gt, 1)], "amplitudeIntegral")
        self._amplitudeIntegral = val
        self._changed("amplitudeIntegral")

    @amplitudeIntegral.deleter
    def amplitudeIntegral(self):
        del self._amplitudeIntegral
        self._changed("amplitudeIntegral")

    @property
    def powerIntegral(self) -> float:
        if not hasattr(self, "_powerIntegral"):
            self.powerIntegral = (
                quad(lambda t: self.value(t) ** 2, 0, self.duration)[0] / self.duration
            )
        return self._powerIntegral

    @powerIntegral.setter
    def powerIntegral(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0), (gt, 1)], "powerIntegral")
        self._powerIntegral = val
        self._changed("powerIntegral")

    @powerIntegral.deleter
    def powerIntegral(self):
        del self._powerIntegral
        self._changed("powerIntegral")

    @property
    def b1peak(self) -> float:
        if not hasattr(self, "_b1peak"):
            self.b1peak = (
                _deg2rad
                * self.flipAngle
                / (self.gyromagneticFactor * self.amplitudeIntegral * self.duration)
            )
        return self._b1peak

    @b1peak.setter
    def b1peak(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0)], "b1peak")
        self._b1peak = val
        self._changed("b1peak")

    @b1peak.deleter
    def b1peak(self):
        del self._b1peak
        self._changed("b1peak")

    @property
    def b1(self):
        return self.b1peak * self.amplitudeIntegral

    @property
    def b1RMS(self):
        return self.b1peak * sqrt(self.powerIntegral)

    @property
    def omegaRMS(self) -> float:
        if not hasattr(self, "_omegaRMS"):
            self.omegaRMS = self.b1RMS * self.gyromagneticFactor
            # self.omegaRMS = sqrt(self.powerIntegral) * abs(self.b1peak * self.gyromagneticFactor / self.duration)
        return self._omegaRMS

    @omegaRMS.setter
    def omegaRMS(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0)], "omegaRMS")
        self._omegaRMS = val
        self._changed("omegaRMS")

    @omegaRMS.deleter
    def omegaRMS(self):
        del self._omegaRMS
        self._changed("omegaRMS")


class Tukey(_Pulse):
    _shape: float  # r factor for Tukey shape

    _classAttributes = ("shape", *_Pulse._get_classAttributes())

    def __init__(
        self,
        duration: float,
        shape: float,
        flipAngle: float,
        offset: float,
        *args: Any,
        **kwargs: Any,
    ):
        """_Tukey pulse class_

        Parameters
        ----------
        duration : float
            _pulse duration in seconds
        shape : float
            _Tukey shape factor ("r" parameter)_
        flipAngle : float
            _pulse flip angle in degrees_
        offset : float
            _pulse offset frequency in Hertz_
        """
        super().__init__()

        self.shape = shape
        self.duration = duration
        self.flipAngle = flipAngle
        self.offset = offset

        self.onChange(
            "shape",
            [
                lambda: self._reset_computed_attributes(
                    ["amplitudeIntegral", "powerIntegral"]
                )
            ],
        )

    def copy(self) -> "Tukey":
        return Tukey(self.duration, self.shape, self.flipAngle, self.offset)

    def value(self, t: float) -> float:
        """_summary_

        Parameters
        ----------
        t : float
            _description_

        Returns
        -------
        float
            _description_
        """
        if (t <= 0) or (t >= self.duration):
            return 0

        dimless_time = t / self.duration

        if (0 < dimless_time) & (dimless_time < 0.5 * self.shape):
            pulse: float = 0.5 * (1 + cos(pi * (-1 + 2 * dimless_time / self.shape)))

        elif (0.5 * self.shape <= dimless_time) & (
            dimless_time <= 1 - 0.5 * self.shape
        ):
            pulse = 1

        else:
            pulse: float = 0.5 * (
                1 + cos(pi * (1 - 2 / self.shape + 2 * dimless_time / self.shape))
            )

        return pulse

    #####
    # BELOW: property getters and setters
    #####
    @property
    def shape(self) -> float:
        return self._shape

    @shape.setter
    def shape(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0), (gt, 1)], "shape")
        self._shape = val
        self._changed("shape")

    @property
    def amplitudeIntegral(self) -> float:
        if not hasattr(self, "_amplitudeIntegral"):
            self.amplitudeIntegral = 1 - 0.5 * self.shape
        return self._amplitudeIntegral

    @amplitudeIntegral.setter
    def amplitudeIntegral(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0), (gt, 1)], "amplitudeIntegral")
        self._amplitudeIntegral = val
        self._changed("amplitudeIntegral")

    @amplitudeIntegral.deleter
    def amplitudeIntegral(self):
        del self._amplitudeIntegral
        self._changed("amplitudeIntegral")

    @property
    def powerIntegral(self) -> float:
        if not hasattr(self, "_powerIntegral"):
            self.powerIntegral = 1 - 0.625 * self.shape
        return self._powerIntegral

    @powerIntegral.setter
    def powerIntegral(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0), (gt, 1)], "powerIntegral")
        self._powerIntegral = val
        self._changed("powerIntegral")

    @powerIntegral.deleter
    def powerIntegral(self):
        del self._powerIntegral
        self._changed("powerIntegral")


type Pulse = _Pulse  # Python 3.12 feature

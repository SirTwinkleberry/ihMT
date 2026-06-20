"""
ihmt/vectorized/pulse.py
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
from numpy import atleast_1d, meshgrid, zeros_like, cos, pi, sqrt, number, ndarray
from scipy.integrate import quad
from operator import le, lt, gt
from typing import Any, NewType
from copy import deepcopy

from ihmt.meta import _Event, check_value_is_valid, _deg2rad, ScalarOrVector

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug("`pulse` module loaded successfully")


class _PulseVector(ABC, _Event):
    """_Abstraction class for pulses_

    Raises
    ------
    RuntimeError
        _raised when user calls `_Pulse().value` directly instead of through a daughter class
    """

    _gyromagneticFactor: ndarray[number]  # rad / s / T

    _duration: ndarray[number]  # s
    _flipAngle: ndarray[number]  # °
    _offset: ndarray[number]  # Hz

    _amplitudeIntegral: ndarray[number]
    _powerIntegral: ndarray[number]
    _b1peak: ndarray[number]
    _omegaRMS: ndarray[number]

    _classAttributes: tuple[str] = (
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
        self.onChange("gyromagneticFactor", [self._reshape])
        self.onChange("duration", [self._reshape])
        self.onChange("flipAngle", [self._reshape])
        self.onChange("amplitudeIntegral", [self._reshape])
        self.onChange("powerIntegral", [self._reshape])
        self.onChange("b1peak", [self._reshape])

    def value(self, t: float) -> float:
        error = "Method `_Pulse.value` should not be called directly. Use daughter class' `value` method instead."
        logger.critical(error)
        raise NotImplementedError(error)

    def copy(self) -> _PulseVector:
        return self(
            **{
                key.replace("_vector_", ""): deepcopy(value)
                for key, value in self.__dict__.items()
                if "_vector_" in key
            }
        )

    #####
    # BELOW: property getters and setters
    #####
    @property
    def gyromagneticFactor(self) -> ndarray[number]:
        if not hasattr(self, "_gyromagneticFactor"):
            self._gyromagneticFactor = atleast_1d(267513000.0)
        return self._gyromagneticFactor

    @gyromagneticFactor.setter
    def gyromagneticFactor(self, val: ScalarOrVector):
        check_value_is_valid(self, val, ScalarOrVector, None, "gyromagneticFactor")
        self._gyromagneticFactor = atleast_1d(val)
        self._changed("gyromagneticFactor")

    @property
    def duration(self) -> ndarray[number]:
        return self._duration

    @duration.setter
    def duration(self, val: ScalarOrVector):
        check_value_is_valid(self, val, ScalarOrVector, [(le, 0)], "duration")
        self._duration = atleast_1d(val)
        self._changed("duration")

    @property
    def flipAngle(self) -> ndarray[number]:
        return self._flipAngle

    @flipAngle.setter
    def flipAngle(self, val: ScalarOrVector):
        check_value_is_valid(self, val, ScalarOrVector, [(le, 0)], "flipAngle")
        self._flipAngle = atleast_1d(val)
        self._changed("flipAngle")

    @property
    def offset(self) -> ndarray[number]:
        return self._offset

    @offset.setter
    def offset(self, val: ScalarOrVector):
        check_value_is_valid(self, val, ScalarOrVector, None, "offset")
        self._offset = atleast_1d(val)
        self._changed("offset")

    @property
    def amplitudeIntegral(self) -> ndarray[number]:
        if not hasattr(self, "_amplitudeIntegral"):
            self._amplitudeIntegral = (
                quad(self.value, 0, self.duration)[0] / self.duration
            )
            self._changed("amplitudeIntegral")
        return self._amplitudeIntegral

    @amplitudeIntegral.deleter
    def amplitudeIntegral(self):
        del self._amplitudeIntegral
        self._changed("amplitudeIntegral")

    @property
    def powerIntegral(self) -> ndarray[number]:
        if not hasattr(self, "_powerIntegral"):
            self._powerIntegral = (
                quad(lambda t: self.value(t) ** 2, 0, self.duration)[0] / self.duration
            )
            self._changed("powerIntegral")
        return self._powerIntegral

    @powerIntegral.deleter
    def powerIntegral(self):
        del self._powerIntegral
        self._changed("powerIntegral")

    @property
    def b1peak(self) -> ndarray[number]:
        if not hasattr(self, "_b1peak"):
            self._b1peak = (
                _deg2rad
                * self.flipAngle
                / (self.gyromagneticFactor * self.amplitudeIntegral * self.duration)
            )
            self._changed("b1peak")
        return self._b1peak

    @b1peak.deleter
    def b1peak(self):
        del self._b1peak
        self._changed("b1peak")

    @property
    def b1(self) -> ndarray[number]:
        return self.b1peak * self.amplitudeIntegral

    @property
    def b1RMS(self) -> ndarray[number]:
        return self.b1peak * sqrt(self.powerIntegral)

    @property
    def omegaRMS(self) -> ndarray[number]:
        if not hasattr(self, "_omegaRMS"):
            self.omegaRMS = self.b1RMS * self.gyromagneticFactor
            self._changed("omegaRMS")
        return self._omegaRMS

    @omegaRMS.deleter
    def omegaRMS(self):
        del self._omegaRMS
        self._changed("omegaRMS")


class TukeyVector(_PulseVector):
    _shape: ndarray[number]  # r factor for Tukey shape

    _classAttributes: tuple[str] = ("shape", *_PulseVector._get_classAttributes())
    _broadcastshape: tuple[int]

    def __init__(
        self,
        duration: ScalarOrVector,
        shape: ScalarOrVector,
        flipAngle: ScalarOrVector,
        offset: ScalarOrVector,
        *args: Any,
        **kwargs: Any
    ):
        """_Tukey pulse class_

        Parameters
        ----------
        duration : ScalarOrVector
            _pulse duration in seconds
        shape : ScalarOrVector
            _Tukey shape factor ("r" parameter)_
        flipAngle : ScalarOrVector
            _pulse flip angle in degrees_
        offset : ScalarOrVector
            _pulse offset frequency in Hertz_
        """
        super().__init__()

        duration, shape, flipAngle, offset = (
            atleast_1d(duration),
            atleast_1d(shape),
            atleast_1d(flipAngle),
            atleast_1d(offset),
        )

        self._vector_duration = duration
        self._vector_shape = shape
        self._vector_flipAngle = flipAngle
        self._vector_offset = offset

        self._reshape()

        self.onChange("shape", [self._reshape])

    def copy(self) -> TukeyVector:
        return TukeyVector(
            deepcopy(self._vector_duration),
            deepcopy(self._vector_shape),
            deepcopy(self._vector_flipAngle),
            deepcopy(self._vector_offset),
        )

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
        pulse = zeros_like(self.duration)
        if t <= 0:
            return pulse

        dimless_time = t / self.duration

        mask = (0 < dimless_time) & (dimless_time < 0.5 * self.shape)
        pulse[mask] = 0.5 * (
            1 + cos(pi * (-1 + 2 * dimless_time[mask] / self.shape[mask]))
        )

        mask = (0.5 * self.shape <= dimless_time) & (
            dimless_time <= 1 - 0.5 * self.shape
        )
        pulse[mask] = 1

        mask = (1 > dimless_time) & (dimless_time > (1 - 0.5 * self.shape))
        pulse[mask] = 0.5 * (
            1
            + cos(
                pi
                * (1 - 2 / self.shape[mask] + 2 * dimless_time[mask] / self.shape[mask])
            )
        )

        return pulse

    def _reshape(self):
        DD, SS, FF, OO = meshgrid(
            self._vector_duration,
            self._vector_shape,
            self._vector_flipAngle,
            self._vector_offset,
            indexing="ij",
            sparse=False,
        )

        self.duration = DD
        self.shape = SS
        self.flipAngle = FF
        self.offset = OO

    #####
    # BELOW: property getters and setters
    #####
    @property
    def shape(self) -> ndarray[number]:
        return self._shape

    @shape.setter
    def shape(self, val: ScalarOrVector):
        check_value_is_valid(self, val, ScalarOrVector, [(lt, 0), (gt, 1)], "shape")
        self._shape = atleast_1d(val)
        self._changed("shape")

    @property
    def amplitudeIntegral(self) -> ndarray[number]:
        if not hasattr(self, "_amplitudeIntegral"):
            self._amplitudeIntegral = 1 - 0.5 * self.shape
            self._changed("amplitudeIntegral")
        return self._amplitudeIntegral

    @amplitudeIntegral.deleter
    def amplitudeIntegral(self):
        del self._amplitudeIntegral
        self._changed("amplitudeIntegral")

    @property
    def powerIntegral(self) -> ndarray[number]:
        if not hasattr(self, "_powerIntegral"):
            self._powerIntegral = 1 - 0.625 * self.shape
            self._changed("powerIntegral")
        return self._powerIntegral

    @powerIntegral.deleter
    def powerIntegral(self):
        del self._powerIntegral
        self._changed("powerIntegral")


PulseVector = NewType("Pulse", _PulseVector)

from logging import getLogger, NullHandler
from abc import ABC
from numpy import cos, pi, sqrt, radians
from scipy.integrate import quad
from operator import le, lt, gt
from typing import Any
from collections.abc import Callable

from brainhack.meta import _Event

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug('`pulse` module loaded successfully')


class _Pulse(ABC, _Event):
    """_Abstraction class for pulses_

    Raises
    ------
    RuntimeError
        _raised when user calls `_Pulse().value` directly instead of through a daughter class
    """
    _gyromagneticFactor: float       # rad / s / T

    _duration: float                 # s
    _flipAngle: float                # °
    _offset: float                   # Hz

    _amplitudeIntegral: float
    _powerIntegral: float
    _b1peak: float
    _omegaRMS: float

    _classAttributes: tuple[str] = ('gyromagneticFactor', 'duration', 'flipAngle', 'offset', 'amplitudeIntegral', 'powerIntegral', 'b1peak', 'omegaRMS')

    def __init__(self, *args: Any, **kwargs: Any):
        error = "Object `_Pulse` should not be instantiated directly. Use daughter classes instead."
        logger.critical(error)
        raise NotImplementedError(error)

    def value(self, t: float) -> float:
        error = "Method `_Pulse.value` should not be called directly. Use daughter class' `value` method instead."
        logger.critical(error)
        raise NotImplementedError(error)

    def check_type(self, val_to_check: Any, type_to_check: type, operators: None | list[tuple[Callable, int | float]], attribute_name: str):
        if type_to_check(val_to_check) != val_to_check:
            error = f'`{attribute_name}` must be safely castable to integer. Received: {repr(val_to_check)}.'
            logger.critical(error)
            raise ValueError(error)

        if operators is not None:
            for operator, bound in operators:
                if operator == le:
                    boundStr = f'less or equal to {bound}'
                elif operator == lt:
                    boundStr = f'less than {bound}'
                elif operator == gt:
                    boundStr = f'greater than {bound}'
                else:
                    error = f"Operator {operator} was not implemented."
                    logger.critical(error)
                    raise NotImplementedError(error)

                if operator(val_to_check, bound):
                    error = f'`{attribute_name}` cannot be {boundStr}. Received: {repr(val_to_check)}.'
                    logger.critical(error)
                    raise ValueError(error)

    #####
    # BELOW: property getters and setters
    #####
    @property
    def gyromagneticFactor(self) -> float:
        if not hasattr(self, '_gyromagneticFactor'):
            self._gyromagneticFactor = 267513000
        return self._gyromagneticFactor

    @gyromagneticFactor.setter
    def gyromagneticFactor(self, val: float):
        self.check_type(val, float, None, 'gyromagneticFactor')
        self._gyromagneticFactor = val
        self._changed('gyromagneticFactor')
        self._resetComputedAttributes(['b1peak', 'omegaRMS'])

    @property
    def duration(self) -> float:
        return self._duration

    @duration.setter
    def duration(self, val: float):
        self.check_type(val, float, [(le, 0)], 'duration')
        self._duration = val
        self._changed('duration')
        self._resetComputedAttributes(['amplitudeIntegral', 'powerIntegral', 'b1peak', 'omegaRMS'])

    @property
    def flipAngle(self) -> float:
        return self._flipAngle

    @flipAngle.setter
    def flipAngle(self, val: float):
        self.check_type(val, float, [(le, 0)], 'flipAngle')
        self._flipAngle = val
        self._changed('flipAngle')
        self._resetComputedAttributes(['b1peak'])

    @property
    def offset(self) -> float:
        return self._offset

    @offset.setter
    def offset(self, val: float):
        self.check_type(val, float, None, 'offset')
        self._offset = val
        self._changed('offset')

    @property
    def amplitudeIntegral(self) -> float:
        if not hasattr(self, '_amplitudeIntegral'):
            self.amplitudeIntegral = quad(self.value, 0, self.duration)[0] / self.duration
        return self._amplitudeIntegral

    @amplitudeIntegral.setter
    def amplitudeIntegral(self, val: float):
        self.check_type(val, float, [(lt, 0), (gt, 1)], 'amplitudeIntegral')
        self._amplitudeIntegral = val
        self._changed('amplitudeIntegral')
        self._resetComputedAttributes(['b1peak'])

    @amplitudeIntegral.deleter
    def amplitudeIntegral(self):
        del self._amplitudeIntegral
        self._changed('amplitudeIntegral')
        self._resetComputedAttributes(['b1peak'])

    @property
    def powerIntegral(self) -> float:
        if not hasattr(self, '_powerIntegral'):
            self.powerIntegral = quad(lambda t: self.value(t)**2, 0, self.duration)[0] / self.duration
        return self._powerIntegral

    @powerIntegral.setter
    def powerIntegral(self, val: float):
        self.check_type(val, float, [(lt, 0), (gt, 1)], 'powerIntegral')
        self._powerIntegral = val
        self._changed('powerIntegral')
        self._resetComputedAttributes(['omegaRMS'])

    @powerIntegral.deleter
    def powerIntegral(self):
        del self._powerIntegral
        self._changed('powerIntegral')
        self._resetComputedAttributes(['omegaRMS'])

    @property
    def b1peak(self) -> float:
        if not hasattr(self, '_b1peak'):
            self.b1peak = radians(self.flipAngle) / (self.gyromagneticFactor * self.amplitudeIntegral * self.duration)
        return self._b1peak

    @b1peak.setter
    def b1peak(self, val: float):
        self.check_type(val, float, [(lt, 0)], 'b1peak')
        self._b1peak = val
        self._changed('b1peak')
        self._resetComputedAttributes(['omegaRMS'])

    @b1peak.deleter
    def b1peak(self):
        del self._b1peak
        self._changed('b1peak')
        self._resetComputedAttributes(['omegaRMS'])

    @property
    def b1(self):
        return self.b1peak * self.amplitudeIntegral

    @property
    def b1RMS(self):
        return self.b1peak * sqrt(self.powerIntegral)

    @property
    def omegaRMS(self) -> float:
        if not hasattr(self, '_omegaRMS'):
            self.omegaRMS = self.b1RMS * self.gyromagneticFactor
            # self.omegaRMS = sqrt(self.powerIntegral) * abs(self.b1peak * self.gyromagneticFactor / self.duration)
        return self._omegaRMS

    @omegaRMS.setter
    def omegaRMS(self, val: float):
        self.check_type(val, float, [(lt, 0)], 'omegaRMS')
        self._omegaRMS = val
        self._changed('omegaRMS')

    @omegaRMS.deleter
    def omegaRMS(self):
        del self._omegaRMS
        self._changed('omegaRMS')


class Tukey(_Pulse):
    _shape: float  # r factor for Tukey shape
    
    _classAttributes: tuple[str] = ('shape', *_Pulse._get_classAttributes())

    def __init__(self, duration: float, shape: float, flipAngle: float, offset: float, *args: Any, **kwargs: Any):
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
        self.shape = shape
        self.duration = duration
        self.flipAngle = flipAngle
        self.offset = offset

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

        if (0 < dimless_time) & (dimless_time < .5 * self.shape):
            pulse: float = 0.5 * ( 1 + cos(pi * (-1 + 2 * dimless_time / self.shape)) )

        elif (.5 * self.shape <= dimless_time) & (dimless_time <= 1 - .5 * self.shape):
            pulse = 1

        else:
            pulse: float = 0.5 * ( 1 + cos(pi * (1 - 2 / self.shape + 2 * dimless_time / self.shape)) )

        return pulse

    #####
    # BELOW: property getters and setters
    #####
    @property
    def shape(self) -> float:
        return self._shape

    @shape.setter
    def shape(self, val: float):
        self.check_type(val, float, [(lt, 0), (gt, 1)], 'shape')
        self._shape = val
        self._changed('shape')
        self._resetComputedAttributes(['amplitudeIntegral', 'powerIntegral'])

    @property
    def amplitudeIntegral(self) -> float:
        if not hasattr(self, '_amplitudeIntegral'):
            self.amplitudeIntegral = 1 - .5 * self.shape
        return self._amplitudeIntegral

    @amplitudeIntegral.setter
    def amplitudeIntegral(self, val: float):
        self.check_type(val, float, [(lt, 0), (gt, 1)], 'amplitudeIntegral')
        self._amplitudeIntegral = val
        self._changed('amplitudeIntegral')
        self._resetComputedAttributes(['b1peak'])

    @amplitudeIntegral.deleter
    def amplitudeIntegral(self):
        del self._amplitudeIntegral
        self._resetComputedAttributes(['b1peak'])

    @property
    def powerIntegral(self) -> float:
        if not hasattr(self, '_powerIntegral'):
            self.powerIntegral = 1 - 0.625 * self.shape
        return self._powerIntegral

    @powerIntegral.setter
    def powerIntegral(self, val: float):
        self.check_type(val, float, [(lt, 0), (gt, 1)], 'powerIntegral')
        self._powerIntegral = val
        self._changed('powerIntegral')
        self._resetComputedAttributes(['omegaRMS'])

    @powerIntegral.deleter
    def powerIntegral(self):
        del self._powerIntegral
        self._resetComputedAttributes(['omegaRMS'])

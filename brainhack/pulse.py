# from logging import
from typing import Any
from collections.abc import Callable
from numpy import cos, pi, sqrt, radians
from scipy.integrate import quad
from operator import le, lt, gt


class Pulse():
    """_Abstraction class for pulses_

    Raises
    ------
    RuntimeError
        _raised when user calls `Pulse().value` directly instead of through a daughter class
    """

    _gyromagneticFactor: float       # rad / s / T

    _duration: float                 # s
    _flipAngle: float                # °
    _offset: float                   # Hz

    _amplitudeIntegral: float
    _powerIntegral: float
    _b1peak: float
    _omegaRMS: float

    _onChange: dict[str, list[Callable]]

    def __init__(self, *args: Any, **kwargs: Any):
        raise NotImplementedError("Object `Pulse` should not be instantiated directly. Use daughter classes instead.")

    def value(self, t: float) -> float:
        raise NotImplementedError("Pulse.value should not be called directly. User daughter class' `value` method instead.")

    def check_type(self, val_to_check: Any, type_to_check: type, operators: None | list[tuple[Callable, int | float]], attribute_name: str):
        if type_to_check(val_to_check) != val_to_check:
            raise ValueError(f'`{attribute_name}` must be safely castable to integer. Received: {repr(val_to_check)}.')
        if operators is not None:
            for operator, bound in operators:
                if operator == le:
                    boundStr = f'less or equal to {bound}'
                elif operator == lt:
                    boundStr = f'less than {bound}'
                elif operator == gt:
                    boundStr = f'greater than {bound}'
                else:
                    raise NotImplementedError(f"Operator {operator} was not implemented.")
                if operator(val_to_check, bound):
                    raise ValueError(f'`{attribute_name}` cannot be {boundStr}. Received: {repr(val_to_check)}.')

    def resetComputedAttributes(self):
        if hasattr(self, '_amplitudeIntegral'):
            del self._amplitudeIntegral
            self._changed('amplitudeIntegral')
        if hasattr(self, '_powerIntegral'):
            del self._powerIntegral
            self._changed('powerIntegral')
        if hasattr(self, '_b1peak'):
            del self._b1peak
            self._changed('b1peak')
        if hasattr(self, '_omegaRMS'):
            del self._omegaRMS
            self._changed('omegaRMS')

    def onChange(self, attribute: str, callbacks: list[Callable]):
        if attribute not in ['gyromagneticFactor', 'duration', 'flipAngle', 'offset', 'amplitudeIntegral', 'powerIntegral', 'b1peak', 'omegaRMS']:
            raise ValueError(f"`attribute` name is not within acceptable values ['duration', 'offset', 'omegaRMS'] for callbacks. Received `{attribute}`.")

        if attribute not in self._get_onChange.keys():
            self._get_onChange[attribute] = []
        # print(self._get_onChange[attribute])
        self._get_onChange[attribute].extend(callbacks)
        # print(self._get_onChange)

    def _changed(self, attribute: str):
        if attribute in self._get_onChange.keys():
            for callback in self._get_onChange[attribute]:
                try:
                    callback()
                except Exception:
                    pass

    #####
    # BELOW: property getters and setters
    #####
    @property
    def _get_onChange(self) -> dict[str, list[Callable]]:
        if not hasattr(self, '_onChange'):
            self._onChange = dict()
        return self._onChange

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
        self.resetComputedAttributes()

    @property
    def duration(self) -> float:
        return self._duration

    @duration.setter
    def duration(self, val: float):
        self.check_type(val, float, [(le, 0)], 'duration')
        self._duration = val
        self._changed('duration')
        self.resetComputedAttributes()

    @property
    def flipAngle(self) -> float:
        return self._flipAngle

    @flipAngle.setter
    def flipAngle(self, val: float):
        self.check_type(val, float, [(le, 0)], 'flipAngle')
        self._flipAngle = val
        self._changed('flipAngle')
        self.resetComputedAttributes()

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

    @amplitudeIntegral.deleter
    def amplitudeIntegral(self):
        del self._amplitudeIntegral

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

    @powerIntegral.deleter
    def powerIntegral(self):
        del self._powerIntegral

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

    @b1peak.deleter
    def b1peak(self):
        del self._b1peak

    @property
    def omegaRMS(self) -> float:
        if not hasattr(self, '_omegaRMS'):
            self.omegaRMS = sqrt(quad(lambda t: self.value(t)**2, 0, self.duration)[0]
                                 * self.b1peak * self.b1peak  * self.gyromagneticFactor * self.gyromagneticFactor
                                 / self.duration)
        return self._omegaRMS

    @omegaRMS.setter
    def omegaRMS(self, val: float):
        self.check_type(val, float, [(lt, 0)], 'omegaRMS')
        self._omegaRMS = val
        self._changed('omegaRMS')

    @omegaRMS.deleter
    def omegaRMS(self):
        del self._omegaRMS


class Tukey(Pulse):
    shape: float  # r factor for Tukey shape

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
        self.resetComputedAttributes()

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

    @amplitudeIntegral.deleter
    def amplitudeIntegral(self):
        del self._amplitudeIntegral

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

    @powerIntegral.deleter
    def powerIntegral(self):
        del self._powerIntegral

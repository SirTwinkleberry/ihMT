from typing import Any
from numpy import cos, pi, sqrt, radians
from scipy.integrate import quad


class Pulse():
    """_Abstraction class for pulses_

    Raises
    ------
    RuntimeError
        _raised when user calls `Pulse().value` directly instead of through a daughter class
    """

    __gyromagneticFactor = 267513000  # rad / s / T

    __duration: float                 # s
    __flipAngle: float                # °
    __offset: float                   # Hz

    __amplitudeIntegral: float
    __powerIntegral: float
    __b1peak: float
    __omegaRMS: float

    def __init__(self, *args: Any, **kwargs: Any):
        raise NotImplementedError("Object `Pulse` should not be instantiated directly. Use daughter classes instead.")

    def resetComputedAttributes(self):
        if hasattr(self, '__amplitudeIntegral'): del self.__amplitudeIntegral  # noqa: E701
        if hasattr(self, '__powerIntegral'): del self.__powerIntegral  # noqa: E701
        if hasattr(self, '__b1peak'): del self.__b1peak  # noqa: E701
        if hasattr(self, '__omegaRMS'): del self.__omegaRMS  # noqa: E701
        # Add callback for system and sequence, emit "onChange" signal on each setter + resetComputedAttributes
        # and have onChange() go through a dict of self attribute / list of callbacks pairs?

    def value(self, t: float) -> float:
        raise NotImplementedError("Pulse.value should not be called directly. User daughter class' `value` method instead.")

    #####
    # BELOW: property getters and setters
    #####
    @property
    def gyromagneticFactor(self) -> float:
        return self.__gyromagneticFactor

    @gyromagneticFactor.setter
    def gyromagneticFactor(self, val: float):
        self.__gyromagneticFactor = val
        self.resetComputedAttributes()

    @property
    def duration(self) -> float:
        return self.__duration

    @duration.setter
    def duration(self, val: float):
        if val <= 0:
            raise ValueError(f"Value cannot be non-positive. Received {val} [s].")
        self.__duration = val
        self.resetComputedAttributes()

    @property
    def flipAngle(self) -> float:
        return self.__flipAngle

    @flipAngle.setter
    def flipAngle(self, val: float):
        if val <= 0:
            raise ValueError(f"Value cannot be non-positive. Received {val} [s].")
        self.__flipAngle = val
        self.resetComputedAttributes()

    @property
    def offset(self) -> float:
        return self.__offset

    @offset.setter
    def offset(self, val: float):
        self.__offset = val

    @property
    def amplitudeIntegral(self) -> float:
        if not hasattr(self, '__amplitudeIntegral'):
            self.amplitudeIntegral = quad(self.value, 0, self.duration)[0] / self.duration
        return self.__amplitudeIntegral

    @amplitudeIntegral.setter
    def amplitudeIntegral(self, val: float):
        self.__amplitudeIntegral = val

    @property
    def powerIntegral(self) -> float:
        if not hasattr(self, '__powerIntegral'):
            self.powerIntegral = quad(lambda t: self.value(t)**2, 0, self.duration)[0] / self.duration
        return self.__powerIntegral

    @powerIntegral.setter
    def powerIntegral(self, val: float):
        self.__powerIntegral = val

    @property
    def b1peak(self) -> float:
        if not hasattr(self, '__b1peak'):
            self.b1peak = radians(self.flipAngle) / (self.gyromagneticFactor * self.amplitudeIntegral * self.duration)
        return self.__b1peak

    @b1peak.setter
    def b1peak(self, val: float):
        self.__b1peak = val

    @property
    def omegaRMS(self) -> float:
        if not hasattr(self, '__omegaRMS'):
            self.omegaRMS = sqrt(quad(lambda t: self.value(t)**2, 0, self.duration)[0]
                                 * self.b1peak * self.b1peak  * self.gyromagneticFactor * self.gyromagneticFactor
                                 / self.duration)
        return self.__omegaRMS

    @omegaRMS.setter
    def omegaRMS(self, val: float):
        self.__omegaRMS = val


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
        return self.__shape

    @shape.setter
    def shape(self, val: float):
        if (val < 0) or (val > 1):
            raise ValueError(f"Value cannot be outside the [0, 1] inclusive range. Received {val} [s].")
        self.__shape = val
        self.resetComputedAttributes()

    @property
    def amplitudeIntegral(self) -> float:
        if not hasattr(self, '__amplitudeIntegral'):
            self.amplitudeIntegral = 1 - .5 * self.shape
        return self.__amplitudeIntegral

    @amplitudeIntegral.setter
    def amplitudeIntegral(self, val: float):
        self.__amplitudeIntegral = val

    @property
    def powerIntegral(self) -> float:
        if not hasattr(self, '__powerIntegral'):
            self.powerIntegral = 1 - 0.625 * self.shape
        return self.__powerIntegral

    @powerIntegral.setter
    def powerIntegral(self, val: float):
        self.__powerIntegral = val

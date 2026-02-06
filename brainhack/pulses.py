from typing import Any
from collections.abc import Callable
from numpy import cos, pi, sqrt, radians
from scipy.integrate import quad  # type: ignore


class Pulse():
    """_Abstraction class for pulses_

    Raises
    ------
    RuntimeError
        _raised when user calls `Pulse().value` directly instead of through a daughter class
    """

    gyromagneticFactor = 1e6 * 267.513  # rad / s / T

    duration: float                     # s
    flipAngle: float                    # °
    offset: float                       # Hz

    amplitudeIntegral: float
    powerIntegral: float
    b1peak: float
    omegaRMS: float

    def __init__(self, *args: Any, **kwargs: Any):
        raise NotImplementedError("Object `Pulse` should not be instantiated directly. Use daughter classes instead.")

    def compute(self):
        if type(self) is Pulse:
            raise NotImplementedError("Object `Pulse` should not be instantiated directly. Use daughter classes instead.")

        invDuration = 1. / self.duration

        self.amplitudeIntegral: float = invDuration * quad(self.value, 0, self.duration)[0]                                    # no dimension
        self.powerIntegral: float = invDuration * quad(lambda t: self.value(t)**2, 0, self.duration)[0]  # type: ignore        # no dimension

        self.b1peak: float = radians(self.flipAngle) / (self.gyromagneticFactor * self.amplitudeIntegral * self.duration)  # type: ignore   # T

        omega: Callable[[float], float] = lambda t: self.value(t) * self.b1peak * self.gyromagneticFactor                       # rad / s
        self.omegaRMS: float = sqrt(invDuration * quad(lambda t: omega(t)**2, 0, self.duration)[0])  # type: ignore             # rad / s

    def value(self, t: float) -> float:
        raise NotImplementedError("Pulse.value should not be called directly. User daughter class' `value` method instead.")


class Tukey(Pulse):
    shape: float                        # r factor for Tukey shape

    def __init__(self, duration: float, shape: float, flipAngle: float, offset: float):
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

        self.compute()

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
        # see https://git.bitbybyte.fi/publicgroup/quantumwheelpublic/blob/c99f7f912244379e9d5ed2bbd41f976578efcda1/QuantumWheel/Assets/Plugins/QuantumWheel/.Python/scipy/signal/windows/windows.py
        # inputs:
        #   t: float = time(s) at which we sample the pulse
        # output:
        #   pulse: float = amplitude at time `t`

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

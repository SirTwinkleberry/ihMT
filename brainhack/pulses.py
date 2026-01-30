from typing import Callable
from numpy import cos, pi, sqrt, radians
from scipy.integrate import quad


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
    B1peak: float
    omegaRMS: float

    B1: Callable
    omega: Callable
    omegaSquared: Callable

    def compute(self):
        invDuration = 1. / self.duration

        self.amplitudeIntegral: float = invDuration * quad(self.value, 0, self.duration)[0]                                     # no dimension
        self.powerIntegral: float = invDuration * quad(lambda t: self.value(t)**2, 0, self.duration)[0]                         # no dimension

        self.B1peak: float = radians(self.flipAngle) / (self.gyromagneticFactor * self.amplitudeIntegral * self.duration)     # T
        self.B1: Callable = lambda t: self.value(t) * self.B1peak                                                               # T

        self.omega: Callable = lambda t: self.gyromagneticFactor * self.B1(t)                                                   # rad / s
        self.omegaSquared: Callable = lambda t: self.omega(t)**2                                                                # (rad / s)^2
        self.omegaRMS: float = sqrt(invDuration * quad(self.omegaSquared, 0, self.duration)[0])                                 # rad / s

    def value():
        raise RuntimeError("Pulse.value should not be called directly. User daughter class' `value` method instead.")


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

    def value(self, t : float) -> float:
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

        if (t < 0) or (t > self.duration):
            return 0

        dimless_time = t / self.duration

        if (0 <= dimless_time) & (dimless_time < .5 * self.shape):
            pulse = 0.5 * ( 1 + cos(pi * (-1 + 2 * dimless_time / self.shape)) )

        elif (.5 * self.shape <= dimless_time) & (dimless_time < 1 - .5 * self.shape):
            pulse = 1

        elif (1 - .5 * self.shape <= dimless_time) & (dimless_time <= 1):
            pulse = 0.5 * ( 1 + cos(pi * (1 - 2 / self.shape + 2 * dimless_time / self.shape)) )

        return pulse

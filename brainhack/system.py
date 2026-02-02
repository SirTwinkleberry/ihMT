from .pulses import Pulse

from typing import Callable
from numpy import ndarray, array, diag, fliplr, zeros, kron, eye, pi, sqrt, exp, sin, cos
from scipy.integrate import quad
from scipy.linalg import block_diag


class System():
    poolFree_Rrf: ndarray
    poolFree_M0: float
    poolFree_T1: float
    poolFree_T2: float

    poolFreeBound_exchangeRate: float

    poolBound_Rrf_singleSat_Positive: ndarray
    poolBound_Rrf_singleSat_Negative: ndarray
    poolBound_Rrf_dualSat: ndarray
    poolBound_M0: float
    poolBound_T1: float
    poolBound_T2: float
    poolBound_T1D: float

    N_pools: int

    def __init__(self, M0a: float, T1f: float, T2f: float, R: float, M0b: float, T1b: float, T2b: float, T1D: float):
        """_summary_

        Parameters
        ----------
        M0a : float
            _description_
        T1f : float
            _description_
        T2f : float
            _description_
        R : float
            _description_
        M0b : float
            _description_
        T1b : float
            _description_
        T2b : float
            _description_
        T1D : float
            _description_
        """
        self.poolFree_M0 = M0a
        self.poolFree_T1 = T1f
        self.poolFree_T2 = T2f

        self.poolFreeBound_exchangeRate = R

        self.poolBound_M0 = M0b
        self.poolBound_T1 = T1b
        self.poolBound_T2 = T2b
        self.poolBound_T1D = T1D
        self.poolBound_omegaLocField = 1. / ( sqrt(15) * T2b )

        self.N_pools = len(array(self.poolFree_T2).flatten()) + len(array(self.poolBound_T2).flatten())

    def RFabsorption_Matrix(self, pulse: Pulse):
        """_summary_

        Parameters
        ----------
        pulse : Pulse
            _description_
        """
        inv_omegaLocField = 1. / self.poolBound_omegaLocField
        angularFrequencyOffset = 2 * pi * pulse.offset

        self.poolFree_Rrf: ndarray = diag( [ -pi * pulse.omegaRMS**2 * self.Lorentzian(pulse, self.poolFree_T2), *zeros(2 * (self.N_pools - 1)) ] )

        superLorentzian: Callable = self.SuperLorentzian if abs(pulse.offset) > 1000 else self.PampelSuperLorentzian
        poolBound_Rrf: float = pi * pulse.omegaRMS**2 * superLorentzian(pulse, self.poolBound_T2)
        tmp_diag: ndarray = diag( [ -poolBound_Rrf, -poolBound_Rrf * (angularFrequencyOffset * inv_omegaLocField)**2 ] )
        tmp_anti: ndarray = fliplr( diag( [ poolBound_Rrf * angularFrequencyOffset, poolBound_Rrf * angularFrequencyOffset * inv_omegaLocField**2 ] ) )

        self.poolBound_Rrf_dualSat: ndarray = block_diag( 0, kron( eye(self.N_pools - 1), tmp_diag ) )
        self.poolBound_Rrf_singleSat_Positive: ndarray = block_diag( 0, kron( eye(self.N_pools - 1), tmp_diag + tmp_anti ) )
        self.poolBound_Rrf_singleSat_Negative: ndarray = block_diag( 0, kron( eye(self.N_pools - 1), tmp_diag - tmp_anti ) )

    def Lorentzian(self, pulse: Pulse, T2: float) -> float:
        """_summary_

        Parameters
        ----------
        pulse : Pulse
            _description_
        T2 : float
            _description_

        Returns
        -------
        float
            _description_
        """
        return (T2 / pi) / ( 1 + (2 * pi * pulse.offset * T2)**2 )

    def Gaussian(self, pulse: Pulse, T2: float) -> float:
        """_summary_

        Parameters
        ----------
        pulse : Pulse
            _description_
        T2 : float
            _description_

        Returns
        -------
        float
            _description_
        """
        return sqrt(1. / (2 * pi) ) * self.T2 * exp( -.5 * (2 * pi * pulse.offset * T2)**2 )

    def SuperLorentzian(self, pulse: Pulse, T2: float) -> float:
        """_summary_

        Parameters
        ----------
        pulse : Pulse
            _description_
        T2 : float
            _description_

        Returns
        -------
        float
            _description_
        """
        return quad(lambda u: sqrt(2 / pi) * (T2 / abs(3 * u * u - 1)) * exp(-2 * ((2 * pi * pulse.offset * T2) / (3 * u * u - 1))**2), 0, 1)[0]

    def PampelSuperLorentzian(self, pulse: Pulse, T2: float) -> float:
        """_summary_

        Parameters
        ----------
        pulse : Pulse
            _description_
        T2 : float
            _description_

        Returns
        -------
        float
            _description_
        """
        def Spherical(theta: float, offset: float, T2: float) -> float:
            # This program set up a function for Spherical lineshape integration
            # include neighboors contribution to remove singularity at the magic angle
            # see Pampel et al. NeuroImage 114 (2015) 136–146
            T2_neighboors = 1. / 31.4  # 10000000 would mean virtually no effect of T2_neighboors
            T2_tmp = 2 * T2 / abs(3 * cos(theta)**2 - 1)
            T2_eff = 1. / sqrt(1. / (T2_tmp * T2_tmp) + 1. / (T2_neighboors * T2_neighboors))

            return sin(theta) * T2_eff * exp( -.5 * ( 2 * pi * offset * T2_eff )**2 )

        return sqrt(1. / (2 * pi)) * quad( lambda theta: Spherical(theta, pulse.offset, T2), 0, .5 * pi)

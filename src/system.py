from typing import Callable
from pulses import Pulse
from numpy import ndarray, array, empty, diag, fliplr, zeros, kron, eye, pi, sqrt, exp, sin, cos
from scipy.integrate import quad
from scipy.linalg import block_diag


class System():
    poolFree_exchanges: ndarray = empty()
    poolFree_M0: float = 0.
    poolFree_T1: float = 0.
    poolFree_T2: float = 0.

    poolFreeBound_exchangeRate: float = 0.

    poolBound_exchanges_singleSat_Positive: ndarray = empty()
    poolBound_exchanges_singleSat_Negative: ndarray = empty()
    poolBound_exchanges_dualSat: ndarray = empty()
    poolBound_M0: float = 0.
    poolBound_T1: float = 0.
    poolBound_T2: float = 0.
    poolBound_T1D: float = 0.

    N_compartments: int = 0

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
        self.poolBound_formFactor = 1. / ( sqrt(15) * T2b )

        self.N_compartments = len(array(self.poolFree_T2).flatten()) + len(array(self.poolBound_T2).flatten())

    def Exchanges(self, pulse: Pulse):
        """_summary_

        Parameters
        ----------
        pulse : Pulse
            _description_
        """
        invFormFactor = 1. / self.poolBound_formFactor
        angularFrequencyOffset = 2 * pi * pulse.offset

        self.poolFree_exchanges: ndarray = diag( [ -pi * pulse.omegaRMS**2 * self.Lorentzian(pulse, self.poolFree_T2), zeros(2 * self.N_compartments) ] )

        superLorentzian: Callable = self.SuperLorentzian if abs(pulse.offset) > 1000 else self.PampelSuperLorentzian
        omega: float = superLorentzian(pulse, self.poolBound_T2)
        tmp_diag: ndarray = diag( [ -omega, -omega * (angularFrequencyOffset * invFormFactor)**2 ] )
        tmp_anti: ndarray = fliplr( diag( [ angularFrequencyOffset, angularFrequencyOffset * invFormFactor**2 ] ) )

        self.poolBound_exchanges_dualSat: ndarray = block_diag( 0, kron( eye(self.N_compartments), tmp_diag ) )
        self.poolBound_exchanges_singleSat_Positive: ndarray = block_diag( 0, kron( tmp_diag + tmp_anti ) )
        self.poolBound_exchanges_singleSat_Negative: ndarray = block_diag( 0, kron( tmp_diag - tmp_anti ) )

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
        func = lambda u: sqrt(2 / pi) * (T2 / abs(3 * u * u - 1)) * exp(-2 * ((2 * pi * pulse.offset * T2) / (3 * u * u - 1))**2)
        return quad(func, 0, 1)[0]
        
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
            T2_neighboors = 1. / 31.4;                                                          # 10000000 would mean virtually no effect of T2_neighboors
            T2_tmp = 2 * T2 / abs(3 * cos(theta)**2 - 1)
            T2_eff = 1. / sqrt(1. / (T2_tmp * T2_tmp) + 1. / (T2_neighboors * T2_neighboors))

            return sin(theta) * T2_eff * exp( -.5 * ( 2 * pi * offset * T2_eff )**2 )

        return sqrt(1. / (2 * pi)) * quad( lambda theta: Spherical(theta, pulse.offset, T2), 0, .5 * pi)

from brainhack.pulse import Pulse

from collections.abc import Callable
from numpy import float64, array, diag, fliplr, zeros, kron, eye, pi, sqrt, exp, sin, cos
from numpy.typing import NDArray
from scipy.integrate import quad  # type: ignore
from scipy.linalg import block_diag  # type: ignore


class System():
    poolFree_Rrf: NDArray[float64]
    poolFree_M0: float
    poolFree_T1: float
    poolFree_T2: float

    poolFreeBound_exchangeRate: float

    poolBound_Rrf_singleSat_Positive: NDArray[float64]
    poolBound_Rrf_singleSat_Negative: NDArray[float64]
    poolBound_Rrf_dualSat: NDArray[float64]
    poolBound_M0: float
    poolBound_T1: float
    poolBound_T2: float
    poolBound_T1D: float
    poolBound_omegaLocField: float

    N_pools: int

    def __init__(self, poolFree_M0: float, poolFree_T1: float, poolFree_T2: float, poolFreeBound_exchangeRate: float, poolBound_M0: float, poolBound_T1: float, poolBound_T2: float, poolBound_T1D: float):
        """_summary_

        Parameters
        ----------
        poolFree_M0 : float
            _description_
        poolFree_T1 : float
            _description_
        poolFree_T2 : float
            _description_
        poolFreeBound_exchangeRate : float
            _description_
        poolBound_M0 : float
            _description_
        poolBound_T1 : float
            _description_
        poolBound_T2 : float
            _description_
        poolBound_T1D : float
            _description_
        """
        self.poolFree_M0 = poolFree_M0
        self.poolFree_T1 = poolFree_T1
        self.poolFree_T2 = poolFree_T2

        self.poolFreeBound_exchangeRate = poolFreeBound_exchangeRate

        self.poolBound_M0 = poolBound_M0
        self.poolBound_T1 = poolBound_T1
        self.poolBound_T2 = poolBound_T2
        self.poolBound_T1D = poolBound_T1D
        self.poolBound_omegaLocField = 1. / ( sqrt(15) * poolBound_T2 )

        self.N_pools = len(array(poolFree_T2).flatten()) + len(array(poolBound_T2).flatten())

    def RFabsorption_Matrix(self, pulse: Pulse):
        """_summary_

        Parameters
        ----------
        pulse : Pulse
            _description_
        """
        inv_omegaLocField = 1. / self.poolBound_omegaLocField
        angularFrequencyOffset = 2 * pi * pulse.offset

        self.poolFree_Rrf = diag( [ -pi * pulse.omegaRMS**2 * self.Lorentzian(pulse, self.poolFree_T2), *zeros(2 * (self.N_pools - 1)) ] )

        superLorentzian: Callable[[Pulse, float], float] = self.SuperLorentzian if abs(pulse.offset) > 1000 else self.PampelSuperLorentzian
        poolBound_Rrf: float = pi * pulse.omegaRMS**2 * superLorentzian(pulse, self.poolBound_T2)
        tmp_diag: NDArray[float64] = diag( [ -poolBound_Rrf, -poolBound_Rrf * (angularFrequencyOffset * inv_omegaLocField)**2 ] )
        tmp_anti: NDArray[float64] = fliplr( diag( [ poolBound_Rrf * angularFrequencyOffset, poolBound_Rrf * angularFrequencyOffset * inv_omegaLocField**2 ] ) )

        self.poolBound_Rrf_dualSat = block_diag( 0, kron( eye(self.N_pools - 1), tmp_diag ) )
        self.poolBound_Rrf_singleSat_Positive = block_diag( 0, kron( eye(self.N_pools - 1), tmp_diag + tmp_anti ) )
        self.poolBound_Rrf_singleSat_Negative = block_diag( 0, kron( eye(self.N_pools - 1), tmp_diag - tmp_anti ) )

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
        return sqrt(1. / (2 * pi) ) * T2 * exp( -.5 * (2 * pi * pulse.offset * T2)**2 )

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
        return quad(lambda u: sqrt(2 / pi) * (T2 / abs(3 * u * u - 1)) * exp(-2 * ((2 * pi * pulse.offset * T2) / (3 * u * u - 1))**2), 0, 1)[0]  # type: ignore

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

        return sqrt(1. / (2 * pi)) * quad( lambda theta: Spherical(theta, pulse.offset, T2), 0, .5 * pi)[0]  # type: ignore

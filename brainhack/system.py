from logging import getLogger, NullHandler
from typing import Any
from collections.abc import Callable
from numpy import float64, array, diag, fliplr, zeros, kron, eye, pi, sqrt, exp, sin, cos, sum, dot, deg2rad
from numpy.typing import NDArray
from scipy.integrate import quad, dblquad
from scipy.linalg import block_diag
from scipy.special import i0

from brainhack.pulse import Pulse

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug('`system` module loaded successfully')


class System():
    _pulse: Pulse

    _poolFree_Rrf: NDArray[float64]
    _poolFree_M0: float
    _poolFree_T1: float
    _poolFree_T2: float

    _poolFreeBound_exchangeRate: float

    _poolBound_Rrf_singleSat_Positive: NDArray[float64]
    _poolBound_Rrf_singleSat_Negative: NDArray[float64]
    _poolBound_Rrf_dualSat: NDArray[float64]
    _poolBound_M0: float
    _poolBound_T1: float
    _poolBound_T2: float
    _poolBound_T1D: float
    _poolBound_omegaLocalField: float

    _N_pools: int

    def __init__(self, pulse: Pulse, poolFree_M0: float, poolFree_T1: float, poolFree_T2: float, poolFreeBound_exchangeRate: float, poolBound_M0: float, poolBound_T1: float, poolBound_T2: float, poolBound_T1D: float, *args: Any, **kwargs: Any):
        """_summary_

        Parameters
        ----------
        pulse : Pulse
            _description_
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
        self.pulse = pulse

        self.poolFree_M0 = poolFree_M0
        self.poolFree_T1 = poolFree_T1
        self.poolFree_T2 = poolFree_T2

        self.poolFreeBound_exchangeRate = poolFreeBound_exchangeRate

        self.poolBound_M0 = poolBound_M0
        self.poolBound_T1 = poolBound_T1
        self.poolBound_T2 = poolBound_T2
        self.poolBound_T1D = poolBound_T1D

    def compute_poolBound_RFabsorptionMatrices(self):
        """_summary_
        """
        inv_omegaLocalField = 1. / self.poolBound_omegaLocalField
        angularFrequencyOffset = 2 * pi * self.pulse.offset

        superLorentzian: Callable[[Pulse, float], float] = self.SuperLorentzian if abs(self.pulse.offset) > 1000 else self.PampelSuperLorentzian
        poolBound_Rrf: float = pi * self.pulse.omegaRMS**2 * superLorentzian(self.poolBound_T2)
        tmp_diag: NDArray[float64] = diag( [ -poolBound_Rrf, -poolBound_Rrf * (angularFrequencyOffset * inv_omegaLocalField)**2 ] )
        tmp_anti: NDArray[float64] = fliplr( diag( [ poolBound_Rrf * angularFrequencyOffset, poolBound_Rrf * angularFrequencyOffset * inv_omegaLocalField**2 ] ) )

        self.poolBound_Rrf_dualSat = block_diag( 0, kron( eye(self.N_pools - 1), tmp_diag ) )
        self.poolBound_Rrf_singleSat_Positive = block_diag( 0, kron( eye(self.N_pools - 1), tmp_diag + tmp_anti ) )
        self.poolBound_Rrf_singleSat_Negative = block_diag( 0, kron( eye(self.N_pools - 1), tmp_diag - tmp_anti ) )

    def resetComputedAttributes_poolBound_RFabsorptionMatrices(self):
        if hasattr(self, '_poolBound_Rrf_dualSat'): del self._poolBound_Rrf_dualSat  # noqa: E701
        if hasattr(self, '_poolBound_Rrf_singleSat_Positive'): del self._poolBound_Rrf_singleSat_Positive  # noqa: E701
        if hasattr(self, '_poolBound_Rrf_singleSat_Negative'): del self._poolBound_Rrf_singleSat_Negative  # noqa: E701

    def resetComputedAttributes_poolFree_Rrf(self):
        if hasattr(self, '_poolFree_Rrf'): del self._poolFree_Rrf  # noqa: E701

    def resetComputedAttributes_poolBound_omegaLocalField(self):
        if hasattr(self, '_poolBound_omegaLocalField'): del self._poolBound_omegaLocalField  # noqa: E701

    def resetComputedAttributes_N_pools(self):
        if hasattr(self, '_N_pools'): del self._N_pools  # noqa: E701

    def Lorentzian(self, T2: float) -> float:
        """_summary_

        Parameters
        ----------
        T2 : float
            _description_

        Returns
        -------
        float
            _description_
        """
        return (T2 / pi) / ( 1 + (2 * pi * self.pulse.offset * T2)**2 )

    def Gaussian(self, T2: float) -> float:
        """_summary_

        Parameters
        ----------
        T2 : float
            _description_

        Returns
        -------
        float
            _description_
        """
        return sqrt(1. / (2 * pi) ) * T2 * exp( -.5 * (2 * pi * self.pulse.offset * T2)**2 )

    def SuperLorentzian(self, T2: float) -> float:
        """_summary_

        Parameters
        ----------
        T2 : float
            _description_

        Returns
        -------
        float
            _description_
        """
        return quad(lambda u: sqrt(2 / pi) * (T2 / abs(3 * u * u - 1)) * exp(-2 * ((2 * pi * self.pulse.offset * T2) / (3 * u * u - 1))**2), 0, 1)[0]

    def PampelSuperLorentzian(self, T2: float) -> float:
        """_summary_

        Parameters
        ----------
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
        return sqrt(1. / (2 * pi)) * quad( lambda theta: Spherical(theta, self.pulse.offset, T2), 0, .5 * pi)[0]

    def Cylindrical(self, T2: float) -> float:
        """_summary_

        Parameters
        ----------
        T2 : float
            _description_

        Returns
        -------
        float
            _description_
        """
        if self.axonal_angle == 0:
            T2_totSquare = 1 / (31.4 * 31.4 + .25 / (T2 * T2))
            return sqrt(2 * pi * T2_totSquare) * exp(-2 * (pi * self.pulse.offset)**2 * T2_totSquare)

        def Spherical(theta: float, phi: float, offset: float, T2: float) -> float:
            # include neighboors contribution to remove singularity at the magic angle, see Pampel et al. NeuroImage 114 (2015) 136–146
            # R2_neighboors 31.4
            T2_totSquare = 1 / (31.4 * 31.4 + (abs(3 * (-sin(theta) * cos(phi))**2 - 1) / (2 * T2))**2)
            return sqrt(T2_totSquare) * exp( -2 * (pi * offset)**2 * T2_totSquare )
        return sqrt(2 / pi) * quad( lambda phi: Spherical(deg2rad(self.axonal_angle), phi, self.pulse.offset, T2), 0, pi, limit=100)[0]

    def DispersedCylindrical(self, T2: float) -> float:
        """Fiber bundle orientation distribution lineshape

        Parameters
        ----------
        T2 : float
            _description_

        Returns
        -------
        float
            _description_
        """
        raise NotImplementedError("Currently not implemented.")
        theta = np.deg2rad(theta)
        
        def ScaledBingham(theta: float, phi: float) -> float:
            u: NDArray = array([sin(theta) * cos(phi), sin(theta) * sin(phi), cos(theta)])
            values = list()
            for fiber in self.fibers:
                f0: float = fiber.maxAngularFiberDensity
                k: NDArray = fiber.concentrationParameters
                m: NDArray = fiber.concentrationAxes
                mat: NDArray = dot(m, dot(diag(k), m.transpose()))
                norm: float = (f0 * 2 * pi * i0(.5 * (k[0] - k[1])) * exp(.5 * (k[0] + k[1])))**2
                values.append(norm * exp(dot(u, dot(mat, u))))
            return tuple(values)

        def Spherical(theta: float, phi: float, offset: float, T2: float) -> float:
            # This program set up a function for Spherical lineshape integration
            # include neighboors contribution to remove singularity at the magic angle
            # see Pampel et al. NeuroImage 114 (2015) 136–146
            R2_neighboors = 31.4  # 10000000 would mean virtually no effect of T2_neighboors
            R2_tmp = abs(3 * (-sin(theta) * cos(phi))**2 - 1) / (2 * T2)
            T2_totSquare = 1 / (R2_neighboors * R2_neighboors + R2_tmp * R2_tmp)
            return sqrt(T2_totSquare) * exp( -.5 * ( 2 * pi * offset * T2_totSquare )**2 )

        norm = 1. / len(self.fibers)
        return norm * sqrt(1. / (2 * pi)**3) * dblquad(lambda theta, phi: sin(theta) * Spherical(theta, phi, self.pulse.offset, T2) * sum(ScaledBingham(theta, phi)), 0, pi, 0, 2 * pi)[0]

    #####
    # BELOW: property getters and setters
    #####
    @property
    def pulse(self):
        return self._pulse

    @pulse.setter
    def pulse(self, val: Pulse):
        offset = None
        omegaRMS = None
        if hasattr(self, '_pulse'):
            offset = self._pulse.offset
            omegaRMS = self._pulse.omegaRMS

        self._pulse = val
        self._pulse.onChange('omegaRMS', [self.resetComputedAttributes_poolFree_Rrf, self.resetComputedAttributes_poolBound_RFabsorptionMatrices])
        self._pulse.onChange('offset', [self.resetComputedAttributes_poolBound_RFabsorptionMatrices])

        if (omegaRMS is not None) and (self._pulse.omegaRMS != omegaRMS):
            self.resetComputedAttributes_poolFree_Rrf()
            self.resetComputedAttributes_poolBound_RFabsorptionMatrices()
        elif (offset is not None) and (self._pulse.offset != offset):
            self.resetComputedAttributes_poolBound_RFabsorptionMatrices()

    @property
    def poolFree_Rrf(self):
        if not hasattr(self, '_poolFree_Rrf'):
            self.poolFree_Rrf = diag( [ -pi * self.pulse.omegaRMS**2 * self.Lorentzian(self.poolFree_T2), *zeros(2 * (self.N_pools - 1)) ] )
        return self._poolFree_Rrf

    @poolFree_Rrf.setter
    def poolFree_Rrf(self, val: NDArray[float64]):
        self._poolFree_Rrf = val

    @poolFree_Rrf.deleter
    def poolFree_Rrf(self):
        del self._poolFree_Rrf

    @property
    def poolFree_M0(self):
        return self._poolFree_M0

    @poolFree_M0.setter
    def poolFree_M0(self, val: float):
        self._poolFree_M0 = val

    @property
    def poolFree_T1(self):
        return self._poolFree_T1

    @poolFree_T1.setter
    def poolFree_T1(self, val: float):
        self._poolFree_T1 = val
        self.resetComputedAttributes_N_pools()

    @property
    def poolFree_T2(self):
        return self._poolFree_T2

    @poolFree_T2.setter
    def poolFree_T2(self, val: float):
        self._poolFree_T2 = val
        self.resetComputedAttributes_N_pools()
        self.resetComputedAttributes_poolFree_Rrf()

    @property
    def poolFreeBound_exchangeRate(self):
        return self._poolFreeBound_exchangeRate

    @poolFreeBound_exchangeRate.setter
    def poolFreeBound_exchangeRate(self, val: float):
        self._poolFreeBound_exchangeRate = val

    @property
    def poolBound_Rrf_singleSat_Positive(self):
        if not hasattr(self, '_poolBound_Rrf_singleSat_Positive'):
            self.compute_poolBound_RFabsorptionMatrices()
        return self._poolBound_Rrf_singleSat_Positive

    @poolBound_Rrf_singleSat_Positive.setter
    def poolBound_Rrf_singleSat_Positive(self, val: NDArray[float64]):
        self._poolBound_Rrf_singleSat_Positive = val

    @poolBound_Rrf_singleSat_Positive.deleter
    def poolBound_Rrf_singleSat_Positive(self):
        del self._poolBound_Rrf_singleSat_Positive

    @property
    def poolBound_Rrf_singleSat_Negative(self):
        if not hasattr(self, '_poolBound_Rrf_singleSat_Negative'):
            self.compute_poolBound_RFabsorptionMatrices()
        return self._poolBound_Rrf_singleSat_Negative

    @poolBound_Rrf_singleSat_Negative.setter
    def poolBound_Rrf_singleSat_Negative(self, val: NDArray[float64]):
        self._poolBound_Rrf_singleSat_Negative = val

    @poolBound_Rrf_singleSat_Negative.deleter
    def poolBound_Rrf_singleSat_Negative(self):
        del self._poolBound_Rrf_singleSat_Negative

    @property
    def poolBound_Rrf_dualSat(self):
        if not hasattr(self, '_poolBound_Rrf_dualSat'):
            self.compute_poolBound_RFabsorptionMatrices()
        return self._poolBound_Rrf_dualSat

    @poolBound_Rrf_dualSat.setter
    def poolBound_Rrf_dualSat(self, val: NDArray[float64]):
        self._poolBound_Rrf_dualSat = val

    @poolBound_Rrf_dualSat.deleter
    def poolBound_Rrf_dualSat(self):
        del self._poolBound_Rrf_dualSat

    @property
    def poolBound_M0(self):
        return self._poolBound_M0

    @poolBound_M0.setter
    def poolBound_M0(self, val: float):
        self._poolBound_M0 = val

    @property
    def poolBound_T1(self):
        return self._poolBound_T1

    @poolBound_T1.setter
    def poolBound_T1(self, val: float):
        self._poolBound_T1 = val

    @property
    def poolBound_T2(self):
        return self._poolBound_T2

    @poolBound_T2.setter
    def poolBound_T2(self, val: float):
        self._poolBound_T2 = val
        self.resetComputedAttributes_N_pools()
        self.resetComputedAttributes_poolBound_omegaLocalField()
        self.resetComputedAttributes_poolBound_RFabsorptionMatrices()

    @property
    def poolBound_T1D(self):
        return self._poolBound_T1D

    @poolBound_T1D.setter
    def poolBound_T1D(self, val: float):
        self._poolBound_T1D = val

    @property
    def poolBound_omegaLocalField(self):
        if not hasattr(self, '_poolBound_omegaLocalField'):
            self._poolBound_omegaLocalField = 1. / ( sqrt(15) * self.poolBound_T2 )
        return self._poolBound_omegaLocalField

    @poolBound_omegaLocalField.setter
    def poolBound_omegaLocalField(self, val: float):
        self._poolBound_omegaLocalField = val
        self.resetComputedAttributes_poolBound_RFabsorptionMatrices()

    @poolBound_omegaLocalField.deleter
    def poolBound_omegaLocalField(self):
        del self._poolBound_omegaLocalField

    @property
    def N_pools(self):
        if not hasattr(self, '_N_pools'):
            if (len1 := len(array(self.poolFree_T1).flatten())) != (len2 := len(array(self.poolFree_T2).flatten())):
                error = f'Could not compute `N_pools` as `poolFree_T1` ({array(self.poolFree_T1).flatten().tolist()}) and `poolFree_T2` ({array(self.poolFree_T2).flatten().tolist()}) arrays do not have the same length ({len1} vs {len2})'
                logger.critical(error)
                raise RuntimeError(error)
            if (len1 := len(array(self.poolBound_T1).flatten())) != (len2 := len(array(self.poolBound_T2).flatten())):
                error = f'Could not compute `N_pools` as `poolBound_T1` ({array(self.poolBound_T1).flatten().tolist()}) and `poolBound_T2` ({array(self.poolBound_T2).flatten().tolist()}) arrays do not have the same length ({len1} vs {len2})'
                logger.critical(error)
                raise RuntimeError(error)
            if (len1 := len(array(self.poolBound_T1).flatten())) != (len2 := len(array(self.poolBound_T1D).flatten())):
                error = f'Could not compute `N_pools` as `poolBound_T1` ({array(self.poolBound_T1).flatten().tolist()}) and `poolBound_T1D` ({array(self.poolBound_T1D).flatten().tolist()}) arrays do not have the same length ({len1} vs {len2})'
                logger.critical(error)
                raise RuntimeError(error)

            self.N_pools = len(array(self.poolFree_T2).flatten()) + len(array(self.poolBound_T2).flatten())
        return self._N_pools

    @N_pools.setter
    def N_pools(self, val: int):
        self._N_pools = val
        self.resetComputedAttributes_poolFree_Rrf()
        self.resetComputedAttributes_poolBound_RFabsorptionMatrices()

    @N_pools.deleter
    def N_pools(self):
        del self._N_pools

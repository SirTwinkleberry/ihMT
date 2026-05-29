from logging import getLogger, NullHandler
from numpy import float64, array, diag, fliplr, zeros, kron, eye, pi, sqrt, exp, sin, cos, sum, dot, deg2rad
from numpy.typing import NDArray
from scipy.integrate import quad, dblquad
from scipy.linalg import block_diag
from scipy.special import i0
from typing import Any
from collections.abc import Callable
from operator import lt

from brainhack.meta import _Event, check_value_is_valid
from brainhack.pulse import Pulse

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug('`system` module loaded successfully')


_sqrt15 = sqrt(15)


class System(_Event):
    _pulse: Pulse

    _poolFree_Rrf: NDArray[float64]
    _poolFree_M0: float
    _poolFree_T1: float
    _poolFree_T2: float

    _poolFreeBound_exchangeRate: float

    _poolBound_Rrf_singleSat_Positive: NDArray[float64]
    _poolBound_Rrf_singleSat_Negative: NDArray[float64]
    _poolBound_Rrf_dualSat: NDArray[float64]
    _poolBound_lineshapeAsymmetry: float
    _poolBound_M0: float
    _poolBound_T1: float
    _poolBound_T2: float
    _poolBound_T1D: float
    _poolBound_omegaLocalField: float

    _N_pools: int

    _classAttributes: tuple[str] = ('pulse', 'poolFree_Rrf', 'poolFree_M0', 'poolFree_T1', 'poolFree_T2', 'poolFreeBound_exchangeRate', 'poolBound_Rrf_singleSat_Positive', 'poolBound_Rrf_singleSat_Negative', 'poolBound_Rrf_dualSat', 'poolBound_lineshapeAsymmetry', 'poolBound_M0', 'poolBound_T1', 'poolBound_T2', 'poolBound_T1D', 'poolBound_omegaLocalField', 'N_pools')

    def __init__(self, pulse: Pulse, poolFree_M0: float, poolFree_T1: float, poolFree_T2: float, poolFreeBound_exchangeRate: float, poolBound_M0: float, poolBound_T1: float, poolBound_T2: float, poolBound_T1D: float, poolBound_lineshapeAsymmetry: float, *args: Any, **kwargs: Any):
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
        self.poolBound_lineshapeAsymmetry = poolBound_lineshapeAsymmetry

        self.onChange('pulse', [lambda: self._reset_computed_attributes(['poolFree_Rrf', 'poolBound_Rrf_dualSat', 'poolBound_Rrf_singleSat_Positive', 'poolBound_Rrf_singleSat_Negative'])])
        self.onChange('N_pools', [lambda: self._reset_computed_attributes(['poolFree_Rrf', 'poolBound_Rrf_dualSat', 'poolBound_Rrf_singleSat_Positive', 'poolBound_Rrf_singleSat_Negative'])])
        self.onChange('poolFree_T1', [lambda: self._reset_computed_attributes(['N_pools'])])
        self.onChange('poolFree_T2', [lambda: self._reset_computed_attributes(['N_pools', 'poolFree_Rrf'])])
        self.onChange('poolBound_T1', [lambda: self._reset_computed_attributes(['N_pools'])])
        self.onChange('poolBound_T2', [lambda: self._reset_computed_attributes(['N_pools', 'poolBound_Rrf_dualSat', 'poolBound_Rrf_singleSat_Positive', 'poolBound_Rrf_singleSat_Negative', 'poolBound_omegaLocalField'])])
        self.onChange('poolBound_omegaLocalField', [lambda: self._reset_computed_attributes(['poolBound_Rrf_dualSat', 'poolBound_Rrf_singleSat_Positive', 'poolBound_Rrf_singleSat_Negative'])])
        self.onChange('poolBound_lineshapeAsymmetry', [lambda: self._reset_computed_attributes(['poolBound_Rrf_singleSat_Positive', 'poolBound_Rrf_singleSat_Negative'])])

    def copy(self) -> System:
        return System(self.pulse.copy(), self.poolFree_M0, self.poolFree_T1, self.poolFree_T2, self.poolFreeBound_exchangeRate, self.poolBound_M0, self.poolBound_T1, self.poolBound_T2, self.poolBound_T1D, self.poolBound_lineshapeAsymmetry)

    def _compute_poolBound_RFabsorptionMatrices(self):
        """_summary_
        """
        inv_omegaLocalField = 1. / self.poolBound_omegaLocalField
        angularFrequencyOffset = 2 * pi * self.pulse.offset
        norm_A = self.pulse.omegaRMS * self.pulse.omegaRMS
        norm_B = angularFrequencyOffset * inv_omegaLocalField

        superLorentzian: Callable[[Pulse, float], float] = self.PampelSuperLorentzian
        # superLorentzian: Callable[[Pulse, float], float] = self.SuperLorentzian if abs(self.pulse.offset) > 1000 else self.PampelSuperLorentzian

        if self.poolBound_lineshapeAsymmetry != 0:
            poolBound_Rrf_Positive: float = .5 * norm_A * superLorentzian(self.poolBound_T2, self.pulse.offset - self.poolBound_lineshapeAsymmetry)
            poolBound_Rrf_Negative: float = .5 * norm_A * superLorentzian(self.poolBound_T2, -self.pulse.offset - self.poolBound_lineshapeAsymmetry)
        else:
            poolBound_Rrf_Positive: float = .5 * norm_A * superLorentzian(self.poolBound_T2, self.pulse.offset)
            poolBound_Rrf_Negative: float = poolBound_Rrf_Positive

        tmp_diag: NDArray[float64] = diag( [ 1, norm_B * norm_B] )
        tmp_anti: NDArray[float64] = fliplr( diag( [ angularFrequencyOffset, norm_B * inv_omegaLocalField ] ) )

        tmp_diag_Positive: NDArray[float64] = -poolBound_Rrf_Positive * tmp_diag
        tmp_anti_Positive: NDArray[float64] =  poolBound_Rrf_Positive * tmp_anti

        tmp_diag_Negative: NDArray[float64] = -poolBound_Rrf_Negative * tmp_diag
        tmp_anti_Negative: NDArray[float64] = -poolBound_Rrf_Negative * tmp_anti

        self.poolBound_Rrf_dualSat = block_diag( 0, kron( eye(self.N_pools - 1), .5 * (tmp_diag_Positive + tmp_diag_Negative) ) )
        self.poolBound_Rrf_singleSat_Positive = block_diag( 0, kron( eye(self.N_pools - 1), tmp_diag_Positive + tmp_anti_Positive ) )
        self.poolBound_Rrf_singleSat_Negative = block_diag( 0, kron( eye(self.N_pools - 1), tmp_diag_Negative + tmp_anti_Negative ) )

    def Lorentzian(self, T2: float, offset: float, *args: Any, **kwargs: Any) -> float:
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
        return 2 * T2 / ( 1 + 4 * pi * pi * offset * offset * T2 * T2)

    def Gaussian(self, T2: float, offset: float, *args: Any, **kwargs: Any) -> float:
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
        return sqrt(2 * pi) * T2 * exp( -2 * pi * pi * offset * offset * T2 * T2 )

    def SuperLorentzian(self, T2: float, offset: float, *args: Any, **kwargs: Any) -> float:
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
        angular_offset_square = 4 * pi * pi * offset * offset
        reduced_R2_square = .25 / (T2 * T2)
        return sqrt( 2 * pi ) * quad(lambda cos_theta: self._Spherical(cos_theta, angular_offset_square, reduced_R2_square, 0), 0, 1)[0]

    def PampelSuperLorentzian(self, T2: float, offset: float, *args: Any, **kwargs: Any) -> float:
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
        angular_offset_square = 4 * pi * pi * offset * offset
        reduced_R2_square = .25 / (T2 * T2)
        return sqrt( 2 * pi ) * quad( lambda cos_theta: self._Spherical(cos_theta, angular_offset_square, reduced_R2_square, 985.96), 0, 1)[0]

    def Cylindrical(self, T2: float, offset: float, *args: Any, **kwargs: Any) -> float:
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
        angular_offset_square = 4 * pi * pi * offset * offset
        reduced_R2_square = .25 / (T2 * T2)

        if self.axonal_angle == 0:
            T2_totSquare = 1 / (985.96 + reduced_R2_square)
            return sqrt(2 * pi * T2_totSquare) * exp(-.5 * angular_offset_square * T2_totSquare)

        sin_theta = -sin(deg2rad(self.axonal_angle))
        return sqrt( 2 / pi ) * quad( lambda cos_phi: self._Spherical(sin_theta * cos_phi, angular_offset_square, reduced_R2_square, 985.96), -1, 1, limit=100)[0]

    def DispersedCylindrical(self, T2: float, offset: float, *args: Any, **kwargs: Any) -> float:
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

    @staticmethod
    def _Spherical(u: float, angular_offset_square: float, reduced_R2_square: float, R2_neighbors_square: float) -> float:
        # include neighboors contribution to remove singularity at the magic angle, see Pampel et al. NeuroImage 114 (2015) 136–146
        # Reduced R2 square = .25 * R2 * R2
        # angular offset = 2 * pi * offset frequency
        # u = -sin(theta) * cos(phi_A)  or, simpler, u = cos(theta_n)
        T2_total_square = 1 / (R2_neighbors_square + reduced_R2_square * (3 * u * u - 1) * (3 * u * u - 1))
        return sqrt(T2_total_square) * exp( -.5 * angular_offset_square * T2_total_square )

    #####
    # BELOW: property getters and setters
    #####
    @property
    def pulse(self):
        return self._pulse

    @pulse.setter
    def pulse(self, val: Pulse):
        self._pulse = val
        self._pulse.onChange('omegaRMS', [lambda: self._reset_computed_attributes(['poolFree_Rrf', 'poolBound_Rrf_dualSat', 'poolBound_Rrf_singleSat_Positive', 'poolBound_Rrf_singleSat_Negative'])])
        self._pulse.onChange('offset', [lambda: self._reset_computed_attributes(['poolBound_Rrf_dualSat', 'poolBound_Rrf_singleSat_Positive', 'poolBound_Rrf_singleSat_Negative'])])
        self._changed('pulse')

    @property
    def poolFree_Rrf(self):
        if not hasattr(self, '_poolFree_Rrf'):
            self.poolFree_Rrf = diag( [ -.5 * self.pulse.omegaRMS * self.pulse.omegaRMS * self.Lorentzian(self.poolFree_T2, self.pulse.offset), *zeros(2 * (self.N_pools - 1)) ] )
        return self._poolFree_Rrf

    @poolFree_Rrf.setter
    def poolFree_Rrf(self, val: NDArray[float64]):
        self._poolFree_Rrf = array(val, dtype=float64)
        self._changed('poolFree_Rrf')

    @poolFree_Rrf.deleter
    def poolFree_Rrf(self):
        del self._poolFree_Rrf
        self._changed('poolFree_Rrf')

    @property
    def poolFree_M0(self):
        return self._poolFree_M0

    @poolFree_M0.setter
    def poolFree_M0(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0)], 'poolFree_M0')
        self._poolFree_M0 = float(val)
        self._changed('poolFree_M0')

    @property
    def poolFree_T1(self):
        return self._poolFree_T1

    @poolFree_T1.setter
    def poolFree_T1(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0)], 'poolFree_T1')
        self._poolFree_T1 = float(val)
        self._changed('poolFree_T1')

    @property
    def poolFree_T2(self):
        return self._poolFree_T2

    @poolFree_T2.setter
    def poolFree_T2(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0)], 'poolFree_T2')
        self._poolFree_T2 = float(val)
        self._changed('poolFree_T2')

    @property
    def poolFreeBound_exchangeRate(self):
        return self._poolFreeBound_exchangeRate

    @poolFreeBound_exchangeRate.setter
    def poolFreeBound_exchangeRate(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0)], 'poolFreeBound_exchangeRate')
        self._poolFreeBound_exchangeRate = float(val)
        self._changed('poolFreeBound_exchangeRate')

    @property
    def poolBound_Rrf_singleSat_Positive(self):
        if not hasattr(self, '_poolBound_Rrf_singleSat_Positive'):
            self._compute_poolBound_RFabsorptionMatrices()
        return self._poolBound_Rrf_singleSat_Positive

    @poolBound_Rrf_singleSat_Positive.setter
    def poolBound_Rrf_singleSat_Positive(self, val: NDArray[float64]):
        self._poolBound_Rrf_singleSat_Positive = array(val, dtype=float64)
        self._changed('poolBound_Rrf_singleSat_Positive')

    @poolBound_Rrf_singleSat_Positive.deleter
    def poolBound_Rrf_singleSat_Positive(self):
        del self._poolBound_Rrf_singleSat_Positive
        self._changed('poolBound_Rrf_singleSat_Positive')

    @property
    def poolBound_Rrf_singleSat_Negative(self):
        if not hasattr(self, '_poolBound_Rrf_singleSat_Negative'):
            self._compute_poolBound_RFabsorptionMatrices()
        return self._poolBound_Rrf_singleSat_Negative

    @poolBound_Rrf_singleSat_Negative.setter
    def poolBound_Rrf_singleSat_Negative(self, val: NDArray[float64]):
        self._poolBound_Rrf_singleSat_Negative = array(val, dtype=float64)
        self._changed('poolBound_Rrf_singleSat_Negative')

    @poolBound_Rrf_singleSat_Negative.deleter
    def poolBound_Rrf_singleSat_Negative(self):
        del self._poolBound_Rrf_singleSat_Negative
        self._changed('poolBound_Rrf_singleSat_Negative')

    @property
    def poolBound_Rrf_dualSat(self):
        if not hasattr(self, '_poolBound_Rrf_dualSat'):
            self._compute_poolBound_RFabsorptionMatrices()
        return self._poolBound_Rrf_dualSat

    @poolBound_Rrf_dualSat.setter
    def poolBound_Rrf_dualSat(self, val: NDArray[float64]):
        self._poolBound_Rrf_dualSat = array(val, dtype=float64)
        self._changed('poolBound_Rrf_dualSat')

    @poolBound_Rrf_dualSat.deleter
    def poolBound_Rrf_dualSat(self):
        del self._poolBound_Rrf_dualSat
        self._changed('poolBound_Rrf_dualSat')

    @property
    def poolBound_M0(self):
        return self._poolBound_M0

    @poolBound_M0.setter
    def poolBound_M0(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0)], 'poolBound_M0')
        self._poolBound_M0 = float(val)
        self._changed('poolBound_M0')

    @property
    def poolBound_T1(self):
        return self._poolBound_T1

    @poolBound_T1.setter
    def poolBound_T1(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0)], 'poolBound_T1')
        self._poolBound_T1 = float(val)
        self._changed('poolBound_T1')

    @property
    def poolBound_T2(self):
        return self._poolBound_T2

    @poolBound_T2.setter
    def poolBound_T2(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0)], 'poolBound_T2')
        self._poolBound_T2 = float(val)
        self._changed('poolBound_T2')

    @property
    def poolBound_T1D(self):
        return self._poolBound_T1D

    @poolBound_T1D.setter
    def poolBound_T1D(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0)], 'poolBound_T1D')
        self._poolBound_T1D = float(val)
        self._changed('poolBound_T1D')

    @property
    def poolBound_lineshapeAsymmetry(self):
        return self._poolBound_lineshapeAsymmetry

    @poolBound_lineshapeAsymmetry.setter
    def poolBound_lineshapeAsymmetry(self, val: float):
        check_value_is_valid(self, val, float, None, 'poolBound_lineshapeAsymmetry')
        self._poolBound_lineshapeAsymmetry = float(val)
        self._changed('poolBound_lineshapeAsymmetry')

    @property
    def poolBound_omegaLocalField(self):
        if not hasattr(self, '_poolBound_omegaLocalField'):
            self._poolBound_omegaLocalField = 1. / ( _sqrt15 * self.poolBound_T2 )
        return self._poolBound_omegaLocalField

    @poolBound_omegaLocalField.setter
    def poolBound_omegaLocalField(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0)], 'poolBound_omegaLocalField')
        self._poolBound_omegaLocalField = float(val)
        self._changed('poolBound_omegaLocalField')

    @poolBound_omegaLocalField.deleter
    def poolBound_omegaLocalField(self):
        del self._poolBound_omegaLocalField
        self._changed('poolBound_omegaLocalField')

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
        check_value_is_valid(self, val, int, [(lt, 1)], 'N_pools')
        self._N_pools = int(val)
        self._changed('N_pools')

    @N_pools.deleter
    def N_pools(self):
        del self._N_pools
        self._changed('N_pools')

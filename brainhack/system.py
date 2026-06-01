from logging import getLogger, NullHandler
from numpy import number, array, diag, fliplr, zeros, pi, sqrt, exp, sin, cos, sum, dot, deg2rad, atleast_1d, atleast_2d, zeros_like, ones_like
from numpy.typing import NDArray
from scipy.integrate import quad, dblquad
from scipy.linalg import block_diag
from scipy.special import i0
from typing import Any
from collections.abc import Callable
from operator import lt
from copy import deepcopy

from brainhack.meta import _Event, ScalarOrVector, ScalarOrMatrix, check_value_is_valid
from brainhack.pulse import Pulse

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug('`system` module loaded successfully')


_sqrt15 = sqrt(15)


class System(_Event):
    _pulse: Pulse

    _poolFree_Rrf: NDArray[number]
    _poolFree_M0: NDArray[number]
    _poolFree_T1: NDArray[number]
    _poolFree_T2: NDArray[number]

    _poolFreeBound_exchangeRate: NDArray[number]

    _poolBound_Rrf_singleSat_Positive: NDArray[number]
    _poolBound_Rrf_singleSat_Negative: NDArray[number]
    _poolBound_Rrf_dualSat: NDArray[number]
    _poolBound_lineshapeAsymmetry: NDArray[number]
    _poolBound_M0: NDArray[number]
    _poolBound_T1: NDArray[number]
    _poolBound_T2: NDArray[number]
    _poolBound_T1D: NDArray[number]
    _poolBound_omegaLocalField: NDArray[number]

    _magnetization_recovery: NDArray[number]
    _relaxation: NDArray[number]

    _N_poolFree: int
    _N_poolBound: int
    _N_pools: int

    _classAttributes: tuple[str] = ('pulse', 'poolFree_Rrf', 'poolFree_M0', 'poolFree_T1', 'poolFree_T2', 'poolFreeBound_exchangeRate', 'poolBound_Rrf_singleSat_Positive', 'poolBound_Rrf_singleSat_Negative', 'poolBound_Rrf_dualSat', 'poolBound_lineshapeAsymmetry', 'poolBound_M0', 'poolBound_T1', 'poolBound_T2', 'poolBound_T1D', 'poolBound_omegaLocalField', 'magnetization_recovery', 'relaxation', 'N_poolFree', 'N_poolBound', 'N_pools')

    def __init__(self, pulse: Pulse, poolFree_M0: ScalarOrVector, poolFree_T1: ScalarOrVector, poolFree_T2: ScalarOrVector, poolFreeBound_exchangeRate: ScalarOrMatrix, poolBound_M0: ScalarOrVector, poolBound_T1: ScalarOrVector, poolBound_T2: ScalarOrVector, poolBound_T1D: ScalarOrVector, poolBound_lineshapeAsymmetry: ScalarOrVector, *args: Any, **kwargs: Any):
        """_summary_

        Parameters
        ----------
        pulse : Pulse
            _description_
        poolFree_M0 : ScalarOrVector
            _description_
        poolFree_T1 : ScalarOrVector
            _description_
        poolFree_T2 : ScalarOrVector
            _description_
        poolFreeBound_exchangeRate : ScalarOrMatrix
            _description_
        poolBound_M0 : ScalarOrVector
            _description_
        poolBound_T1 : ScalarOrVector
            _description_
        poolBound_T2 : ScalarOrVector
            _description_
        poolBound_T1D : ScalarOrVector
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

        self.onChange('N_poolFree', [lambda: self._reset_computed_attributes(['N_pools'])])
        self.onChange('poolFree_M0', [lambda: self._check_pool_dimension_compatibility('poolFree_M0', self.poolFree_M0.shape, 'free'), lambda: self._reset_computed_attributes(['N_poolFree', 'magnetization_recovery'])])
        self.onChange('poolFree_T1', [lambda: self._check_pool_dimension_compatibility('poolFree_T1', self.poolFree_T1.shape, 'free'), lambda: self._reset_computed_attributes(['N_poolFree', 'magnetization_recovery'])])
        self.onChange('poolFree_T2', [lambda: self._check_pool_dimension_compatibility('poolFree_T2', self.poolFree_T2.shape, 'free'), lambda: self._reset_computed_attributes(['N_poolFree', 'poolFree_Rrf'])])

        self.onChange('N_pools', [lambda: self._reset_computed_attributes(['poolFree_Rrf', 'poolBound_Rrf_dualSat', 'poolBound_Rrf_singleSat_Positive', 'poolBound_Rrf_singleSat_Negative'])])
        self.onChange('poolFreeBound_exchangeRate', [lambda: self._check_pool_dimension_compatibility('poolFreeBound_exchangeRate', self.poolFreeBound_exchangeRate.shape, 'both'), lambda: self._reset_computed_attributes(['N_poolFree', 'N_poolBound'])])

        self.onChange('N_poolBound', [lambda: self._reset_computed_attributes(['N_pools'])])
        self.onChange('poolBound_M0', [lambda: self._check_pool_dimension_compatibility('poolBound_M0', self.poolBound_M0.shape, 'bound'), lambda: self._reset_computed_attributes(['N_poolBound', 'magnetization_recovery'])])
        self.onChange('poolBound_T1', [lambda: self._check_pool_dimension_compatibility('poolBound_T1', self.poolBound_T1.shape, 'bound'), lambda: self._reset_computed_attributes(['N_poolBound', 'magnetization_recovery'])])
        self.onChange('poolBound_T2', [lambda: self._check_pool_dimension_compatibility('poolBound_T2', self.poolBound_T2.shape, 'bound'), lambda: self._reset_computed_attributes(['N_poolBound', 'poolBound_Rrf_dualSat', 'poolBound_Rrf_singleSat_Positive', 'poolBound_Rrf_singleSat_Negative', 'poolBound_omegaLocalField'])])
        self.onChange('poolBound_lineshapeAsymmetry', [lambda: self._check_pool_dimension_compatibility('poolBound_lineshapeAsymmetry', self.poolBound_lineshapeAsymmetry.shape, 'bound'), lambda: self._reset_computed_attributes(['N_poolBound', 'poolBound_Rrf_singleSat_Positive', 'poolBound_Rrf_singleSat_Negative'])])
        self.onChange('poolBound_omegaLocalField', [lambda: self._check_pool_dimension_compatibility('poolBound_omegaLocalField', self.poolBound_omegaLocalField.shape, 'bound'), lambda: self._reset_computed_attributes(['N_poolBound', 'poolBound_Rrf_dualSat', 'poolBound_Rrf_singleSat_Positive', 'poolBound_Rrf_singleSat_Negative'])])

        self._check_pool_dimension_compatibility('poolFree_M0', self.poolFree_M0.shape, 'free')
        self._check_pool_dimension_compatibility('poolFree_T1', self.poolFree_T1.shape, 'free')
        self._check_pool_dimension_compatibility('poolFree_T2', self.poolFree_T2.shape, 'free')
        self._check_pool_dimension_compatibility('poolFreeBound_exchangeRate', self.poolFreeBound_exchangeRate.shape, 'both')
        self._check_pool_dimension_compatibility('poolBound_M0', self.poolBound_M0.shape, 'bound')
        self._check_pool_dimension_compatibility('poolBound_T1', self.poolBound_T1.shape, 'bound')
        self._check_pool_dimension_compatibility('poolBound_T2', self.poolBound_T2.shape, 'bound')
        self._check_pool_dimension_compatibility('poolBound_lineshapeAsymmetry', self.poolBound_lineshapeAsymmetry.shape, 'bound')
        self._check_pool_dimension_compatibility('poolBound_omegaLocalField', self.poolBound_omegaLocalField.shape, 'bound')

    def copy(self) -> System:
        return System(self.pulse.copy(), deepcopy(self.poolFree_M0), deepcopy(self.poolFree_T1), deepcopy(self.poolFree_T2), deepcopy(self.poolFreeBound_exchangeRate), deepcopy(self.poolBound_M0), deepcopy(self.poolBound_T1), deepcopy(self.poolBound_T2), deepcopy(self.poolBound_T1D), deepcopy(self.poolBound_lineshapeAsymmetry))

    def _check_pool_dimension_compatibility(self, caller: str, shape: tuple[int, ...], pool: str) -> bool:
        poolFree_attrs = ['poolFree_M0', 'poolFree_T1', 'poolFree_T2']
        poolBound_attrs = ['poolBound_M0', 'poolBound_T1', 'poolBound_T2', 'poolBound_T1D', 'poolBound_lineshapeAsymmetry', 'poolBound_omegaLocalField']

        match pool:
            case 'both':
                if len(shape) != 2:
                    raise ValueError(f'Expected a shape of length 2, received `{shape}` of length {len(shape)}. Caller: {caller}.')
                self._check_pool_dimension_compatibility('poolFreeBound_exchangeRate', (shape[0],), 'free')
                self._check_pool_dimension_compatibility('poolFreeBound_exchangeRate', (shape[1],), 'bound')
                return True

            case 'free':
                attrlist = poolFree_attrs
                if hasattr(self, '_poolFreeBound_exchangeRate') and (shape != self.poolFreeBound_exchangeRate.shape[slice(None, 1)]):
                    raise ValueError(f'Dimension mismatched between new free pool shape `{shape}` and exchange rate matrix column length `{self.poolFreeBound_exchangeRate.shape[slice(None, 1)]}`. Caller: {caller}.')

            case 'bound':
                attrlist = poolBound_attrs
                if hasattr(self, '_poolFreeBound_exchangeRate') and (shape != self.poolFreeBound_exchangeRate.shape[slice(1, None)]):
                    raise ValueError(f'Dimension mismatched between new bound pool shape `{shape}` and exchange rate matrix row length `{self.poolFreeBound_exchangeRate.shape[slice(1, None)]}`. Caller: {caller}.')

            case _:
                raise ValueError(f'Pool attribute (`{pool}`) does not match available values: [`free`, `bound`, `both`]. Caller: {caller}.')

        for attr in attrlist:
            if hasattr(self, f'_{attr}'):
                if shape != getattr(self, attr).shape:
                    raise ValueError(f'Dimension mismatched between new {pool} pool attribute shape `{shape}` and `{attr}` shape `{getattr(self, attr).shape}`. Caller: {caller}.')
                else:  # No need to check all every attribute since they will individually check their own shape against at least the 1st attribute
                    return True

        return True

    def _compute_poolBound_RFabsorptionMatrices(self):
        """_summary_
        """
        inv_omegaLocalField = 1. / self.poolBound_omegaLocalField
        angularFrequencyOffset = 2 * pi * self.pulse.offset
        norm_A = self.pulse.omegaRMS * self.pulse.omegaRMS
        norm_B = angularFrequencyOffset * inv_omegaLocalField

        superLorentzian: Callable[[NDArray[number], float], NDArray[number]] = self.PampelSuperLorentzian
        # superLorentzian: Callable[[NDArray[number], float], NDArray[number]] = self.SuperLorentzian if abs(self.pulse.offset) > 1000 else self.PampelSuperLorentzian

        if (self.poolBound_lineshapeAsymmetry != 0).any():
            poolBound_Rrf_Positive: NDArray[number] = .5 * norm_A * superLorentzian(self.poolBound_T2, self.pulse.offset - self.poolBound_lineshapeAsymmetry)
            poolBound_Rrf_Negative: NDArray[number] = .5 * norm_A * superLorentzian(self.poolBound_T2, -self.pulse.offset - self.poolBound_lineshapeAsymmetry)
        else:
            poolBound_Rrf_Positive: NDArray[number] = .5 * norm_A * superLorentzian(self.poolBound_T2, self.pulse.offset)
            poolBound_Rrf_Negative: NDArray[number] = poolBound_Rrf_Positive

        diag_elements = norm_B * norm_B
        anti_elements = norm_B * inv_omegaLocalField

        tmp_diag: NDArray[number] = [ diag( [ 1, elem] ) for elem in diag_elements]
        tmp_anti: NDArray[number] = [ fliplr( diag( [ angularFrequencyOffset, elem ] ) ) for elem in anti_elements]

        diag_Positive: NDArray[number] = [-Rrf_scalar * mat for Rrf_scalar, mat in zip(poolBound_Rrf_Positive, tmp_diag)]
        anti_Positive: NDArray[number] = [ Rrf_scalar * mat for Rrf_scalar, mat in zip(poolBound_Rrf_Positive, tmp_anti)]

        diag_Negative: NDArray[number] = [-Rrf_scalar * mat for Rrf_scalar, mat in zip(poolBound_Rrf_Negative, tmp_diag)]
        anti_Negative: NDArray[number] = [-Rrf_scalar * mat for Rrf_scalar, mat in zip(poolBound_Rrf_Negative, tmp_anti)]

        # Setters aren't defined to avoid having to deepcopy to prevent user messing with referenced arrays
        # so we need to call the vars with a leading underscore
        self._poolBound_Rrf_dualSat            = block_diag( zeros((self.N_poolFree, self.N_poolFree)), *[.5 * (tmp_diag_Positive + tmp_diag_Negative)  for tmp_diag_Positive, tmp_diag_Negative in zip(diag_Positive, diag_Negative)])
        self._poolBound_Rrf_singleSat_Positive = block_diag( zeros((self.N_poolFree, self.N_poolFree)), *[      tmp_diag_Positive + tmp_anti_Positive   for tmp_diag_Positive, tmp_anti_Positive in zip(diag_Positive, anti_Positive)])
        self._poolBound_Rrf_singleSat_Negative = block_diag( zeros((self.N_poolFree, self.N_poolFree)), *[      tmp_diag_Negative + tmp_anti_Negative   for tmp_diag_Negative, tmp_anti_Negative in zip(diag_Negative, anti_Negative)])

        # But getters are defined, so no need for the leading underscore in the var name
        self.poolBound_Rrf_dualSat.setflags(write=False)
        self.poolBound_Rrf_singleSat_Positive.setflags(write=False)
        self.poolBound_Rrf_singleSat_Negative.setflags(write=False)

    def Lorentzian(self, T2: NDArray[number], offset: float, *args: Any, **kwargs: Any) -> NDArray[number]:
        """_summary_

        Parameters
        ----------
        T2 : NDArray[number]
            _description_
        offset : float
            _description_

        Returns
        -------
        NDArray[number]
            _description_
        """
        return 2 * T2 / ( 1 + 4 * pi * pi * offset * offset * T2 * T2)

    def Gaussian(self, T2: NDArray[number], offset: float, *args: Any, **kwargs: Any) -> NDArray[number]:
        """_summary_

        Parameters
        ----------
        T2 : NDArray[number]
            _description_
        offset : float
            _description_

        Returns
        -------
        NDArray[number]
            _description_
        """
        return sqrt(2 * pi) * T2 * exp( -2 * pi * pi * offset * offset * T2 * T2 )

    def SuperLorentzian(self, T2: NDArray[number], offset: float, *args: Any, **kwargs: Any) -> NDArray[number]:
        """_summary_

        Parameters
        ----------
        T2 : NDArray[number]
            _description_
        offset : float
            _description_

        Returns
        -------
        NDArray[number]
            _description_
        """
        angular_offset_square = 4 * pi * pi * offset * offset
        reduced_R2_square = .25 / (T2 * T2)
        return sqrt( 2 * pi ) * array(list(quad(lambda cos_theta: self._Spherical(cos_theta, angular_offset_square, rT2sq, 0), 0, 1)[0] for rT2sq in reduced_R2_square))

    def PampelSuperLorentzian(self, T2: NDArray[number], offset: float, *args: Any, **kwargs: Any) -> NDArray[number]:
        """_summary_

        Parameters
        ----------
        T2 : NDArray[number]
            _description_
        offset : float
            _description_

        Returns
        -------
        NDArray[number]
            _description_
        """
        angular_offset_square = 4 * pi * pi * offset * offset
        reduced_R2_square = .25 / (T2 * T2)
        return sqrt( 2 * pi ) * array(list(quad(lambda cos_theta: self._Spherical(cos_theta, angular_offset_square, rT2sq, 985.96), 0, 1)[0] for rT2sq in reduced_R2_square))

    def Cylindrical(self, T2: NDArray[number], offset: float, *args: Any, **kwargs: Any) -> NDArray[number]:
        """_summary_

        Parameters
        ----------
        T2 : NDArray[number]
            _description_
        offset : float
            _description_

        Returns
        -------
        NDArray[number]
            _description_
        """
        angular_offset_square = 4 * pi * pi * offset * offset
        reduced_R2_square = .25 / (T2 * T2)

        if self.axonal_angle == 0:
            T2_totSquare = 1 / (985.96 + reduced_R2_square)
            return sqrt(2 * pi * T2_totSquare) * exp(-.5 * angular_offset_square * T2_totSquare)

        sin_theta = -sin(deg2rad(self.axonal_angle))
        return sqrt( .5 * pi ) * array(list(quad(lambda cos_phi: self._Spherical(sin_theta * cos_phi, angular_offset_square, rT2sq, 985.96), -1, 1)[0] for rT2sq in reduced_R2_square))

    def DispersedCylindrical(self, T2: NDArray[number], offset: float, *args: Any, **kwargs: Any) -> NDArray[number]:
        """Fiber bundle orientation distribution lineshape

        Parameters
        ----------
        T2 : NDArray[number]
            _description_
        offset : float
            _description_

        Returns
        -------
        NDArray[number]
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
    def magnetization_recovery(self):
        if not hasattr(self, '_magnetization_recovery'):
            HomogenizeCol: NDArray[number] = zeros(self.N_poolFree + 2 * (self.N_poolBound))
            HomogenizeCol[0:self.N_poolFree] = self.poolFree_M0 / self.poolFree_T1
            HomogenizeCol[self.N_poolFree::2] = self.poolBound_M0 / self.poolBound_T1
            self._magnetization_recovery = array([HomogenizeCol]).T
            self._magnetization_recovery.setflags(write=False)
            self._changed('magnetization_recovery')
        return self._magnetization_recovery

    @magnetization_recovery.deleter
    def magnetization_recovery(self):
        del self._magnetization_recovery
        self._changed('magnetization_recovery')

    @property
    def relaxation(self):
        if not hasattr(self, '_relaxation'):
            # filling the diagonal relaxations: poolFree => Zeeman compartments
            poolFree_block = diag( -(1. / self.poolFree_T1 + sum(self.poolFreeBound_exchangeRate * self.poolBound_M0, axis=1)) )
            poolBound_block = diag(array([[-(1. / T1 + exchange), 0] for T1, exchange in zip(self.poolBound_T1, sum(self.poolFreeBound_exchangeRate.T * self.poolFree_M0, axis=1))]).flatten())

            tmp = block_diag(poolFree_block, poolBound_block)

            # Filling the off-diagonal: poolBound => Zeeman compartments
            for i in range(self.N_poolFree):
                for j in range(self.N_poolBound):
                    tmp[self.N_poolFree + 2 * j, i] = self.poolFreeBound_exchangeRate[i][j] * self.poolBound_M0[j]
                    tmp[i, self.N_poolFree + 2 * j] = self.poolFreeBound_exchangeRate[i][j] * self.poolFree_M0[i]

            # filling the diagonal relaxations: poolBound => dipolar compartment
            tmp[self.N_poolFree + 1::2, self.N_poolFree + 1::2] = diag( -1. / self.poolBound_T1D )

            self._relaxation = tmp
            self._relaxation.setflags(write=False)
            self._changed('relaxation')
        return self._relaxation

    @relaxation.deleter
    def relaxation(self):
        del self._poolFree_Rrf
        self._changed('relaxation')

    @property
    def poolFree_Rrf(self):
        if not hasattr(self, '_poolFree_Rrf'):
            self._poolFree_Rrf = diag( [ *(-.5 * self.pulse.omegaRMS * self.pulse.omegaRMS * self.Lorentzian(self.poolFree_T2, self.pulse.offset)), *zeros(2 * (self.N_poolBound)) ] )
            self._poolFree_Rrf.setflags(write=False)
            self._changed('poolFree_Rrf')
        return self._poolFree_Rrf

    @poolFree_Rrf.deleter
    def poolFree_Rrf(self):
        del self._poolFree_Rrf
        self._changed('poolFree_Rrf')

    @property
    def poolFree_M0(self):
        return self._poolFree_M0

    @poolFree_M0.setter
    def poolFree_M0(self, val: ScalarOrVector):
        check_value_is_valid(self, val, ScalarOrVector, [(lt, 0)], 'poolFree_M0')
        self._poolFree_M0 = atleast_1d(val)
        self._poolFree_M0.setflags(write=False)
        self._changed('poolFree_M0')

    @property
    def poolFree_T1(self):
        return self._poolFree_T1

    @poolFree_T1.setter
    def poolFree_T1(self, val: ScalarOrVector):
        check_value_is_valid(self, val, ScalarOrVector, [(lt, 0)], 'poolFree_T1')
        self._poolFree_T1 = atleast_1d(val)
        self._poolFree_T1.setflags(write=False)
        self._changed('poolFree_T1')

    @property
    def poolFree_T2(self):
        return self._poolFree_T2

    @poolFree_T2.setter
    def poolFree_T2(self, val: ScalarOrVector):
        check_value_is_valid(self, val, ScalarOrVector, [(lt, 0)], 'poolFree_T2')
        self._poolFree_T2 = atleast_1d(val)
        self._poolFree_T2.setflags(write=False)
        self._changed('poolFree_T2')

    @property
    def poolFreeBound_exchangeRate(self):
        return self._poolFreeBound_exchangeRate

    @poolFreeBound_exchangeRate.setter
    def poolFreeBound_exchangeRate(self, val: ScalarOrMatrix):
        check_value_is_valid(self, val, ScalarOrMatrix, [(lt, 0)], 'poolFreeBound_exchangeRate')
        self._poolFreeBound_exchangeRate = atleast_2d(val)
        self._poolFreeBound_exchangeRate.setflags(write=False)
        self._changed('poolFreeBound_exchangeRate')

    @property
    def poolBound_Rrf_singleSat_Positive(self):
        if not hasattr(self, '_poolBound_Rrf_singleSat_Positive'):
            self._compute_poolBound_RFabsorptionMatrices()
            self._changed('poolBound_Rrf_singleSat_Positive')
        return self._poolBound_Rrf_singleSat_Positive

    @poolBound_Rrf_singleSat_Positive.deleter
    def poolBound_Rrf_singleSat_Positive(self):
        del self._poolBound_Rrf_singleSat_Positive
        self._changed('poolBound_Rrf_singleSat_Positive')

    @property
    def poolBound_Rrf_singleSat_Negative(self):
        if not hasattr(self, '_poolBound_Rrf_singleSat_Negative'):
            self._compute_poolBound_RFabsorptionMatrices()
            self._changed('poolBound_Rrf_singleSat_Negative')
        return self._poolBound_Rrf_singleSat_Negative

    @poolBound_Rrf_singleSat_Negative.deleter
    def poolBound_Rrf_singleSat_Negative(self):
        del self._poolBound_Rrf_singleSat_Negative
        self._changed('poolBound_Rrf_singleSat_Negative')

    @property
    def poolBound_Rrf_dualSat(self):
        if not hasattr(self, '_poolBound_Rrf_dualSat'):
            self._compute_poolBound_RFabsorptionMatrices()
            self._changed('poolBound_Rrf_dualSat')
        return self._poolBound_Rrf_dualSat

    @poolBound_Rrf_dualSat.deleter
    def poolBound_Rrf_dualSat(self):
        del self._poolBound_Rrf_dualSat
        self._changed('poolBound_Rrf_dualSat')

    @property
    def poolBound_M0(self):
        return self._poolBound_M0

    @poolBound_M0.setter
    def poolBound_M0(self, val: ScalarOrVector):
        check_value_is_valid(self, val, ScalarOrVector, [(lt, 0)], 'poolBound_M0')
        self._poolBound_M0 = atleast_1d(val)
        self._poolBound_M0.setflags(write=False)
        self._changed('poolBound_M0')

    @property
    def poolBound_T1(self):
        return self._poolBound_T1

    @poolBound_T1.setter
    def poolBound_T1(self, val: ScalarOrVector):
        check_value_is_valid(self, val, ScalarOrVector, [(lt, 0)], 'poolBound_T1')
        self._poolBound_T1 = atleast_1d(val)
        self._poolBound_T1.setflags(write=False)
        self._changed('poolBound_T1')

    @property
    def poolBound_T2(self):
        return self._poolBound_T2

    @poolBound_T2.setter
    def poolBound_T2(self, val: ScalarOrVector):
        check_value_is_valid(self, val, ScalarOrVector, [(lt, 0)], 'poolBound_T2')
        self._poolBound_T2 = atleast_1d(val)
        self._poolBound_T2.setflags(write=False)
        self._changed('poolBound_T2')

    @property
    def poolBound_T1D(self):
        return self._poolBound_T1D

    @poolBound_T1D.setter
    def poolBound_T1D(self, val: ScalarOrVector):
        check_value_is_valid(self, val, ScalarOrVector, [(lt, 0)], 'poolBound_T1D')
        self._poolBound_T1D = atleast_1d(val)
        self._poolBound_T1D.setflags(write=False)
        self._changed('poolBound_T1D')

    @property
    def poolBound_lineshapeAsymmetry(self):
        return self._poolBound_lineshapeAsymmetry

    @poolBound_lineshapeAsymmetry.setter
    def poolBound_lineshapeAsymmetry(self, val: ScalarOrVector):
        check_value_is_valid(self, val, ScalarOrVector, None, 'poolBound_lineshapeAsymmetry')
        self._poolBound_lineshapeAsymmetry = atleast_1d(val)
        self._poolBound_lineshapeAsymmetry.setflags(write=False)
        self._changed('poolBound_lineshapeAsymmetry')

    @property
    def poolBound_omegaLocalField(self):
        if not hasattr(self, '_poolBound_omegaLocalField'):
            tmp = atleast_1d(1. / ( _sqrt15 * self.poolBound_T2 ))
            tmp.setflags(write=False)
            check_value_is_valid(self, tmp, ScalarOrVector, [(lt, 0)], 'poolBound_omegaLocalField')
            self._poolBound_omegaLocalField = tmp
            self._changed('poolBound_omegaLocalField')
        return self._poolBound_omegaLocalField

    @poolBound_omegaLocalField.deleter
    def poolBound_omegaLocalField(self):
        del self._poolBound_omegaLocalField
        self._changed('poolBound_omegaLocalField')

    @property
    def N_poolFree(self):
        if not hasattr(self, '_N_poolFree'):
            check_value_is_valid(self, len(self.poolFree_T2), int, [(lt, 1)], 'N_poolFree')
            self._N_poolFree = len(self.poolFree_T2)
            self._changed('N_poolFree')
        return self._N_poolFree

    @N_poolFree.deleter
    def N_poolFree(self):
        del self._N_poolFree
        self._changed('N_poolFree')

    @property
    def N_poolBound(self):
        if not hasattr(self, '_N_poolBound'):
            check_value_is_valid(self, len(self.poolBound_T2), int, [(lt, 1)], 'N_poolBound')
            self._N_poolBound = len(self.poolBound_T2)
            self._changed('N_poolBound')
        return self._N_poolBound

    @N_poolBound.deleter
    def N_poolBound(self):
        del self._N_poolBound
        self._changed('N_poolBound')

    @property
    def N_pools(self):
        if not hasattr(self, '_N_pools'):
            check_value_is_valid(self, self.N_poolFree + self.N_poolBound, int, [(lt, 1)], 'N_pools')
            self._N_pools = self.N_poolFree + self.N_poolBound
            self._changed('N_pools')
        return self._N_pools

    @N_pools.deleter
    def N_pools(self):
        del self._N_pools
        self._changed('N_pools')

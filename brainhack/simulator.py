from logging import getLogger, NullHandler
from numpy import zeros, kron, eye, diag, array, sum, vstack, hstack, round, deg2rad, cos
from numpy.typing import NDArray
from numpy.linalg import matrix_power, eig
from scipy.linalg import expm, block_diag

from brainhack.pulse import Pulse
from brainhack.system import System
from brainhack.sequence import Sequence, Modulation

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug('`simulator` module loaded successfully')


class Simulator():
    _export_readMatrix: bool
    _system: System
    _sequence: Sequence

    _pulse: Pulse

    def __init__(self, system: System, sequence: Sequence, export_readMatrix: bool):
        """_summary_

        Parameters
        ----------
        system : System
            _description_
        sequence : Sequence
            _description_
        export_readMatrix : bool
            _description_

        Raises
        ------
        ValueError
            _description_
        """
        self.system = system
        self.sequence = sequence
        self.export_readMatrix = export_readMatrix

        if sequence.pulse != system.pulse:
            error = f'Mismatched RF pulse between sequence and system. Received {sequence.pulse} (sequence) and {system.pulse} (system).'
            logger.critical(error)
            raise ValueError(error)

        self.pulse = sequence.pulse

    def SteadyState(self) -> dict[str, NDArray[float]]:
        """_summary_

        Returns
        -------
        tuple[NDArray[float], ...]
            _description_
        """

        sys = self.system
        seq = self.sequence

        HomogenizeCol: NDArray[float] = zeros(1 + 2 * (sys.N_pools - 1))
        HomogenizeCol[0] = sys.poolFree_M0 / sys.poolFree_T1
        # print(sys.poolBound_M0)
        HomogenizeCol[1::2] = sys.poolBound_M0 / sys.poolBound_T1
        HomogenizeCol = array([HomogenizeCol]).T

        REX = block_diag(
            -(1. / sys.poolFree_T1 + sys.poolFreeBound_exchangeRate * sum(array(sys.poolBound_M0))),
            kron(
                eye(sys.N_pools - 1),
                diag( [ -(1. / sys.poolBound_T1 + sys.poolFreeBound_exchangeRate * sys.poolFree_M0), 0 ] )
            )
        )

        REX[1::2, 0] = sys.poolFreeBound_exchangeRate * sys.poolBound_M0
        REX[0, 1::2] = sys.poolFreeBound_exchangeRate * sys.poolFree_M0

        # Assuming only 1 free pool with 1 single compartment, filling the dipolar compartment relaxations
        REX[2::2, 2::2] = diag( array( [-1. / sys.poolBound_T1D] ).flatten() )

        mat_REX = vstack([hstack([REX, HomogenizeCol]), zeros((1, 2 + 2 * (sys.N_pools - 1)))])

        evol_relax_interPulse: NDArray[float] = expm(mat_REX * (seq.dt_interPulse - seq.pulse.duration))
        evol_relax_interReadRF: NDArray[float] = expm(mat_REX * seq.es)
        evol_relax_recovery: NDArray[float] = expm(mat_REX * seq.duration_recovery)
        evol_relax_TR_burst: NDArray[float] = expm(mat_REX * (seq.TR_burst - seq.N_pulse * seq.dt_interPulse))
        evol_relax_lastBurst: NDArray[float] = expm(mat_REX * (seq.dt_lastBurst - seq.N_pulse * seq.dt_interPulse))
        evol_relax_fullPrep: NDArray[float] = expm(mat_REX * seq.duration_preparation)

        evol_rf_readoutInstantAction = eye(2 + 2 * (sys.N_pools - 1))
        evol_rf_readoutInstantAction[0, 0] = cos(deg2rad(seq.readout_flipAngle))

        evol_rf_singleSat_Positive: NDArray[float] = expm(
            vstack([
                hstack( [ sys.poolBound_Rrf_singleSat_Positive + sys.poolFree_Rrf + REX, HomogenizeCol ] ),
                zeros( (1, 2 + 2 * (sys.N_pools - 1)) )
            ]) * seq.pulse.duration
        )

        evol_rf_singleSat_Negative: NDArray[float] = expm(
            vstack([
                hstack( [ sys.poolBound_Rrf_singleSat_Negative + sys.poolFree_Rrf + REX, HomogenizeCol ] ),
                zeros( (1, 2 + 2 * (sys.N_pools - 1)) )
            ]) * seq.pulse.duration
        )

        read: NDArray[float] = evol_relax_interReadRF @ evol_rf_readoutInstantAction
        evol_RAGE: NDArray[float] = evol_relax_recovery @ matrix_power(read, seq.N_adc - seq.N_dummyADC)
        evol_dummyRAGE: NDArray[float] = matrix_power(read, seq.N_dummyADC)

        evol_MTsat_single: NDArray[float] = (evol_relax_lastBurst @ matrix_power(evol_relax_interPulse @ evol_rf_singleSat_Positive, seq.N_pulse)) \
            @ matrix_power(evol_relax_TR_burst @ matrix_power(evol_relax_interPulse @ evol_rf_singleSat_Positive, seq.N_pulse), seq.N_burst - 1)

        # array in steady-state is the eigenvector associated to eigenvalue=1 (last column here)
        # Indeed: eigenequation is <Av = lv> with l the eigenvalue of A associated to the eigenvector v
        # Meanwhile: steady state equation is <Av = v>. We can identify both equations by setting l = 1.
        # For l = 1, v_1 is the steady state eigenvector of A, i.e., the steady state magnetization of A.
        # Eigenvectors are always defined up to a scaling factor. The last element of v_1 is also necessarily non-zero.
        # The last element of v_1, present because of the homogeneization of matrix A, is not associated to a physical quantity.
        # We choose the normalization where this last element of v_1 is unity, so we rescale v_1 by the scalar <1. / v_1[-1]>
        v_MT0 = eig(round(evol_dummyRAGE @ (evol_relax_fullPrep @ evol_RAGE), 16))[1][:, -1]
        v_MTs = eig(round(evol_dummyRAGE @ (evol_MTsat_single @ evol_RAGE), 16))[1][:, -1]

        output: dict[str, NDArray[float]] = {
            'MT0': v_MT0 / v_MT0[-1],
            'MTs': v_MTs / v_MTs[-1],
        }

        if Modulation.CM in seq.modulation:
            evol_rf_dualSat_SM: NDArray[float] = expm(
                vstack([
                    hstack( [ sys.poolBound_Rrf_dualSat + sys.poolFree_Rrf + REX, HomogenizeCol ] ),
                    zeros( (1, 2 + 2 * (sys.N_pools - 1)) )
                ]) * seq.pulse.duration
            )

            evol_MTsat_dual_CM: NDArray[float] = (evol_relax_lastBurst @ matrix_power(evol_relax_interPulse @ evol_rf_dualSat_SM, seq.N_pulse)) \
                @ matrix_power(evol_relax_TR_burst @ matrix_power(evol_relax_interPulse @ evol_rf_dualSat_SM, seq.N_pulse), seq.N_burst - 1)

            v_MTd_CM = eig(round(evol_dummyRAGE @ (evol_MTsat_dual_CM @ evol_RAGE), 16))[1][:, -1]
            MTd_CM = v_MTd_CM / v_MTd_CM[-1]

            output['MTd_CM'] = MTd_CM

        if Modulation.ALT in seq.modulation:
            evol_MTsat_dual_ALT: NDArray[float] = evol_relax_lastBurst @ matrix_power(
                    matrix_power(evol_relax_interPulse @ evol_rf_singleSat_Negative, seq.N_pulsePerOffset)
                    @ matrix_power(evol_relax_interPulse @ evol_rf_singleSat_Positive, seq.N_pulsePerOffset),
                    int(.5 * seq.N_pulse / seq.N_pulsePerOffset)
                ) \
                @ matrix_power(evol_relax_TR_burst @ matrix_power(
                        matrix_power(evol_relax_interPulse @ evol_rf_singleSat_Negative, seq.N_pulsePerOffset)
                        @ matrix_power(evol_relax_interPulse @ evol_rf_singleSat_Positive, seq.N_pulsePerOffset),
                        int(.5 * seq.N_pulse / seq.N_pulsePerOffset)
                    ),
                    seq.N_burst - 1
                )

            v_MTd_ALT = eig(round(evol_dummyRAGE @ (evol_MTsat_dual_ALT @ evol_RAGE), 16))[1][:, -1]
            MTd_ALT = v_MTd_ALT / v_MTd_ALT[-1]

            output['MTd_ALT'] = MTd_ALT

        if self.export_readMatrix:
            output['readout'] = read

        return output

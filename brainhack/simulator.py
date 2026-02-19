from logging import getLogger, NullHandler
from numpy import float64, zeros, kron, eye, diag, array, sum, vstack, hstack, round, matmul, radians, cos
from numpy.typing import NDArray
from numpy.linalg import matrix_power, eig
from scipy.linalg import expm, block_diag

from brainhack.system import System
from brainhack.sequence import Sequence, Modulation

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug('`simulator` module loaded successfully')


def SteadyState(system: System, sequence: Sequence) -> tuple[NDArray[float64], ...]:
    """_summary_

    Parameters
    ----------
    system : System
        _description_
    sequence : Sequence
        _description_

    Returns
    -------
    tuple[float]
        _description_

    Raises
    ------
    ValueError
        _description_
    """
    if sequence.pulse != system.pulse:
        error = f'Mismatched RF pulse between sequence and system. Received {sequence.pulse} (sequence) and {system.pulse} (system).'
        logger.critical(error)
        raise ValueError(error)

    HomogenizeCol: NDArray[float64] = zeros(1 + 2 * (system.N_pools - 1))
    HomogenizeCol[0] = system.poolFree_M0 / system.poolFree_T1
    # print(system.poolBound_M0)
    HomogenizeCol[1::2] = system.poolBound_M0 / system.poolBound_T1
    HomogenizeCol = array([HomogenizeCol]).T

    REX = block_diag(
        -(1. / system.poolFree_T1 + system.poolFreeBound_exchangeRate * sum(array(system.poolBound_M0))),
        kron(
            eye(system.N_pools - 1),
            diag( [ -(1. / system.poolBound_T1 + system.poolFreeBound_exchangeRate * system.poolFree_M0), 0 ] )
        )
    )

    REX[1::2, 0] = system.poolFreeBound_exchangeRate * system.poolBound_M0
    REX[0, 1::2] = system.poolFreeBound_exchangeRate * system.poolFree_M0

    # Assuming only 1 free pool with 1 single compartment, filling the dipolar compartment relaxations
    REX[2::2, 2::2] = diag( array( [-1. / system.poolBound_T1D] ).flatten() )

    mat_REX = vstack([hstack([REX, HomogenizeCol]), zeros((1, 2 + 2 * (system.N_pools - 1)))])

    evol_relax_interPulse: NDArray[float64] = expm(mat_REX * (sequence.dt_interPulse - sequence.pulse.duration))
    evol_relax_interReadRF: NDArray[float64] = expm(mat_REX * sequence.es)
    evol_relax_recovery: NDArray[float64] = expm(mat_REX * sequence.duration_recovery)
    evol_relax_TR_burst: NDArray[float64] = expm(mat_REX * (sequence.TR_burst - sequence.N_pulse * sequence.dt_interPulse))
    evol_relax_lastBurst: NDArray[float64] = expm(mat_REX * (sequence.dt_lastBurst - sequence.N_pulse * sequence.dt_interPulse))
    evol_relax_fullPrep: NDArray[float64] = expm(mat_REX * sequence.duration_preparation)

    evol_rf_readoutInstantAction = eye(2 + 2 * (system.N_pools - 1))
    evol_rf_readoutInstantAction[0, 0] = cos(radians(sequence.readout_flipAngle))

    evol_rf_singleSat_Positive: NDArray[float64] = expm(
        vstack([
            hstack( [ system.poolBound_Rrf_singleSat_Positive + system.poolFree_Rrf + REX, HomogenizeCol ] ),
            zeros( (1, 2 + 2 * (system.N_pools - 1)) )
        ]) * sequence.pulse.duration
    )

    evol_rf_singleSat_Negative: NDArray[float64] = expm(
        vstack([
            hstack( [ system.poolBound_Rrf_singleSat_Negative + system.poolFree_Rrf + REX, HomogenizeCol ] ),
            zeros( (1, 2 + 2 * (system.N_pools - 1)) )
        ]) * sequence.pulse.duration
    )

    evol_RAGE: NDArray[float64] = matmul( evol_relax_recovery, matrix_power(matmul(evol_relax_interReadRF, evol_rf_readoutInstantAction), sequence.N_adc) )

    evol_MTsat_single: NDArray[float64] = matmul(
        matmul( evol_relax_lastBurst, matrix_power(matmul(evol_relax_interPulse, evol_rf_singleSat_Positive), sequence.N_pulse) ),
        matrix_power( matmul(evol_relax_TR_burst , matrix_power(matmul(evol_relax_interPulse, evol_rf_singleSat_Positive), sequence.N_pulse)), sequence.N_burst - 1)
    )

    # array in steady-state is the eigenvector associated to eigenvalue=1 (last column here)
    # Indeed: eigenequation is <Av = lv> with l the eigenvalue of A associated to the eigenvector v
    # Meanwhile: steady state equation is <Av = v>. We can identify both equations by setting l = 1.
    # For l = 1, v_1 is the steady state eigenvector of A, i.e., the steady state magnetization of A.
    # Eigenvectors are always defined up to a scaling factor. The last element of v_1 is also necessarily non-zero.
    # The last element of v_1, present because of the homogeneization of matrix A, is not associated to a physical quantity.
    # We choose the normalization where this last element of v_1 is unity, so we rescale v_1 by the scalar <1. / v_1[-1]>
    v_MT0 = eig(round(matmul(evol_relax_fullPrep, evol_RAGE), 16))[1][:, -1]
    v_MTs = eig(round(matmul(evol_MTsat_single, evol_RAGE), 16))[1][:, -1]

    MT0: NDArray[float64] = v_MT0 / v_MT0[-1]
    MTs: NDArray[float64] = v_MTs / v_MTs[-1]

    MTds: list[NDArray[float64]] = list()
    if Modulation.CM in sequence.modulation:
        evol_rf_dualSat_SM: NDArray[float64] = expm(
            vstack([
                hstack( [ system.poolBound_Rrf_dualSat + system.poolFree_Rrf + REX, HomogenizeCol ] ),
                zeros( (1, 2 + 2 * (system.N_pools - 1)) )
            ]) * sequence.pulse.duration
        )

        evol_MTsat_dual_CM: NDArray[float64] = matmul(
            matmul( evol_relax_lastBurst, matrix_power(matmul(evol_relax_interPulse, evol_rf_dualSat_SM), sequence.N_pulse) ),
            matrix_power( matmul(evol_relax_TR_burst , matrix_power(matmul(evol_relax_interPulse, evol_rf_dualSat_SM), sequence.N_pulse)), sequence.N_burst - 1)
        )

        v_MTd_CM = eig(round(matmul(evol_MTsat_dual_CM, evol_RAGE), 16))[1][:, -1]
        MTd_CM = v_MTd_CM / v_MTd_CM[-1]

        MTds.append(MTd_CM)

    if Modulation.ALT in sequence.modulation:
        evol_MTsat_dual_ALT: NDArray[float64] = matmul(
            matmul(
                evol_relax_lastBurst,
                matrix_power(
                    matmul(matrix_power(matmul(evol_relax_interPulse, evol_rf_singleSat_Negative),
                                        sequence.N_pulsePerOffset),
                           matrix_power(matmul(evol_relax_interPulse, evol_rf_singleSat_Positive),
                                        sequence.N_pulsePerOffset)),
                    int(.5 * sequence.N_pulse / sequence.N_pulsePerOffset)
                )
            ),
            matrix_power(
                matmul(
                    evol_relax_TR_burst,
                    matrix_power(
                        matmul(matrix_power(matmul(evol_relax_interPulse, evol_rf_singleSat_Negative),
                                            sequence.N_pulsePerOffset),
                               matrix_power(matmul(evol_relax_interPulse, evol_rf_singleSat_Positive),
                                            sequence.N_pulsePerOffset)),
                        int(.5 * sequence.N_pulse / sequence.N_pulsePerOffset)
                    )
                ),
                sequence.N_burst - 1
            )
        )

        v_MTd_ALT = eig(round(matmul(evol_MTsat_dual_ALT, evol_RAGE), 16))[1][:, -1]
        MTd_ALT = v_MTd_ALT / v_MTd_ALT[-1]

        MTds.append(MTd_ALT)

    return MT0, MTs, *MTds

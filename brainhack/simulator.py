from .system import System
from .sequence import Sequence, Modulation

from numpy import ndarray, zeros, kron, eye, diag, array, sum, vstack, hstack, abs, matmul, radians, cos
from numpy.linalg import matrix_power
from scipy.linalg import expm, block_diag, eig, eigvals      
from sys import exit

def Simulate(system: System, sequence: Sequence) -> tuple[float]:
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
    """
    HomogenizeCol: ndarray = zeros((1 + 2 * (system.N_pools - 1)))
    # print(HomogenizeCol.shape)
    HomogenizeCol[0] = system.poolFree_M0 / system.poolFree_T1
    # print(system.poolBound_M0)
    HomogenizeCol[1::2] = system.poolBound_M0 / system.poolBound_T1

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

    mat_REX = vstack([hstack([REX, HomogenizeCol.T]), zeros((1, 2 + 2 * (system.N_pools - 1)))])
    # print(HomogenizeCol)
    # print(REX)
    # print(mat_REX)
 
    evol_relax_interPulse = expm(mat_REX * (sequence.dt_interPulse - sequence.pulse.duration))
    # print("evol_relax_interPulse", evol_relax_interPulse)
    evol_relax_interReadRF = expm(mat_REX * sequence.ES)
    evol_relax_recovery = expm(mat_REX * sequence.duration_recovery)
    evol_relax_TR_burst = expm(mat_REX * (sequence.TR_burst - sequence.N_pulse * sequence.dt_interPulse))
    evol_relax_lastBurst = expm(mat_REX * (sequence.dt_LastBurst - sequence.N_pulse * sequence.dt_interPulse))
    evol_relax_fullPrep = expm(mat_REX * sequence.duration_preparation)


   
    evol_rf_readoutInstantAction = eye(2 + 2 * (system.N_pools - 1))
    evol_rf_readoutInstantAction[0, 0] = cos(radians(sequence.readout_flipAngle))
    # print("evol_rf_readoutInstantAction", evol_rf_readoutInstantAction) 
    # print("-----------------------------------------------------------------------------------")

    # print("system.poolBound_Rrf_singleSat_Positive", system.poolBound_Rrf_singleSat_Positive)
    # print("system.poolFree_Rrf",system.poolFree_Rrf)
    # print("-----------------------------------------------------------------------------------")
    temp = vstack([hstack( [ system.poolBound_Rrf_singleSat_Positive + system.poolFree_Rrf + REX, HomogenizeCol.T ] ) ,
            zeros( (1, 2 + 2 * (system.N_pools - 1)) )])
    # print("temp", temp)
    # print("-----------------------------------------------------------------------------------")
    # print("sequence.pulse.duration", sequence.pulse.duration)
    evol_rf_singleSat_Positive = expm(
        vstack([
            hstack( [ system.poolBound_Rrf_singleSat_Positive + system.poolFree_Rrf + REX, HomogenizeCol.T ] ),
            zeros( (1, 2 + 2 * (system.N_pools - 1)) )
        ]) * sequence.pulse.duration
    )
    # print("evol_rf_singleSat_Positive", evol_rf_singleSat_Positive)
    # print("-----------------------------------------------------------------------------------")

   

    evol_rf_singleSat_Negative = expm(
        vstack([
            hstack( [ system.poolBound_Rrf_singleSat_Negative + system.poolFree_Rrf + REX, HomogenizeCol.T ] ),
            zeros( (1, 2 + 2 * (system.N_pools - 1)) )
        ]) * sequence.pulse.duration
    )

    evol_RAGE = matmul( evol_relax_recovery, matrix_power(matmul(evol_relax_interReadRF, evol_rf_readoutInstantAction), sequence.N_adc) )

    # print("evol_RAGE", evol_RAGE)
    # print("-----------------------------------------------------------------------------------")

    
    evol_MTsat_single = matmul(
        matmul( evol_relax_lastBurst, matrix_power(matmul(evol_relax_interPulse, evol_rf_singleSat_Positive), sequence.N_pulse) ),
        matrix_power( matmul(evol_relax_TR_burst , matrix_power(matmul(evol_relax_interPulse, evol_rf_singleSat_Positive), sequence.N_pulse)), sequence.N_burst - 1)
    )
    # print("evol_MTsat_single", evol_MTsat_single)
    # print("-----------------------------------------------------------------------------------")

    
    #exit()
    
    if Modulation.CM in sequence.modulation:
        evol_rf_dualSat_SM = expm(
            vstack([
                hstack( [ system.poolBound_Rrf_dualSat + system.poolFree_Rrf + REX, HomogenizeCol.T ] ),
                zeros( (1, 2 + 2 * (system.N_pools - 1)) )
            ]) * sequence.pulse.duration
        )

        evol_MTsat_dual_CM = matmul(
            matmul( evol_relax_lastBurst, matrix_power(matmul(evol_relax_interPulse, evol_rf_dualSat_SM), sequence.N_pulse) ),
            matrix_power( matmul(evol_relax_TR_burst , matrix_power(matmul(evol_relax_interPulse, evol_rf_dualSat_SM), sequence.N_pulse)), sequence.N_burst - 1)
        )
        
        # print("evol_MTsat_dual_CM", evol_MTsat_dual_CM)
        # print("-----------------------------------------------------------------------------------")

    if Modulation.ALT in sequence.modulation:
        evol_MTsat_dual_ALT = matmul(
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
        # print("evol_MTsat_dual_ALT", evol_MTsat_dual_ALT)
        # print("-----------------------------------------------------------------------------------")


    # array in steady-state is the eigenvector associated to eigenvalue=1 (last column here)
    # normalization: see https://github.com/mriphysics/ihMT_steadystate/blob/master/src/ssSPGR_ihMT_integrate.m#L121-L123
    v_MT0 = eig(matmul(evol_relax_fullPrep, evol_RAGE))[1]
    # print("vector_MT0", v_MT0)
    # print("value_MT0", eigvals(matmul(evol_relax_fullPrep, evol_RAGE)))
    # print("-----------------------------------------------------------------------------------")
    
    v_MTs = eig(matmul(evol_MTsat_single, evol_RAGE))[1]

    MT0 = v_MT0[:, -1] / v_MT0[-1, -1]
    MTs = abs(v_MTs[:, -1] / v_MTs[-1, -1])

    # print("MT0", MT0)
    # print("MTs", MTs)
    # print("-----------------------------------------------------------------------------------")
    
    # ihMTs = list()
    MTds = list()
    if Modulation.CM in sequence.modulation:
        v_MTd_CM = eig(matmul(evol_MTsat_dual_CM, evol_RAGE))[1]
        MTd_CM = abs(v_MTd_CM[:, -1] / v_MTd_CM[-1, -1])

        # ihMT_cm = 2 * (abs(V2(1, end) / V2(end, end)) - abs(V3(1, end) / V3(end, end)));
        # ihMTs.append(...)
        MTds.append(MTd_CM)

    if Modulation.ALT in sequence.modulation:
        v_MTd_ALT = eig(matmul(evol_MTsat_dual_ALT, evol_RAGE))[1]
        MTd_ALT = abs(v_MTd_ALT[:, -1] / v_MTd_ALT[-1, -1])

        # ihMT_alt = 2 * (abs(V2(1, end) / V2(end, end)) - abs(V3(1, end) / V3(end, end)));
        # ihMTs.append(...)
        MTds.append(MTd_ALT)

    return MT0, MTs, *MTds

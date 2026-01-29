# To Do

from system import System
from sequence import Sequence, Modulation
from numpy import ndarray, zeros, kron, eye, diag, array, sum, vstack, hstack, radians, cos
from scipy.linalg import expm, block_diag, eig

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
    C: ndarray = zeros((1, 1 + system.N_compartments))
    C[0] = system.poolFree_M0 / system.poolFree_T1
    C[1::2] = system.poolBound_M0 / system.poolBound_T1

    REX = block_diag( [
        -(1. / system.poolFree_T1 + system.poolFreeBound_exchangeRate * sum(array(system.poolBound_M0))),
        kron(
            eye(system.N_compartments),
            diag( [ -(1. / system.poolBound_T1 + system.poolFreeBound_exchangeRate * system.poolFree_M0), 0 ] )
        )
    ])

    REX[1::2, 0] = system.poolFreeBound_exchangeRate * system.poolBound_M0
    REX[0, 1::2] = system.poolFreeBound_exchangeRate * system.poolFree_M0

    # Assuming only 1 free pool with 1 single compartment, filling the dipolar compartment relaxations
    REX[2::2, 2::2] = diag( array( [-1. / system.poolBound_T1D] ).flatten() )

    mat_REX = vstack([hstack([REX, C.T]), zeros((1, 2 + system.N_compartments))])

    evol_relax_interPulse = expm(mat_REX * sequence.dt_interPulse - sequence.pulse.duration)
    evol_relax_interReadRF = expm(mat_REX * sequence.ES)
    evol_relax_recovery = expm(mat_REX * sequence.duration_recovery)
    evol_relax_TR_burst = expm(mat_REX * (sequence.TR_burst - sequence.N_pulse * sequence.dt_interPulse))
    evol_relax_lastBurst = expm(mat_REX * (sequence.dt_LastBurst - sequence.N_pulse * sequence.dt_interPulse))
    evol_relax_fullPrep = expm(mat_REX * sequence.duration_preparation)

    evol_rf_readoutInstantAction = eye(2 + 2 * system.N_compartments)
    evol_rf_readoutInstantAction[0, 0] = cos(radians(sequence.readout_flipAngle))

    # Xt.PW_P                 = func_expm( vertcat([PREP.W_P(:,:) + PREP.W_DS(:,:) + REX C], zeros(1, 2 * tiss.Ncomp + 2)), PREP.PW ); % pulse P
    # Xt.PW_M                 = func_expm( vertcat([PREP.W_M(:,:) + PREP.W_DS(:,:) + REX C], zeros(1, 2 * tiss.Ncomp + 2)), PREP.PW ); % pulse M
    
    # %%% final operators
    # Xt.RAGE                 = Xt.RD_TR * (Xt.TRsub * Xt.EXC)^RAGE.TurboFac;
    # Xt.PREP_MTs(:,:)        = (Xt.BTR_last * (Xt.delta_t * Xt.PW_P)^PREP.Np) * ((Xt.BTR * (Xt.delta_t * Xt.PW_P)^PREP.Np)^(PREP.N_BTR - 1));

    if Modulation.CM in sequence.modulation:
        # Xt.PW_SM(:,:)       = func_expm( vertcat([PREP.W_SM(:,:) + PREP.W_DS(:,:) + REX C], zeros(1, 2 * tiss.Ncomp + 2)), PREP.PW );
        # Xt.PREP_MTd(:,:)    = Xt.BTR_last * (Xt.delta_t * Xt.PW_SM(:,:))^PREP.Np * (Xt.BTR * (Xt.delta_t * Xt.PW_SM(:,:))^PREP.Np)^(PREP.N_BTR - 1);
        ...

    if Modulation.ALT in sequence.modulation:
        # Xt.PREP_MTd(:,:)    = ...
        # (Xt.BTR_last * ((Xt.delta_t * Xt.PW_M)^PREP.N_altern * (Xt.delta_t * Xt.PW_P)^PREP.N_altern)^(0.5 * PREP.Np / PREP.N_altern)) * ...
        # (Xt.BTR * ((Xt.delta_t * Xt.PW_M)^PREP.N_altern * (Xt.delta_t * Xt.PW_P)^PREP.N_altern)^(0.5 * PREP.Np / PREP.N_altern))^(PREP.N_BTR - 1);
        ...

    # array in steady-state is the eigenvector associated to eigenvalue=1 (last column here)
    # normalization: see https://github.com/mriphysics/ihMT_steadystate/blob/master/src/ssSPGR_ihMT_integrate.m#L121-L123
    # [V1,~]  = eig(Xt.PREP_MT0 * Xt.RAGE, 'vector');       % MT0
    # [V2,~]  = eig(Xt.PREP_MTs(:,:) * Xt.RAGE, 'vector');  % MTs
    # [V3,~]  = eig(Xt.PREP_MTd(:,:) * Xt.RAGE, 'vector');  % MTd

    # MT0    = V1(1, end) / V1(end, end);
    
    ihMTs = list()
    if Modulation.CM in sequence.modulation:
        # ihMT_cm = 2 * (abs(V2(1, end) / V2(end, end)) - abs(V3(1, end) / V3(end, end)));
        ihMTs.append(...)
    
    if Modulation.ALT in sequence.modulation:
        # ihMT_alt = 2 * (abs(V2(1, end) / V2(end, end)) - abs(V3(1, end) / V3(end, end)));
        ihMTs.append(...)

    return ...

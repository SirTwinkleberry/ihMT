% compute ihMTR/MTRs/MTRd right before the first RAGE shot
% (i.e. assumes a centric acquisition)
% Lucas SOUSTELLE 2022/02/09, CRMBM-CEMEREM Lab. UMR 7339, Marseille, France
% Updated: 2024/07/25, Timothy Anderson (round at duration check, more outputs, ihMT instead of ihMTR...)

function [ihMT, MT0] = wrapper_qihMT_RAGE_HPC(xData)
    %% handle fixed parameters & quantities
    tiss      = xData.tiss;
    PREP      = xData.PREP;
    RAGE      = xData.RAGE;

    % restore into structs
    tiss.T2b  = xData.fixedvals(1);
    tiss.T2f  = xData.fixedvals(2);
    tiss.R    = xData.fixedvals(3);
    tiss.R1b  = xData.fixedvals(4);
    tiss.R1f  = xData.fixedvals(5);
    tiss.M0bs = xData.fixedvals(6 : 6 + tiss.Ncomp - 1);
    tiss.T1Ds = xData.fixedvals(6 + tiss.Ncomp : end);

    % define experimental quantities
    %%% constant variables
    % if ~isfield(xData,'Np');        PREP.Np         = PREP.Np * ones(size(xData.N_altern));         else, PREP.Np       = xData.Np;         end
    % if ~isfield(xData,'BTR_last');  PREP.BTR_last   = PREP.BTR_last * ones(size(xData.N_altern));   else, PREP.BTR_last = xData.BTR_last;   end
    % if ~isfield(xData,'BTR');       PREP.BTR        = PREP.BTR * ones(size(xData.N_altern));        else, PREP.BTR      = xData.BTR;        end
    % if ~isfield(xData,'N_BTR');     PREP.N_BTR      = PREP.N_BTR * ones(size(xData.N_altern));      else, PREP.N_BTR    = xData.N_BTR;      end

    %%% others that should always be defined
    PREP.N_altern = xData.N_altern;
    PREP.delta_f  = xData.delta_f;
    PREP.FA_sat   = xData.FA_sat;
    RAGE.DUR      = RAGE.TurboFac * RAGE.TRsub;

    % %%% check some durations
    if RAGE.TR < round(RAGE.DUR+(PREP.N_BTR-1)*PREP.BTR + PREP.BTR_last,6)
        error('ERROR: RAGE.TR too short for some experiments')
    end
    if PREP.delta_t < PREP.PW
        error('ERROR: PREP.delta_t < PREP.PW')
    end
    if PREP.BTR < round(PREP.Np*PREP.delta_t,6)
        error('ERROR: PREP.BTR too short for some experiments')
    end


    %% declare
    idx_diag    = 1 : 1 + 2 * tiss.Ncomp + 1 : (1 + 2 * tiss.Ncomp)^2;
    C           = zeros(1 + 2 * tiss.Ncomp, 1);


    %% Invariant relax & exchanges
    REX                     = blkdiag(-(tiss.R1f + tiss.R * sum(tiss.M0bs)), kron(eye(tiss.Ncomp), diag([-(tiss.R1b + tiss.R * tiss.M0f) ; 0])));
    REX(2:2:end,1)          = tiss.R * tiss.M0bs;
    REX(1,2:2:end)          = tiss.R * tiss.M0f;
    REX(idx_diag(3:2:end))  = -1 ./ tiss.T1Ds;
    C(1)                    = tiss.R1f * tiss.M0f;
    C(2:2:end)              = tiss.R1b * tiss.M0bs;
    REX_At                  = vertcat([REX C], zeros(1, 2 * tiss.Ncomp + 2)); % tiss.Ncomp*2+2 = 1 Free Pool + 2* #Bound Pools + 1 additionnal (C)

    %% Invariant operators
    %%% PREP Xtilde operators
    Xt.delta_t  = func_expm( REX_At, PREP.delta_t - PREP.PW );                % delta_t

    %%% RAGE Xtilde operators (pulses = instant. & no MT)
    Xt.EXC      = diag([cos(RAGE.FA) ones(1, 2 * tiss.Ncomp + 1)]);           % RAGE EXC
    Xt.TRsub    = func_expm( REX_At, RAGE.TRsub );                            % RAGE sub-TR ('echo spacing')


    %% Varying operators Xtilde for PREP & RARE
    %%% PREP operators
    PREP.DUR                = (PREP.N_BTR-1).*PREP.BTR + PREP.BTR_last;
    
    Xt.RD_TR                = func_expm( REX_At, RAGE.TR-PREP.DUR-RAGE.DUR );
    Xt.PREP_MT0             = func_expm( REX_At, PREP.DUR );                                                                         % MT0
    Xt.BTR                  = func_expm( REX_At, PREP.BTR-PREP.Np*PREP.delta_t );                                                    % BTR
    Xt.BTR_last             = func_expm( REX_At, PREP.BTR_last-PREP.Np*PREP.delta_t );                                               % BTR_last
    Xt.PW_P                 = func_expm( vertcat([PREP.W_P(:,:) + PREP.W_DS(:,:) + REX C], zeros(1, 2 * tiss.Ncomp + 2)), PREP.PW ); % pulse P
    Xt.PW_M                 = func_expm( vertcat([PREP.W_M(:,:) + PREP.W_DS(:,:) + REX C], zeros(1, 2 * tiss.Ncomp + 2)), PREP.PW ); % pulse M
    
    %%% final operators
    Xt.RAGE                 = Xt.RD_TR * (Xt.TRsub * Xt.EXC)^RAGE.TurboFac;
    Xt.PREP_MTs(:,:)        = (Xt.BTR_last * (Xt.delta_t * Xt.PW_P)^PREP.Np) * ((Xt.BTR * (Xt.delta_t * Xt.PW_P)^PREP.Np)^(PREP.N_BTR - 1));

    % Cosine Modulated
    if PREP.FLAG_Sine_Modulation
        Xt.PW_SM(:,:)       = func_expm( vertcat([PREP.W_SM(:,:) + PREP.W_DS(:,:) + REX C], zeros(1, 2 * tiss.Ncomp + 2)), PREP.PW );
        Xt.PREP_MTd(:,:)    = Xt.BTR_last * (Xt.delta_t * Xt.PW_SM(:,:))^PREP.Np * (Xt.BTR * (Xt.delta_t * Xt.PW_SM(:,:))^PREP.Np)^(PREP.N_BTR - 1);

    % Frequency Alternated
    else
        Xt.PREP_MTd(:,:)    = ...
            (Xt.BTR_last * ((Xt.delta_t * Xt.PW_M)^PREP.N_altern * (Xt.delta_t * Xt.PW_P)^PREP.N_altern)^(0.5 * PREP.Np / PREP.N_altern)) * ...
            (Xt.BTR * ((Xt.delta_t * Xt.PW_M)^PREP.N_altern * (Xt.delta_t * Xt.PW_P)^PREP.N_altern)^(0.5 * PREP.Np / PREP.N_altern))^(PREP.N_BTR - 1);
    end


    %% Compute steady-state ihMTR
    % array in steady-state is the eigenvector associated to eigenvalue=1 (last column here)
    % normalization: see https://github.com/mriphysics/ihMT_steadystate/blob/master/src/ssSPGR_ihMT_integrate.m#L121-L123

    [V1,~]  = eig(Xt.PREP_MT0 * Xt.RAGE, 'vector');       % MT0
    [V2,~]  = eig(Xt.PREP_MTs(:,:) * Xt.RAGE, 'vector');  % MTs
    [V3,~]  = eig(Xt.PREP_MTd(:,:) * Xt.RAGE, 'vector');  % MTd

    MT0    = V1(1, end) / V1(end, end);
    ihMT   = 2 * (abs(V2(1, end) / V2(end, end)) - abs(V3(1, end) / V3(end, end)));
end

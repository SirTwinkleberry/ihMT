% compute ihMTR/MTRs/MTRd right before the first RAGE shot
% (i.e. assumes a centric acquisition)
% Lucas SOUSTELLE 2022/02/09, CRMBM-CEMEREM Lab. UMR 7339, Marseille, France
% Updated: 2024/07/25, Timothy Anderson (round at duration check, more outputs, ihMT instead of ihMTR...)

function [OUT, MT0, out_readout] = wrapper_qihMT_RAGE(parx,xData)
    %% handle fixed parameters & quantities
    tiss    = xData.tiss;
    PREP    = xData.PREP;
    RAGE    = xData.RAGE;
    fixparx = xData.fixparx;

    % handle fixed values; fixparx = [ T2b T2f R R1b R1f [M0bs] [T1Ds] ]
    parxtmp                 = zeros(size(fixparx));
    parxtmp(fixparx == 1)   = xData.fixedvals;
    parxtmp(fixparx == 0)   = parx;

    % restore into structs
    tiss.T2b    = parxtmp(1);
    tiss.T2f    = parxtmp(2);
    tiss.R      = parxtmp(3);
    tiss.R1b    = parxtmp(4);
    tiss.R1f    = parxtmp(5);
    tiss.M0bs   = parxtmp(6:6+tiss.Ncomp-1);
    tiss.T1Ds   = parxtmp(6+tiss.Ncomp:end);

    % define experimental quantities
    %%% constant variables
    if ~isfield(xData,'Np');        PREP.Np         = PREP.Np * ones(size(xData.N_altern));         else, PREP.Np       = xData.Np;         end
    if ~isfield(xData,'BTR_last');  PREP.BTR_last   = PREP.BTR_last * ones(size(xData.N_altern));   else, PREP.BTR_last = xData.BTR_last;   end
    if ~isfield(xData,'BTR');       PREP.BTR        = PREP.BTR * ones(size(xData.N_altern));        else, PREP.BTR      = xData.BTR;        end
    if ~isfield(xData,'N_BTR');     PREP.N_BTR      = PREP.N_BTR * ones(size(xData.N_altern));      else, PREP.N_BTR    = xData.N_BTR;      end

    %%% others that should always be defined
    PREP.N_altern   = xData.N_altern;
    PREP.delta_f    = xData.delta_f;
    PREP.FA_sat     = xData.FA_sat;
    RAGE.DUR        = RAGE.TurboFac * RAGE.TRsub;

    %%% check some durations
    if RAGE.TR < round(RAGE.DUR+(max(PREP.N_BTR)-1)*max(PREP.BTR) + max(PREP.BTR_last),6); error('ERROR: RAGE.TR too short for some experiments'); end
    if PREP.delta_t < PREP.PW; error('ERROR: PREP.delta_t < PREP.PW'); end
    if PREP.BTR < round(max(PREP.Np)*PREP.delta_t,6); error('ERROR: PREP.BTR too short for some experiments'); end


    %% pre-compute quantities
    if ~xData.fixparx(1); PREP = func_compute_Wb(tiss,PREP,xData); end % T2b not fixed (should be rather slow)
    if ~xData.fixparx(2); PREP = func_compute_Wf(tiss,PREP,xData); end % T2f not fixed


    %% calculate ihMTR/MTdN/MTsN
    [OUT, MT0, out_readout] = func_qihMT_RAGE(tiss,PREP,RAGE);
end


function [OUT, MT0, out_readout] = func_qihMT_RAGE(tiss,PREP,RAGE)
    if ~isfield(PREP,'OutputType'), PREP.OutputType = 'ihMTR'; end % default output

    %% declare
    MTs         = zeros(1+2*tiss.Ncomp+1,numel(PREP.FA_sat));
    MTd         = zeros(1+2*tiss.Ncomp+1,numel(PREP.FA_sat));
    idx_diag    = 1:1+2*tiss.Ncomp+1:(1+2*tiss.Ncomp)^2;
    C           = zeros(1+2*tiss.Ncomp,1);
    out_readout = zeros(RAGE.TurboFac,1);


    %% Invariant relax & exchanges
    REX                     = blkdiag(-(tiss.R1f+tiss.R*sum(tiss.M0bs)), kron(eye(tiss.Ncomp), diag([-(tiss.R1b+tiss.R*tiss.M0f);0])));
    REX(2:2:end,1)          = tiss.R*tiss.M0bs;
    REX(1,2:2:end)          = tiss.R*tiss.M0f;
    REX(idx_diag(3:2:end))  = -1./tiss.T1Ds;
    C(1)                    = tiss.R1f*tiss.M0f;
    C(2:2:end)              = tiss.R1b*tiss.M0bs;
    REX_At                  = vertcat([REX C], zeros(1,tiss.Ncomp*2+2)); % tiss.Ncomp*2+2 = 1 Free Pool + 2* #Bound Pools + 1 additionnal (C)


    %% Invariant operators
    %%% PREP Xtilde operators
    Xt.delta_t  = func_expm( REX_At, PREP.delta_t-PREP.PW );% delta_t

    %%% RAGE Xtilde operators (pulses = instant. & no MT)
    Xt.EXC      = diag([cos(RAGE.FA) ones(1,1+tiss.Ncomp*2)]);  % RAGE EXC
    Xt.TRsub    = func_expm( REX_At, RAGE.TRsub );          % RAGE sub-TR ('echo spacing')

    readout     = Xt.TRsub*Xt.EXC;
    allreadouts = readout^RAGE.TurboFac;

    %% Varying operators Xtilde for PREP & RARE
    %%% PREP operators
    for ii = 1 : numel(PREP.FA_sat)
        PREP.DUR    = (PREP.N_BTR(ii)-1).*PREP.BTR(ii) + PREP.BTR_last(ii);
        
        Xt.RD_TR    = func_expm( REX_At, RAGE.TR-PREP.DUR-RAGE.DUR );
        Xt.PREP_MT0 = func_expm( REX_At, PREP.DUR ); % MT0
        Xt.BTR      = func_expm( REX_At, PREP.BTR(ii)-PREP.Np(ii)*PREP.delta_t ); % BTR
        Xt.BTR_last = func_expm( REX_At, PREP.BTR_last(ii)-PREP.Np(ii)*PREP.delta_t ); % BTR_last
        Xt.PW_P     = func_expm( vertcat([PREP.W_P(:,:,ii)+PREP.W_DS(:,:,ii)+REX C], zeros(1,tiss.Ncomp*2+2)), PREP.PW ); % pulse P
        Xt.PW_M     = func_expm( vertcat([PREP.W_M(:,:,ii)+PREP.W_DS(:,:,ii)+REX C], zeros(1,tiss.Ncomp*2+2)), PREP.PW ); % pulse M
        
        %%% final operators
        Xt.RAGE     = Xt.RD_TR*allreadouts; % the operators goes from last to first elements of the block
        if strcmp(PREP.OutputType,'ihMT') || strcmp(PREP.OutputType,'MTs')
            Xt.PREP_MTs(:,:,ii)     = (Xt.BTR_last*(Xt.delta_t*Xt.PW_P)^PREP.Np(ii))*((Xt.BTR*(Xt.delta_t*Xt.PW_P)^PREP.Np(ii))^(PREP.N_BTR(ii)-1));
        end
        if strcmp(PREP.DualType,'ALT') % ALT
            Xt.PREP_MTd(:,:,ii)     = (Xt.BTR_last*((Xt.delta_t*Xt.PW_M)^PREP.N_altern(ii)*(Xt.delta_t*Xt.PW_P)^PREP.N_altern(ii))^(PREP.Np(ii)/PREP.N_altern(ii)/2))* ...
                (Xt.BTR*((Xt.delta_t*Xt.PW_M)^PREP.N_altern(ii)*(Xt.delta_t*Xt.PW_P)^PREP.N_altern(ii))^(PREP.Np(ii)/PREP.N_altern(ii)/2))^(PREP.N_BTR(ii)-1);
        else                     % SM
            Xt.PW_SM(:,:,ii)        = func_expm( vertcat([PREP.W_SM(:,:,ii)+PREP.W_DS(:,:,ii)+REX C], zeros(1,tiss.Ncomp*2+2)), PREP.PW );
            Xt.PREP_MTd(:,:,ii)     = Xt.BTR_last*(Xt.delta_t*Xt.PW_SM(:,:,ii))^PREP.Np(ii)*(Xt.BTR*(Xt.delta_t*Xt.PW_SM(:,:,ii))^PREP.Np(ii))^(PREP.N_BTR(ii)-1);
        end
    end


    %% Compute steady-state ihMTR
    % array in steady-state is the eigenvector associated to eigenvalue=1 (last column here)
    % normalization: see https://github.com/mriphysics/ihMT_steadystate/blob/master/src/ssSPGR_ihMT_integrate.m#L121-L123

    % MT0
    [V,~]   = eig(Xt.PREP_MT0*Xt.RAGE,'vector');
    MT0     = V(1,end)/V(end,end);

    if strcmp(PREP.OutputType,'ihMT')
        
        % MTs/MTd
        for ii = 1 : numel(PREP.FA_sat)
            [V,~]       = eig(Xt.PREP_MTs(:,:,ii)*Xt.RAGE,'vector');
            MTs(:,ii)   = abs(V(:,end)/V(end,end));
            
            [V,~]       = eig(Xt.PREP_MTd(:,:,ii)*Xt.RAGE,'vector');
            MTd(:,ii)   = abs(V(:,end)/V(end,end));
        end

        % ihMT
        tmp = MTs(:,:) - MTd(:,:);
        OUT = tmp(1,:);

        out_readout(1) = tmp(1);
        for ii = 2 : RAGE.TurboFac
            tmp = readout * tmp;
            out_readout(ii,:) = tmp(1,:);
        end
        
    elseif strcmp(PREP.OutputType,'MTd')
        
        % MTd
        for ii = 1 : numel(PREP.FA_sat)
            [V,~]       = eig(Xt.PREP_MTd(:,:,ii)*Xt.RAGE,'vector');
            MTd(:,ii)   = abs(V(:,end)/V(end,end));
        end
        % MTd normalized
        OUT = MTd(1,:);
        
    elseif strcmp(PREP.OutputType,'MTs')
        
        % MTs
        for ii = 1 : numel(PREP.FA_sat)
            [V,~]       = eig(Xt.PREP_MTs(:,:,ii)*Xt.RAGE,'vector');
            MTs(:,ii)   = abs(V(:,end)/V(end,end));
        end
        % MTs normalized
        OUT = MTs(1,:);
        
    else
        error('Wrongly defined PREP.OutputType variable (should be ''ihMT'', ''MTd'' or ''MTs''')
    end
end

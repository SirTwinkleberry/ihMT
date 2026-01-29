% Simulation ihMTR from steady-state boost ihMT-prepared RAGE & fit ihMTsat
% Lucas SOUSTELLE 2022/04/28, CRMBM-CEMEREM Lab. UMR 7339, Marseille, France
% Adapted and slightly optimized by: Timothy ANDERSON, 2023/07/13
% Added support for ihMT export and ALT parameters in function call 2023/10/10
% Update: 2024/02/16 (Added more parameters in function call)
% 'addpath(genpath(toolpath));' seems not to work and creates a downstream error with func_compute_Wb

function ihMTfit_turbo(B1, T1f, T2f, R, M0bs, T1b, T1Ds, T2b, pw, dt, ess, tr, turbo, np, nb, btr, btrlast, fa_sat, fa_rages, dualType, N_altern, r_tukey, outPrefix)
    close all;
    
    parts = strsplit(mfilename('fullpath'), filesep);
    toolpath = string(strjoin(parts(1:end-1), filesep)) + filesep + 'Tools';
    
    addpath(genpath(toolpath));
    
    % Misc constants
    gamma                 = 267.513;      % gamma * 1e-6
    outPrefix             = convertCharsToStrings(outPrefix);
    if dualType == "SM", N_altern = 0; end

    fa_rages_nom          = pi .* fa_rages ./ 180;         % 6 deg
    fa_rages              = fa_rages_nom .* B1;
    
    % sampling parametrization
    [mesh_ess, mesh_fa_rages] = meshgrid(ess, fa_rages);
    
    len_fa_rages          = numel(fa_rages);
    len_ess               = numel(ess);
    
    % SNR                   = zeros(len_fa_rages, len_ess);
    % READOUTs              = zeros(len_fa_rages, len_ess, turbo);
    % READ_SATs             = zeros(turbo);
    
    R1f                   = 1 ./ T1f;
    fa_sat                = fa_sat .* B1;               % 80 deg * 10 = 800 deg
    
    
    phy_const             = 1 / (B1 * gamma);
    
    R1b                   = 1 ./ T1b;
    
    
    % fixed tissues & seq. parameters
    tiss.R                = R;
    tiss.T2b              = T2b;
    tiss.T1Ds             = T1Ds;
    tiss.M0bs             = M0bs;
    tiss.M0f              = 1.0;
    tiss.Ncomp            = numel(tiss.M0bs);
    tiss.dB1              = B1;
    
    tiss.T1               = T1f;          % 1450e-3     % s
    tiss.R1f              = R1f;          % 1/1450e-3;  % s
    tiss.T2f              = T2f;          % s
    tiss.R1b              = R1b;          % s
    
    PREP.DualType         = dualType;
    PREP.r_Tukey          = r_tukey;
    PREP.PW               = pw;
    PREP.pulse_fun        = @(t) func_TukeyFun_pulse(t, PREP.PW, PREP.r_Tukey);
    PREP.delta_t          = dt;
    PREP.N_BTR            = nb;
    PREP.BTR              = btr;
    PREP.BTR_last         = btrlast;
    PREP.Np               = np;
    
    RAGE.TurboFac         = turbo;

    xData.T1              = T1f;
    
    xData.FA_sat          = fa_sat;
    xData.Np              = np;
    xData.BTR             = btr;
    xData.N_BTR           = nb;
    xData.BTR_last        = btrlast;
    xData.N_altern        = N_altern;
    xData.delta_f         = 7e3;
    xData.fixparx         = ones(1, 9);
    
    ihMT                  = zeros(len_fa_rages, len_ess);
    MT0                   = zeros(len_fa_rages, len_ess);
    readout               = zeros(len_fa_rages, len_ess, turbo);
    % TRsub                 = zeros(len_fa_rages, len_ess, tiss.Ncomp * 2 + 2, tiss.Ncomp * 2 + 2);
    
    
    for jj = 1 : len_ess
        c_RAGE            = RAGE;
        c_RAGE.TRsub      = ess(jj);
        c_RAGE.TR         = ceil((tr + turbo * ess(jj)) * 1e3) * 1e-3;
        
        tmp_fa_rages      = fa_rages;
        
        c_xData           = xData;
        c_PREP            = PREP;
        
        % ihMT computation
        for ii = 1 : len_fa_rages
            
            % mono-compartimental model
            c_xData.fixedvals = [tiss.T2b tiss.T2f    tiss.R  tiss.R1b    tiss.R1f    tiss.M0bs   tiss.T1Ds   ];
            
            % simulation - if T2f fixed, pre-compute
            if c_xData.fixparx(1)
                c_PREP        = func_compute_Wb(tiss, c_PREP, c_xData);
            end
            
            if c_xData.fixparx(2)
                c_PREP        = func_compute_Wf(tiss, c_PREP, c_xData);
            end
                            
            % 'ihMT' / 'MTdN' / 'MTsN'
            c_PREP.OutputType = 'ihMT';
            c_xData.tiss      = tiss;
            c_xData.PREP      = c_PREP;
            c_xData.RAGE      = c_RAGE;
            c_xData.RAGE.FA   = tmp_fa_rages(ii);
            [ihMT(ii, jj), MT0(ii, jj), readout(ii, jj, :)] = wrapper_qihMT_RAGE([], c_xData);
        end

        if jj == 1
            B1rms_nom = c_PREP.pulse.w1RMS * sqrt(c_PREP.Np * c_PREP.PW / c_PREP.BTR) * phy_const;
            disp(['B1rms_nom = ' num2str(B1rms_nom) ' [μT]']);
        end
    end
    
    FA      = repmat(transpose(fa_rages), 1, len_ess);
    sinFA   = sin(FA);
    
    ihMT    = 2 * ihMT;
    ihMTr   = 100 * ihMT ./ MT0;
    SNR     = readout .* sinFA;
    
    % Exports
    save(outPrefix + "mesh_ess.mat", "mesh_ess");
    save(outPrefix + "mesh_fa_rages.mat", "mesh_fa_rages");
    save(outPrefix + "ihMTr.mat", "ihMTr");
    save(outPrefix + "ihMT.mat", "ihMT");
    save(outPrefix + "MT0.mat", "MT0");
    save(outPrefix + "SNR.mat", "SNR");

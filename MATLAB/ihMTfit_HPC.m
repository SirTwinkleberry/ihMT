% Simulation ihMTR from steady-state boost ihMT-prepared RAGE & fit ihMTsat
% Lucas SOUSTELLE 2022/04/28, CRMBM-CEMEREM Lab. UMR 7339, Marseille, France
% Adapted and slightly optimized by: Timothy ANDERSON, 2023/07/13
% Added support for ihMT export and ALT parameters in function call 2023/10/10
% Update: 2024/02/16 (Added more parameters in function call)
% 'addpath(genpath(toolpath));' seems not to work and creates a downstream error with func_compute_Wb

function [ihMT, MT0] = ihMTfit_HPC(dB1, T1fs, T2fs, R, M0bs, T1bs, T1Ds, T2b, pw, dt, es, tr, turbo, np, nb, btr, btrlast, fa_sat, fa_rage, FLAG_Sine_Modulation, N_altern, r_tukey, outPrefix, export)
    close all;
    
    parts = strsplit(mfilename('fullpath'), filesep);
    toolpath = string(strjoin(parts(1 : end - 1), filesep)) + filesep + 'Tools';
    
    addpath(genpath(toolpath));
    
    % Misc constants
    outPrefix             = convertCharsToStrings(outPrefix);
    
    % sampling parametrization
    len_dB1               = numel(dB1);
    len_T1fs              = numel(T1fs);
    
    
    R1fs                  = 1 ./ T1fs;
    fa_rages              = 0.0174532925199432 .* fa_rage .* dB1;  % pi / 180 ~= 0.0174532925199432
    fa_sats               = fa_sat .* dB1;
    
    R1bs                  = 1 ./ T1bs;
    
    % fixed tissues & seq. parameters
    tiss.R                = R;
    tiss.T2b              = T2b;
    tiss.T1Ds             = T1Ds;
    tiss.M0bs             = M0bs;
    tiss.M0f              = 1.0;
    tiss.Ncomp            = numel(tiss.M0bs);
    
    PREP.FLAG_Sine_Modulation = FLAG_Sine_Modulation;
    PREP.r_Tukey          = r_tukey;
    PREP.PW               = pw;
    PREP.pulse_fun        = @(t) func_TukeyFun_pulse(t, PREP.PW, PREP.r_Tukey);
    PREP.delta_t          = dt;
    PREP.N_BTR            = nb;
    PREP.BTR              = btr;
    PREP.BTR_last         = btrlast;
    PREP.Np               = np;

    RAGE.TRsub            = es;
    RAGE.TR               = tr;
    RAGE.TurboFac         = turbo;
    
    xData.Np              = np;
    xData.BTR             = btr;
    xData.N_BTR           = nb;
    xData.BTR_last        = btrlast;
    xData.N_altern        = N_altern;
    xData.delta_f         = 7e3;
    % xData.fixparx         = ones(1, 9);
    
    ihMT                  = zeros(len_dB1, len_T1fs);
    MT0                   = zeros(len_dB1, len_T1fs);

    for jj = 1 : len_T1fs
        % fixed tissues & seq. parameters
        tiss.T1         = T1fs(jj);          % 1450e-3     % s
        tiss.R1f        = R1fs(jj);          % 1/1450e-3;  % s
        tiss.T2f        = T2fs(jj);          % s
        tiss.R1b        = R1bs(jj);          % s

        xData.T1        = T1fs(jj);

        % mono-compartimental model
        xData.fixedvals = [tiss.T2b tiss.T2f    tiss.R  tiss.R1b    tiss.R1f    tiss.M0bs   tiss.T1Ds];

        % ihMT computation
        for ii = 1 : len_dB1
            tiss.dB1        = dB1(ii);
            xData.FA_sat    = fa_sats(ii);

            xData.PREP      = func_compute_Wf(tiss, func_compute_Wb(tiss, PREP, xData), xData);

            xData.tiss      = tiss;
            xData.RAGE      = RAGE;
            xData.RAGE.FA   = fa_rages(ii);
            [ihMT(ii, jj), MT0(ii, jj)] = wrapper_qihMT_RAGE_HPC(xData);
        end
    end


    % Exports
    if export
        save(outPrefix + "ihMT.mat", "ihMT");
        save(outPrefix + "MT0.mat", "MT0");
    end
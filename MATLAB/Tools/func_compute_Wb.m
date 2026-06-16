function PREP = func_compute_Wb(tiss,PREP,xData)
if ~isfield(xData,'FA_sat'), xData.FA_sat = PREP.FA_sat; xData.delta_f = PREP.delta_f; end
    
% Optimized so as to not recompute similar Wb-related quantities (FAsat/deltaf)
array_FAsat_deltaf = [xData.FA_sat ; xData.delta_f]';
[xData.FAsat_delta_f, ~, idf] = unique(array_FAsat_deltaf,'rows','stable');

PREP.W_P = zeros(1+2*tiss.Ncomp,1+2*tiss.Ncomp,numel(idf));
PREP.W_M = PREP.W_P; PREP.W_SM = PREP.W_P;
for ii = 1 : size(xData.FAsat_delta_f,1)
    idx_fill    = find(idf == ii);
    tmp_FA_sat  = xData.FAsat_delta_f(ii,1);
    tmp_delta_f = xData.FAsat_delta_f(ii,2);
    PREP.pulse  = func_compute_pulse(PREP.pulse_fun,PREP.PW,tmp_FA_sat,tmp_delta_f);
    
    % T2b-related
    tiss.D  = 1/( sqrt(15) * tiss.T2b );
    Wb      = func_computeW(PREP.pulse.w1RMS,tmp_delta_f,tiss.T2b,'SuperLorentzian');
%     Wb      = func_computeW_mex(PREP.pulse.w1RMS,tmp_delta_f,tiss.T2b,'SuperLorentzian');
    W_P     = blkdiag(0,kron(eye(tiss.Ncomp), ...
                                [-Wb,                            Wb*2*pi*tmp_delta_f ; ...
                                  Wb*2*pi*tmp_delta_f/tiss.D^2, -Wb*(2*pi*tmp_delta_f/tiss.D)^2]));
    W_M     = blkdiag(0,kron(eye(tiss.Ncomp), ...
                            [-Wb,                           -Wb*2*pi*tmp_delta_f ; ...
                             -Wb*2*pi*tmp_delta_f/tiss.D^2, -Wb*(2*pi*tmp_delta_f/tiss.D)^2]));

    W_SM    = blkdiag(0,kron(eye(tiss.Ncomp), ...
                            diag([-Wb ; -Wb*(2*pi*tmp_delta_f/tiss.D)^2])));
    PREP.W_P(:,:,idx_fill) = repmat(W_P,[1 1 numel(idx_fill)]);
    PREP.W_M(:,:,idx_fill) = repmat(W_M,[1 1 numel(idx_fill)]);
    PREP.W_SM(:,:,idx_fill) = repmat(W_SM,[1 1 numel(idx_fill)]);
end

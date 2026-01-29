function PREP = func_compute_Wf(tiss,PREP,xData)
if ~isfield(xData,'FA_sat'), xData.FA_sat = PREP.FA_sat; xData.delta_f = PREP.delta_f; end

% Optimized so as to not recompute similar Wf-related quantities (FAsat/deltaf)
array_FAsat_deltaf = [xData.FA_sat ; xData.delta_f]';
[xData.FAsat_delta_f, ~, idf] = unique(array_FAsat_deltaf,'rows','stable');

PREP.W_DS = zeros(1 + 2 * tiss.Ncomp,1 + 2 * tiss.Ncomp, numel(idf));
for ii = 1 : size(xData.FAsat_delta_f,1)
    idx_fill    = find(idf == ii);
    tmp_FA_sat  = xData.FAsat_delta_f(ii,1);
    tmp_delta_f = xData.FAsat_delta_f(ii,2);
    PREP.pulse  = func_compute_pulse(PREP.pulse_fun,PREP.PW,tmp_FA_sat,tmp_delta_f);
    
    % T2f-related
    Wf      = func_computeW(PREP.pulse.w1RMS,tmp_delta_f,tiss.T2f,'Lorentzian');
    W_DS    = diag([-Wf,zeros(1,2*tiss.Ncomp)]);
    PREP.W_DS(:,:,idx_fill) = repmat(W_DS,[1 1 numel(idx_fill)]);
end

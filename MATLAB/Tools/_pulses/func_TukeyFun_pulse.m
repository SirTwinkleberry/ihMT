function pulse = func_TukeyFun_pulse(t,tau,r)
% see https://git.bitbybyte.fi/publicgroup/quantumwheelpublic/blob/c99f7f912244379e9d5ed2bbd41f976578efcda1/QuantumWheel/Assets/Plugins/QuantumWheel/.Python/scipy/signal/windows/windows.py
% inputs:
%   r: tukey window parmameter
%   t: timespan
%   tau: pulse duration
% output: 
%   pulse function handle

if 0 <= t/tau && t/tau < r/2
    pulse = 0.5 * ( 1 + cos(pi*(-1+2*t/r/tau)) );
elseif r/2 <= t/tau && t/tau < 1-r/2
    pulse = 1;
elseif 1-r/2 <= t/tau && t/tau <= 1
    pulse = 0.5 * ( 1 + cos(pi*(-2/r+1+2*t/r/tau)) );
end

pulse((t < 0 | t>tau)) = 0;
return



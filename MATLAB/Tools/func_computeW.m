function W = func_computeW(w1RMS,delta_f,T2,LINESHAPE)

switch LINESHAPE
    case 'SuperLorentzian'
        if abs(delta_f) < 1000; error('|delta_f| < 1 kHz, better use Pampel''s implementation (see ''SuperLorentzian_Pampel''). Exiting ...'); end
        fun = @(u) sqrt(2/pi) .* (T2./abs(3*u.^2-1)) .* exp(-2*((2*pi .* delta_f .* T2)./(3*u.^2-1)).^2);
        G = quadgk(fun, 0, 1);
        
    case 'SuperLorentzian_Pampel'
        G = sqrt(1./(2*pi))*quadgk(@(theta)func_SphericalLineShape(delta_f,T2,theta),0,pi/2);

    case 'Lorentzian'
        G = (T2/pi)/(1+(2*pi*delta_f*T2)^2);
        
    case 'Gaussian'
        G = sqrt(1/(2*pi))*T2*exp(-((2*pi*delta_f* T2)^2)/2);
        
    otherwise
        error('Unrecognized ''%s'' lineshape',LINESHAPE);
end
    
W = pi * w1RMS^2 * G;
end


function dg = func_SphericalLineShape(delta,T2,theta)
% This program set up a function for Spherical lineshape integration
% include neighboors contribution to remove singularity at the magic angle
% see Pampel et al. NeuroImage 114 (2015) 136–146
T2neighboors=1/31.4;  % 10000000 would mean virtually no effect of T2neighboors
T2=2*T2./abs(3.*cos(theta).^2-1);
T2eff=1./sqrt(1./(T2).^2+1/(T2neighboors).^2);

dg = sin(theta).*(T2eff).*exp(-1/2.*(2*pi*delta.*T2eff).^2);

end
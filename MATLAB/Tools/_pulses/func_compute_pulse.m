function pulse = func_compute_pulse(pulse_fun,tau,FAsat,delta)

gamma   = 267.513 * 1e6;                    % rad/s/T
pulse.norm_int          = integral(@(t) (pulse_fun(t)),0,tau,'ArrayValued',true)/tau;  			
pulse.norm_powerint     = integral(@(t) (pulse_fun(t).^2),0,tau,'ArrayValued',true)/tau;

pulse.FA                = FAsat;
pulse.tau               = tau;
pulse.delta             = delta;
pulse.B1peak            = FAsat*pi/180 / ( gamma * integral(@(t) (pulse_fun(t)),0,tau,'ArrayValued',true) );
pulse.B1                = @(t) pulse_fun(t) * pulse.B1peak; % T
pulse.Omega1            = @(t) (gamma *pulse.B1(t)); % rad.s-1
pulse.Omega1sq          = @(t) (gamma *pulse.B1(t)).^2; 

pulse.w1RMS             = sqrt( integral(@(t) (pulse.Omega1sq(t)),0,tau,'ArrayValued',true)/tau );



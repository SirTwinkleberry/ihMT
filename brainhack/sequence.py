from .pulses import Pulse

from numpy import round
from enum import Flag, auto


class Modulation(Flag):
    CM = auto()
    ALT = auto()
    BP = CM | ALT


class Sequence():
    modulation: Modulation

    pulse: Pulse

    N_pulsePerOffset: int
    N_pulse: int
    N_burst: int
    N_adc: int

    readout_flipAngle: float

    dt_interPulse: float
    dt_LastBurst: float
    TR_burst: float
    ES: float
    TR: float
    duration_readout: float
    duration_preparation: float
    duration_recovery: float

    def __init__(self, modulation: Modulation, pulse: Pulse, N_pulsePerOffset: int, N_pulse: int, N_burst: int, N_adc: int, dt_interPulse: float, TR_burst: float, dt_lastBurst: float, ES: float, TR: float, readout_flipAngle: float):
        """_summary_

        Parameters
        ----------
        modulation : Modulation
            _Flag(s) corresponding to the type of MT RF modulation_
        pulse : Pulse
            _MT RF pulse_
        N_pulsePerOffset : int
            _aka `N_altern`, `N_switch`, `N_tauSwitch`, ..._
        N_pulse : int
            _description_
        N_burst : int
            _description_
        N_adc : int
            _aka `turbo_factor`_
        dt_interPulse : float
            _aka `dt`_
        TR_burst : float
            _aka `BTR`_
        dt_lastBurst : float
            _aka `BTR_last`_
        ES : float
            _Echo spacing_
        TR : float
            _aka `TR_RAGE`_
        readout_flipAngle : float
            _aka `FA_RAGE`, in degrees and not in radians this time_

        Raises
        ------
        RuntimeError
            _description_
        RuntimeError
            _description_
        RuntimeError
            _description_
        """
        self.modulation = modulation

        self.pulse = pulse

        self.N_pulsePerOffset = N_pulsePerOffset
        self.N_pulse = N_pulse
        self.N_burst = N_burst
        self.N_adc = N_adc

        self.dt_interPulse = dt_interPulse
        self.dt_LastBurst = dt_lastBurst
        self.TR_burst = TR_burst
        self.es = ES
        self.tr = TR

        self.duration_readout = N_adc * ES
        self.duration_preparation = (N_burst - 1) * TR_burst + dt_lastBurst
        self.duration_recovery = TR - self.duration_readout - self.duration_preparation

        self.readout_flipAngle = readout_flipAngle

        if TR < round(self.duration_readout + self.duration_preparation, 6):
            raise RuntimeError('TR < round(N_adc * ES + (N_burst - 1) * TR_burst + dt_lastBurst, 6)')

        if dt_interPulse < pulse.duration:
            raise RuntimeError('dt_interPulse < pulse.duration')

        if TR_burst < round(N_pulse * dt_interPulse, 6):
            raise RuntimeError('TR_burst < round(N_pulse * dt_interPulse, 6)')

        if .5 * N_pulse % N_pulsePerOffset != 0:
            raise RuntimeError('.5 * N_pulse % N_pulsePerOffset != 0')

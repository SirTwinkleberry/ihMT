from logging import getLogger, NullHandler
from numpy import round
from typing import Any
from operator import lt

from brainhack.meta import _Event, Signal, check_value_is_valid
from brainhack.pulse import Pulse

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug('`sequence` module loaded successfully')


class Sequence(_Event):
    _signal: Signal

    _pulse: Pulse

    _N_pulsePerOffset: int
    _N_pulse: int
    _N_burst: int
    _N_adc: int

    _readout_flipAngle: float

    _dt_interPulse: float
    _dt_lastBurst: float
    _TR_burst: float
    _es: float
    _tr: float
    _duration_readout: float
    _duration_preparation: float
    _duration_recovery: float

    _classAttributes: tuple[str] = ('signal', 'pulse', 'N_pulsePerOffset', 'N_pulse', 'N_burst', 'N_adc', 'N_dummyADC', 'readout_flipAngle', 'dt_interPulse', 'dt_lastBurst', 'TR_burst', 'es', 'tr', 'duration_readout', 'duration_preparation', 'duration_recovery')

    def __init__(self, signal: Signal, pulse: Pulse, N_pulsePerOffset: int, N_pulse: int, N_burst: int, N_adc: int, N_dummyADC: int, dt_interPulse: float, TR_burst: float, dt_lastBurst: float, es: float, tr: float, readout_flipAngle: float, *args: Any, **kwargs: Any):
        """_summary_

        Parameters
        ----------
        signal : Signal
            _Flag(s) corresponding to the type of MT RF signal_
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
        N_dummyADC : int
            _Number of dummy readout echoes_
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
        ValueError
            _description_
        ValueError
            _description_
        ValueError
            _description_
        ValueError
            _description_
        """
        self.signal = signal

        self.pulse = pulse
        self.readout_flipAngle = readout_flipAngle

        self.N_pulsePerOffset = N_pulsePerOffset
        self.N_pulse = N_pulse
        self.N_burst = N_burst
        self.dt_interPulse = dt_interPulse
        self.dt_lastBurst = dt_lastBurst
        self.TR_burst = TR_burst

        self.es = es
        self.N_adc = N_adc
        self.N_dummyADC = N_dummyADC

        self.tr = tr

        self.onChange('signal', [self._check_against_N_pulse_multiplicity])

        self.onChange('pulse', [lambda: self._reset_computed_attributes(['duration_preparation', 'duration_recovery']), self._check_against_pulse_duration])

        self.onChange('N_pulsePerOffset', [self._check_against_N_pulse_multiplicity])
        self.onChange('N_pulse', [lambda: self._reset_computed_attributes(['duration_readout', 'duration_recovery']), self._check_against_N_pulse_multiplicity, self._check_against_tr_burst, self._check_against_tr])
        self.onChange('N_burst', [lambda: self._reset_computed_attributes(['duration_readout', 'duration_recovery']), self._check_against_tr])
        self.onChange('dt_interPulse', [lambda: self._reset_computed_attributes(['duration_readout', 'duration_recovery']), self._check_against_pulse_duration, self._check_against_tr_burst, self._check_against_tr])
        self.onChange('dt_lastBurst', [lambda: self._reset_computed_attributes(['duration_readout', 'duration_recovery']), self._check_against_tr])
        self.onChange('TR_burst', [lambda: self._reset_computed_attributes(['duration_readout', 'duration_recovery']), self._check_against_tr_burst, self._check_against_tr])

        self.onChange('es', [lambda: self._reset_computed_attributes(['duration_readout', 'duration_recovery']), self._check_against_tr])
        self.onChange('N_adc', [lambda: self._reset_computed_attributes(['duration_readout', 'duration_recovery']), self._check_against_N_dummyADC, self._check_against_tr])
        self.onChange('N_dummyADC', [self._check_against_N_dummyADC])

        self.onChange('tr', [lambda: self._reset_computed_attributes(['duration_recovery']), self._check_against_tr])

        self._check_against_tr()
        self._check_against_tr_burst()
        self._check_against_N_pulse_multiplicity()
        self._check_against_pulse_duration()
        self._check_against_N_dummyADC()

    def copy(self) -> Sequence:
        return Sequence(self.signal, self.pulse.copy(), self.N_pulsePerOffset, self.N_pulse, self.N_burst, self.N_adc, self.N_dummyADC, self.dt_interPulse, self.TR_burst, self.dt_lastBurst, self.es, self.tr, self.readout_flipAngle)

    def _check_against_tr(self):
        if (hasattr(self, '_N_adc') and hasattr(self, '_es')  # Readout parameters
            and hasattr(self, '_N_burst') and hasattr(self, '_TR_burst') and hasattr(self, '_dt_lastBurst')  # Prep parameters
                and hasattr(self, '_tr')):
            if self.tr < round(self.duration_readout + self.duration_preparation, 6):
                error = 'TR < round(N_adc * ES + (N_burst - 1) * TR_burst + dt_lastBurst, 6)'
                raise ValueError(error)

    def _check_against_tr_burst(self):
        if hasattr(self, '_TR_burst') and hasattr(self, '_N_pulse') and hasattr(self, '_dt_interPulse'):
            if self.TR_burst < round(self.N_pulse * self.dt_interPulse, 6):
                error = 'TR_burst < round(N_pulse * dt_interPulse, 6)'
                logger.critical(error)
                raise ValueError(error)

    def _check_against_N_pulse_multiplicity(self):
        if hasattr(self, '_N_pulse') and hasattr(self, '_N_pulsePerOffset') and hasattr(self, '_signal'):
            if (Signal.MTd_ALT in self.signal) and (((.5 * self.N_pulse) % self.N_pulsePerOffset) != 0):
                error = '.5 * N_pulse % N_pulsePerOffset != 0'
                logger.critical(error)
                raise ValueError(error)

    def _check_against_pulse_duration(self):
        if hasattr(self, '_dt_interPulse') and hasattr(self, '_pulse'):
            if self.dt_interPulse < self.pulse.duration:
                error = 'dt_interPulse < pulse.duration'
                logger.critical(error)
                raise ValueError(error)

    def _check_against_N_dummyADC(self):
        if hasattr(self, '_N_dummyADC') and hasattr(self, '_N_adc'):
            if self.N_adc < self.N_dummyADC:
                error = 'N_adc < N_dummyADC'
                logger.critical(error)
                raise ValueError(error)

    #####
    # BELOW: property getters and setters
    #####
    @property
    def signal(self):
        return self._signal

    @signal.setter
    def signal(self, val: Signal):
        if type(val) is not Signal:
            error = f"Value {repr(val)} is not a signal flag of type `Signal`."
            logger.critical(error)
            raise TypeError(error)
        self._signal = val
        self._changed('signal')

    @property
    def pulse(self):
        return self._pulse

    @pulse.setter
    def pulse(self, val: Pulse):
        self._pulse = val
        self._pulse.onChange('duration', [lambda: self._reset_computed_attributes(['duration_preparation', 'duration_recovery']), self._check_against_pulse_duration])
        self._changed('pulse')

    @property
    def N_pulsePerOffset(self):
        return self._N_pulsePerOffset

    @N_pulsePerOffset.setter
    def N_pulsePerOffset(self, val: int):
        check_value_is_valid(self, val, int, [(lt, 0)], 'N_pulsePerOffset')
        self._N_pulsePerOffset = val
        self._changed('N_pulsePerOffset')

    @property
    def N_pulse(self):
        return self._N_pulse

    @N_pulse.setter
    def N_pulse(self, val: int):
        check_value_is_valid(self, val, int, [(lt, 0)], 'N_pulse')
        self._N_pulse = int(val)
        self._changed('N_pulse')

    @property
    def N_burst(self):
        return self._N_burst

    @N_burst.setter
    def N_burst(self, val: int):
        check_value_is_valid(self, val, int, [(lt, 0)], 'N_burst')
        self._N_burst = int(val)
        self._changed('N_burst')

    @property
    def N_adc(self):
        return self._N_adc

    @N_adc.setter
    def N_adc(self, val: int):
        check_value_is_valid(self, val, int, [(lt, 0)], 'N_adc')
        self._N_adc = int(val)
        self._changed('N_adc')

    @property
    def N_dummyADC(self):
        return self._N_dummyADC

    @N_dummyADC.setter
    def N_dummyADC(self, val: int):
        check_value_is_valid(self, val, int, [(lt, 0)], 'N_dummyADC')
        self._N_dummyADC = int(val)
        self._changed('N_dummyADC')

    @property
    def readout_flipAngle(self):
        return self._readout_flipAngle

    @readout_flipAngle.setter
    def readout_flipAngle(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0)], 'readout_flipAngle')
        self._readout_flipAngle = float(val)
        self._changed('readout_flipAngle')

    @property
    def dt_interPulse(self):
        return self._dt_interPulse

    @dt_interPulse.setter
    def dt_interPulse(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0)], 'dt_interPulse')
        self._dt_interPulse = float(val)
        self._changed('dt_interPulse')

    @property
    def dt_lastBurst(self):
        return self._dt_lastBurst

    @dt_lastBurst.setter
    def dt_lastBurst(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0)], 'dt_lastBurst')
        self._dt_lastBurst = float(val)
        self._changed('dt_lastBurst')

    @property
    def TR_burst(self):
        return self._TR_burst

    @TR_burst.setter
    def TR_burst(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0)], 'TR_burst')
        self._TR_burst = float(val)
        self._changed('TR_burst')

    @property
    def es(self):
        return self._es

    @es.setter
    def es(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0)], 'es')
        self._es = float(val)
        self._changed('es')

    @property
    def tr(self):
        return self._tr

    @tr.setter
    def tr(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0)], 'tr')
        self._tr = float(val)
        self._changed('tr')

    @property
    def duration_readout(self):
        if not hasattr(self, '_duration_readout'):
            self.duration_readout = self.N_adc * self.es
        return self._duration_readout

    @duration_readout.setter
    def duration_readout(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0)], 'duration_readout')
        self._duration_readout = float(val)
        self._changed('duration_readout')

    @property
    def duration_preparation(self):
        if not hasattr(self, '_duration_preparation'):
            self.duration_preparation = (self.N_burst - 1) * self.TR_burst + self.N_pulse * self.dt_interPulse + self.dt_lastBurst
        return self._duration_preparation

    @duration_preparation.setter
    def duration_preparation(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0)], 'duration_preparation')
        self._duration_preparation = float(val)
        self._changed('duration_preparation')

    @property
    def duration_recovery(self):
        if not hasattr(self, '_duration_recovery'):
            self.duration_recovery = self.tr - self.duration_readout - self.duration_preparation
        return self._duration_recovery

    @duration_recovery.setter
    def duration_recovery(self, val: float):
        check_value_is_valid(self, val, float, [(lt, 0)], 'duration_recovery')
        self._duration_recovery = float(val)
        self._changed('duration_recovery')

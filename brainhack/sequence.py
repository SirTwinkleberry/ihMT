from brainhack.pulse import Pulse

from numpy import round
from enum import Flag, auto
from typing import Any


class Modulation(Flag):
    CM = auto()
    ALT = auto()
    BP = CM | ALT


class Sequence():
    __modulation: Modulation

    __pulse: Pulse

    __N_pulsePerOffset: int
    __N_pulse: int
    __N_burst: int
    __N_adc: int

    __readout_flipAngle: float

    __dt_interPulse: float
    __dt_lastBurst: float
    __TR_burst: float
    __es: float
    __tr: float
    __duration_readout: float
    __duration_preparation: float
    __duration_recovery: float

    def __init__(self, modulation: Modulation, pulse: Pulse, N_pulsePerOffset: int, N_pulse: int, N_burst: int, N_adc: int, dt_interPulse: float, TR_burst: float, dt_lastBurst: float, es: float, tr: float, readout_flipAngle: float):
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
        ValueError
            _description_
        ValueError
            _description_
        ValueError
            _description_
        ValueError
            _description_
        """
        self.modulation = modulation

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

        self.tr = tr

    def check_against_tr(self):
        if (hasattr(self, 'N_adc') and hasattr(self, 'es')  # Readout parameters
            and hasattr(self, 'N_burst') and hasattr(self, 'TR_burst') and hasattr(self, 'dt_lastBurst')  # Prep parameters
                and hasattr(self, 'tr')):
            if self.tr < round(self.duration_readout + self.duration_preparation, 6):
                raise ValueError('TR < round(N_adc * ES + (N_burst - 1) * TR_burst + dt_lastBurst, 6)')

    def check_against_tr_burst(self):
        if hasattr(self, 'TR_burst') and hasattr(self, 'N_pulse') and hasattr(self, 'dt_interPulse'):
            if self.TR_burst < round(self.N_pulse * self.dt_interPulse, 6):
                raise ValueError('TR_burst < round(N_pulse * dt_interPulse, 6)')

    def check_against_N_pulse_multiplicity(self):
        if hasattr(self, 'N_pulse') and hasattr(self, 'N_pulsePerOffset'):
            if .5 * self.N_pulse % self.N_pulsePerOffset != 0:
                raise ValueError('.5 * N_pulse % N_pulsePerOffset != 0')

    def check_against_pulse_duration(self):
        if hasattr(self, 'dt_interPulse') and hasattr(self, 'pulse'):
            if self.dt_interPulse < self.pulse.duration:
                raise ValueError('dt_interPulse < pulse.duration')

    @staticmethod
    def check_type(val_to_check: Any, type_to_check: type, attribute_name: str):
        if type_to_check(val_to_check) != val_to_check:
            raise ValueError(f'`{attribute_name}` must be safely castable to integer. Received: {repr(val_to_check)}.')
        if val_to_check < 0:
            raise ValueError(f'`{attribute_name}` cannot be negative. Received: {repr(val_to_check)}.')

    def resetComputedAttributes_Recovery(self):
        if hasattr(self, 'duration_recovery'): del self.duration_recovery  # noqa: E701

    def resetComputedAttributes_Preparation(self):
        if hasattr(self, 'duration_preparation'): del self.duration_preparation  # noqa: E701
        self.resetComputedAttributes_Recovery()

    def resetComputedAttributes_Readout(self):
        if hasattr(self, 'duration_readout'): del self.duration_readout  # noqa: E701
        self.resetComputedAttributes_Recovery()

    #####
    # BELOW: property getters and setters
    #####
    @property
    def modulation(self):
        return self.__modulation

    @modulation.setter
    def modulation(self, val: Modulation):
        if type(val) is not Modulation:
            raise TypeError(f"Value {repr(val)} is not a modulation flag of type `Modulation`.")
        self.__modulation = val

    @property
    def pulse(self):
        return self.__pulse

    @pulse.setter
    def pulse(self, val: Pulse):
        self.__pulse = val
        self.resetComputedAttributes_Preparation()
        self.check_against_pulse_duration()

    @property
    def N_pulsePerOffset(self):
        return self.__N_pulsePerOffset

    @N_pulsePerOffset.setter
    def N_pulsePerOffset(self, val: int):
        self.check_type(val, int, 'N_pulsePerOffset')
        self.__N_pulsePerOffset = val
        self.check_against_N_pulse_multiplicity()

    @property
    def N_pulse(self):
        return self.__N_pulse

    @N_pulse.setter
    def N_pulse(self, val: int):
        self.check_type(val, int, 'N_pulse')
        self.__N_pulse = int(val)
        self.resetComputedAttributes_Preparation()
        self.check_against_N_pulse_multiplicity()
        self.check_against_tr_burst()
        self.check_against_tr()

    @property
    def N_burst(self):
        return self.__N_burst

    @N_burst.setter
    def N_burst(self, val: int):
        self.check_type(val, int, 'N_burst')
        self.__N_burst = int(val)
        self.resetComputedAttributes_Preparation()
        self.check_against_tr()

    @property
    def N_adc(self):
        return self.__N_adc

    @N_adc.setter
    def N_adc(self, val: int):
        self.check_type(val, int, 'N_adc')
        self.__N_adc = int(val)
        self.resetComputedAttributes_Readout()
        self.check_against_tr()

    @property
    def readout_flipAngle(self):
        return self.__readout_flipAngle

    @readout_flipAngle.setter
    def readout_flipAngle(self, val: float):
        self.check_type(val, float, 'readout_flipAngle')
        self.__readout_flipAngle = float(val)

    @property
    def dt_interPulse(self):
        return self.__dt_interPulse

    @dt_interPulse.setter
    def dt_interPulse(self, val: float):
        self.check_type(val, float, 'dt_interPulse')
        self.__dt_interPulse = float(val)
        self.resetComputedAttributes_Preparation()
        self.check_against_pulse_duration()
        self.check_against_tr_burst()
        self.check_against_tr()

    @property
    def dt_lastBurst(self):
        return self.__dt_lastBurst

    @dt_lastBurst.setter
    def dt_lastBurst(self, val: float):
        self.check_type(val, float, 'dt_lastBurst')
        self.__dt_lastBurst = float(val)
        self.resetComputedAttributes_Preparation()
        self.check_against_tr()

    @property
    def TR_burst(self):
        return self.__TR_burst

    @TR_burst.setter
    def TR_burst(self, val: float):
        self.check_type(val, float, 'TR_burst')
        self.__TR_burst = float(val)
        self.resetComputedAttributes_Preparation()
        self.check_against_tr_burst()
        self.check_against_tr()

    @property
    def es(self):
        return self.__es

    @es.setter
    def es(self, val: float):
        self.check_type(val, float, 'es')
        self.__es = float(val)
        self.resetComputedAttributes_Readout()
        self.check_against_tr()

    @property
    def tr(self):
        return self.__tr

    @tr.setter
    def tr(self, val: float):
        self.check_type(val, float, 'tr')
        self.__tr = float(val)
        self.resetComputedAttributes_Recovery()
        self.check_against_tr()

    @property
    def duration_readout(self):
        if not hasattr(self, '__duration_readout'):
            self.__duration_readout = self.N_adc * self.es
        return self.__duration_readout

    @duration_readout.setter
    def duration_readout(self, val: float):
        self.check_type(val, float, 'duration_readout')
        self.__duration_readout = float(val)

    @duration_readout.deleter
    def duration_readout(self):
        del self.__duration_readout

    @property
    def duration_preparation(self):
        if not hasattr(self, '__duration_preparation'):
            self.__duration_preparation = (self.N_burst - 1) * self.TR_burst + self.N_pulse * self.dt_interPulse + self.dt_lastBurst
        return self.__duration_preparation

    @duration_preparation.setter
    def duration_preparation(self, val: float):
        self.check_type(val, float, 'duration_preparation')
        self.__duration_preparation = float(val)

    @duration_preparation.deleter
    def duration_preparation(self):
        del self.__duration_preparation

    @property
    def duration_recovery(self):
        if not hasattr(self, '__duration_recovery'):
            self.__duration_recovery = self.tr - self.duration_readout - self.duration_preparation
        return self.__duration_recovery

    @duration_recovery.setter
    def duration_recovery(self, val: float):
        self.check_type(val, float, 'duration_recovery')
        self.__duration_recovery = float(val)

    @duration_recovery.deleter
    def duration_recovery(self):
        del self.__duration_recovery

from brainhack.sequence import Modulation, Sequence
from brainhack.pulses import Pulse

from unittest import TestCase

DEFAULT: dict[str, bool | int | float | str] = {
    'B1rel': 1,
    'M0a': 1,
    'T1f': 1,
    'T2f': 0.1,
    'R': 10,
    'M0b': 0.1,
    'T1b': 1,
    'T1D': 1.0e-2,
    'T2b': 1.0e-5,
    'pw': 1.0e-3,
    'dt': 1.5e-3,
    'es': 6.0e-3,
    'tr': 3,
    'turbo': 80,
    'np': 4,
    'nb': 10,
    'btr': 1.0e-1,
    'btrlast': 1.0e-3,
    'fa_sat': 200,
    'fa_rage': 5,
    'FLAG_Sine_Modulation': "BP",
    'N_altern': 1,
    'r_tukey': 0.3,
    'outPrefix': './output/',
    'export': True,
    'offset': 7000,
}


class TestModulation(TestCase):
    def test_CM(self):
        ...

    def test_ALT(self):
        ...

    def test_BP(self):
        ...


class TestSequence(TestCase):
    mock_Pulse = Pulse
    mock_Pulse.duration = 1e-3

    mock_Sequence = Sequence
    mock_Sequence.modulation = Modulation.BP
    mock_Sequence.pulse = Pulse(mock_Pulse)
    mock_Sequence.N_pulsePerOffset = int(DEFAULT['N_altern'])
    mock_Sequence.N_pulse = int(DEFAULT['np'])
    mock_Sequence.N_burst = int(DEFAULT['nb'])
    mock_Sequence.N_adc = int(DEFAULT['turbo'])
    mock_Sequence.dt_interPulse = float(DEFAULT['dt'])
    mock_Sequence.dt_LastBurst = float(DEFAULT['btrlast'])
    mock_Sequence.TR_burst = float(DEFAULT['btr'])
    mock_Sequence.es = float(DEFAULT['es'])
    mock_Sequence.tr = float(DEFAULT['tr'])
    mock_Sequence.duration_readout = float(DEFAULT['turbo']) * float(DEFAULT['es'])
    mock_Sequence.duration_preparation = (float(DEFAULT['nb']) - 1) * float(DEFAULT['btr']) + float(DEFAULT['btrlast'])
    mock_Sequence.duration_recovery = float(DEFAULT['tr']) - (float(DEFAULT['turbo']) * float(DEFAULT['es'])) - ((float(DEFAULT['nb']) - 1) * float(DEFAULT['btr']) + float(DEFAULT['btrlast']))
    mock_Sequence.readout_flipAngle = float(DEFAULT['fa_rage'])

    def test___init__modulation_CM(self):
        ...

    def test___init__modulation_ALT(self):
        ...

    def test___init__modulation_BP(self):
        ...

    def test___init__pulse(self):
        ...

    def test___init__N_pulsePerOffset(self):
        ...

    def test___init__N_pulse(self):
        ...

    def test___init__N_burst(self):
        ...

    def test___init__N_adc(self):
        ...

    def test___init__dt_interpulse(self):
        ...

    def test___init__dt_LastBurst(self):
        ...

    def test___init__TR_burst(self):
        ...

    def test___init__es(self):
        ...

    def test___init__tr(self):
        ...

    def test___init__duration_readout(self):
        ...

    def test___init__duration_preparation(self):
        ...

    def test___init__duration_recovery(self):
        ...

    def test___init__flipAngle(self):
        ...

    def test___init__wrong_TR(self):
        ...

    def test___init__wrong_dt_interPulse(self):
        ...

    def test___init__wrong_TR_burst(self):
        ...

    def test___init__wrong_N_pulsePerOffset_Multiplicity(self):
        ...

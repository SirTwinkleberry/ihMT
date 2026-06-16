from ihmt.meta import Signal
from ihmt.sequence import Sequence
from ihmt.pulse import Tukey

from copy import deepcopy as copy
from unittest import TestCase

from numpy import set_printoptions
from sys import maxsize

set_printoptions(precision=maxsize)

CONFIG_SEQUENCE = {
    "init": {
        "signal": Signal.ALL,
        "N_pulsePerOffset": 1,
        "N_pulse": 4,
        "N_burst": 10,
        "N_adc": 80,
        "N_dummyADC": 3,
        "dt_interPulse": 1.5e-3,
        "TR_burst": 1e-1,
        "dt_lastBurst": 1e-3,
        "es": 6e-3,
        "tr": 1.387,
        "readout_flipAngle": 5,
    },
}

CONFIG_TUKEY = {
    "init": {
        "duration": 1e-3,
        "shape": 0.3,
        "flipAngle": 299,
        "offset": 7e3,
    },
}


class TestSequence(TestCase):
    def setUp(self):
        self.pulse = Tukey(**CONFIG_TUKEY["init"])
        self.sequence = Sequence(pulse=self.pulse, **CONFIG_SEQUENCE["init"])

    def test___init__signal_CM(self):
        tmp = copy(CONFIG_SEQUENCE["init"])
        tmp["signal"] = Signal.ihMTR_CM
        self.sequence = Sequence(pulse=self.pulse, **tmp)
        self.assertEqual(self.sequence.signal, Signal.ihMTR_CM)

    def test___init__pulse(self):
        self.sequence.pulse.__dict__["_onChanges"] = {}
        tmp = Tukey(**CONFIG_TUKEY["init"]).__dict__
        tmp["_onChanges"] = {}
        self.assertDictEqual(self.sequence.pulse.__dict__, tmp)

    def test___init__N_pulsePerOffset(self):
        self.assertEqual(
            self.sequence.N_pulsePerOffset, CONFIG_SEQUENCE["init"]["N_pulsePerOffset"]
        )

    def test___init__N_pulse(self):
        self.assertEqual(self.sequence.N_pulse, CONFIG_SEQUENCE["init"]["N_pulse"])

    def test___init__N_burst(self):
        self.assertEqual(self.sequence.N_burst, CONFIG_SEQUENCE["init"]["N_burst"])

    def test___init__N_adc(self):
        self.assertEqual(self.sequence.N_adc, CONFIG_SEQUENCE["init"]["N_adc"])

    def test___init__dt_interPulse(self):
        self.assertEqual(
            self.sequence.dt_interPulse, CONFIG_SEQUENCE["init"]["dt_interPulse"]
        )

    def test___init__dt_lastBurst(self):
        self.assertEqual(
            self.sequence.dt_lastBurst, CONFIG_SEQUENCE["init"]["dt_lastBurst"]
        )

    def test___init__TR_burst(self):
        self.assertEqual(self.sequence.TR_burst, CONFIG_SEQUENCE["init"]["TR_burst"])

    def test___init__es(self):
        self.assertEqual(self.sequence.es, CONFIG_SEQUENCE["init"]["es"])

    def test___init__tr(self):
        self.assertEqual(self.sequence.tr, CONFIG_SEQUENCE["init"]["tr"])

    def test___init__duration_readout(self):
        self.assertEqual(
            self.sequence.duration_readout,
            CONFIG_SEQUENCE["init"]["N_adc"] * CONFIG_SEQUENCE["init"]["es"],
        )

    def test___init__duration_preparation(self):
        self.assertEqual(
            self.sequence.duration_preparation,
            (CONFIG_SEQUENCE["init"]["N_burst"] - 1)
            * CONFIG_SEQUENCE["init"]["TR_burst"]
            + CONFIG_SEQUENCE["init"]["dt_lastBurst"],
        )

    def test___init__duration_recovery(self):
        self.assertEqual(
            self.sequence.duration_recovery,
            CONFIG_SEQUENCE["init"]["tr"]
            - (CONFIG_SEQUENCE["init"]["N_adc"] * CONFIG_SEQUENCE["init"]["es"])
            - (
                (CONFIG_SEQUENCE["init"]["N_burst"] - 1)
                * CONFIG_SEQUENCE["init"]["TR_burst"]
                + CONFIG_SEQUENCE["init"]["dt_lastBurst"]
            ),
        )

    def test___init__flipAngle(self):
        self.assertEqual(
            self.sequence.readout_flipAngle,
            CONFIG_SEQUENCE["init"]["readout_flipAngle"],
        )

    def test___init__wrong_TR(self):
        tmp = copy(CONFIG_SEQUENCE["init"])
        tmp["tr"] = (
            self.sequence.duration_preparation + self.sequence.duration_readout - 1e-15
        )
        with self.assertRaises(ValueError):
            Sequence(pulse=self.pulse, **tmp)

    def test___init__wrong_dt_interPulse(self):
        tmp = copy(CONFIG_SEQUENCE["init"])
        tmp["dt_interPulse"] = CONFIG_TUKEY["init"]["duration"] - 1e-15
        with self.assertRaises(ValueError):
            Sequence(pulse=self.pulse, **tmp)

    def test___init__wrong_TR_burst(self):
        tmp = copy(CONFIG_SEQUENCE["init"])
        tmp["TR_burst"] = (
            CONFIG_SEQUENCE["init"]["N_pulse"]
            * CONFIG_SEQUENCE["init"]["dt_interPulse"]
            - 1e-15
        )
        with self.assertRaises(ValueError):
            Sequence(pulse=self.pulse, **tmp)

    def test___init__wrong_N_pulsePerOffset_Multiplicity(self):
        tmp = copy(CONFIG_SEQUENCE["init"])
        tmp["N_pulsePerOffset"] = 4
        with self.assertRaises(ValueError):
            Sequence(pulse=self.pulse, **tmp)

    def test__init__wrong_N_adc_vs_N_dummy_ADC(self):
        tmp = copy(CONFIG_SEQUENCE["init"])
        tmp["N_dummyADC"] = tmp["N_adc"] + 1
        with self.assertRaises(ValueError):
            Sequence(pulse=self.pulse, **tmp)

    def test__init__flag_not_Signal(self):
        tmp = copy(CONFIG_SEQUENCE["init"])
        tmp["signal"] = "ihMTR_CM"
        with self.assertRaises(TypeError):
            Sequence(pulse=self.pulse, **tmp)

    def test_TR_set_wrong(self):
        with self.assertRaises(ValueError):
            self.sequence.tr = (
                self.sequence.duration_preparation
                + self.sequence.duration_readout
                - 1e-15
            )

    def test_dt_interPulse_set_wrong(self):
        with self.assertRaises(ValueError):
            self.sequence.dt_interPulse = CONFIG_TUKEY["init"]["duration"] - 1e-15

    def test_TR_burst_set_wrong(self):
        with self.assertRaises(ValueError):
            self.sequence.TR_burst = (
                CONFIG_SEQUENCE["init"]["N_pulse"]
                * CONFIG_SEQUENCE["init"]["dt_interPulse"]
                - 1e-15
            )

    def test_N_pulsePerOffset_Multiplicity_set_wrong(self):
        with self.assertRaises(ValueError):
            self.sequence.N_pulsePerOffset = 4

    def test_reset_duration_preparation(self):
        seq = Sequence(pulse=self.pulse, **CONFIG_SEQUENCE["init"])
        seq.duration_preparation
        del seq.duration_preparation
        self.assertFalse(hasattr(seq, "_duration_preparation"))
        seq.duration_preparation
        self.assertTrue(hasattr(seq, "_duration_preparation"))

    def test_reset_duration_readout(self):
        seq = Sequence(pulse=self.pulse, **CONFIG_SEQUENCE["init"])
        seq.duration_readout
        del seq.duration_readout
        self.assertFalse(hasattr(seq, "_duration_readout"))
        seq.duration_readout
        self.assertTrue(hasattr(seq, "_duration_readout"))

    def test_reset_duration_recovery(self):
        seq = Sequence(pulse=self.pulse, **CONFIG_SEQUENCE["init"])
        seq.duration_recovery
        del seq.duration_recovery
        self.assertFalse(hasattr(seq, "_duration_recovery"))
        seq.duration_recovery
        seq.duration_recovery
        self.assertTrue(hasattr(seq, "_duration_recovery"))

    def test_bypass_check_against_tr(self):
        seq = Sequence(pulse=self.pulse, **CONFIG_SEQUENCE["init"])
        del seq._N_adc
        self.assertIsNone(seq._check_against_tr())

    def test_bypass_check_against_tr_burst(self):
        seq = Sequence(pulse=self.pulse, **CONFIG_SEQUENCE["init"])
        del seq._TR_burst
        self.assertIsNone(seq._check_against_tr_burst())

    def test_bypass_check_against_N_pulse_multiplicity(self):
        seq = Sequence(pulse=self.pulse, **CONFIG_SEQUENCE["init"])
        del seq._N_pulse
        self.assertIsNone(seq._check_against_N_pulse_multiplicity())

    def test_bypass_check_against_pulse_duration(self):
        seq = Sequence(pulse=self.pulse, **CONFIG_SEQUENCE["init"])
        del seq._dt_interPulse
        self.assertIsNone(seq._check_against_pulse_duration())

    def test_bypass_check_against_N_dummyADC(self):
        seq = Sequence(pulse=self.pulse, **CONFIG_SEQUENCE["init"])
        del seq._N_dummyADC
        self.assertIsNone(seq._check_against_N_dummyADC())

    def test_copy(self):
        seq = Sequence(pulse=self.pulse, **CONFIG_SEQUENCE["init"])
        tmp = seq.copy()
        self.assertTrue(tmp.signal == seq.signal)
        self.assertTrue(tmp.N_pulsePerOffset == seq.N_pulsePerOffset)
        self.assertTrue(tmp.N_pulse == seq.N_pulse)
        self.assertTrue(tmp.N_burst == seq.N_burst)
        self.assertTrue(tmp.N_adc == seq.N_adc)
        self.assertTrue(tmp.readout_flipAngle == seq.readout_flipAngle)
        self.assertTrue(tmp.dt_interPulse == seq.dt_interPulse)
        self.assertTrue(tmp.dt_lastBurst == seq.dt_lastBurst)
        self.assertTrue(tmp.TR_burst == seq.TR_burst)
        self.assertTrue(tmp.es == seq.es)
        self.assertTrue(tmp.tr == seq.tr)
        self.assertTrue(tmp.duration_readout == seq.duration_readout)
        self.assertTrue(tmp.duration_preparation == seq.duration_preparation)
        self.assertTrue(tmp.duration_recovery == seq.duration_recovery)
        self.assertNotEqual(tmp._get_onChanges(), seq._get_onChanges())
        self.assertTrue(tmp.pulse.shape, seq.pulse.shape)
        self.assertTrue(tmp.pulse.duration, seq.pulse.duration)
        self.assertTrue(tmp.pulse.flipAngle, seq.pulse.flipAngle)
        self.assertTrue(tmp.pulse.offset, seq.pulse.offset)
        self.assertNotEqual(tmp.pulse._get_onChanges(), seq.pulse._get_onChanges())

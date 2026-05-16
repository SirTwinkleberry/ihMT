from brainhack.sequence import Modulation, Sequence
from brainhack.pulse import Tukey

from copy import deepcopy as copy
from unittest import TestCase

from numpy import set_printoptions
from sys import maxsize
set_printoptions(precision=maxsize)

CONFIG_SEQUENCE = {
    'init': {
        'modulation': Modulation.BP,
        'N_pulsePerOffset': 1,
        'N_pulse': 4,
        'N_burst': 10,
        'N_adc': 80,
        'N_dummyADC': 3,
        'dt_interPulse': 1.5e-3,
        'TR_burst': 1e-1,
        'dt_lastBurst': 1e-3,
        'es': 6e-3,
        'tr': 1.387,
        'readout_flipAngle': 5,
    },
}

CONFIG_TUKEY = {
    'init': {
        'duration': 1e-3,
        'shape': .3,
        'flipAngle': 299,
        'offset': 7e3,
    },
}


class TestModulation(TestCase):
    def test_CM_in_ALT(self):
        self.assertFalse(Modulation.CM in Modulation.ALT)

    def test_ALT_in_CM(self):
        self.assertFalse(Modulation.ALT in Modulation.CM)

    def test_BP_in_ALT(self):
        self.assertFalse(Modulation.BP in Modulation.ALT)

    def test_BP_in_CM(self):
        self.assertFalse(Modulation.BP in Modulation.CM)

    def test_ALT_in_BP(self):
        self.assertTrue(Modulation.ALT in Modulation.BP)

    def test_CM_in_BP(self):
        self.assertTrue(Modulation.CM in Modulation.BP)


class TestSequence(TestCase):
    def setUp(self):
        self.pulse = Tukey(**CONFIG_TUKEY['init'])
        self.sequence = Sequence(pulse=self.pulse, **CONFIG_SEQUENCE['init'])

    def test___init__modulation_CM(self):
        tmp = copy(CONFIG_SEQUENCE['init'])
        tmp['modulation'] = Modulation.CM
        self.sequence = Sequence(pulse=self.pulse, **tmp)
        self.assertEqual(self.sequence.modulation, Modulation.CM)

    def test___init__modulation_ALT(self):
        tmp = copy(CONFIG_SEQUENCE['init'])
        tmp['modulation'] = Modulation.ALT
        self.sequence = Sequence(pulse=self.pulse, **tmp)
        self.assertEqual(self.sequence.modulation, Modulation.ALT)

    def test___init__modulation_BP(self):
        self.assertEqual(self.sequence.modulation, Modulation.BP)

    def test___init__pulse(self):
        self.sequence.pulse.__dict__['_onChanges'] = {}
        tmp = Tukey(**CONFIG_TUKEY['init']).__dict__
        tmp['_onChanges'] = {}
        self.assertDictEqual(self.sequence.pulse.__dict__, tmp)

    def test___init__N_pulsePerOffset(self):
        self.assertEqual(self.sequence.N_pulsePerOffset, CONFIG_SEQUENCE['init']['N_pulsePerOffset'])

    def test___init__N_pulse(self):
        self.assertEqual(self.sequence.N_pulse, CONFIG_SEQUENCE['init']['N_pulse'])

    def test___init__N_burst(self):
        self.assertEqual(self.sequence.N_burst, CONFIG_SEQUENCE['init']['N_burst'])

    def test___init__N_adc(self):
        self.assertEqual(self.sequence.N_adc, CONFIG_SEQUENCE['init']['N_adc'])

    def test___init__dt_interPulse(self):
        self.assertEqual(self.sequence.dt_interPulse, CONFIG_SEQUENCE['init']['dt_interPulse'])

    def test___init__dt_lastBurst(self):
        self.assertEqual(self.sequence.dt_lastBurst, CONFIG_SEQUENCE['init']['dt_lastBurst'])

    def test___init__TR_burst(self):
        self.assertEqual(self.sequence.TR_burst, CONFIG_SEQUENCE['init']['TR_burst'])

    def test___init__es(self):
        self.assertEqual(self.sequence.es, CONFIG_SEQUENCE['init']['es'])

    def test___init__tr(self):
        self.assertEqual(self.sequence.tr, CONFIG_SEQUENCE['init']['tr'])

    def test___init__duration_readout(self):
        self.assertEqual(self.sequence.duration_readout, CONFIG_SEQUENCE['init']['N_adc'] * CONFIG_SEQUENCE['init']['es'])

    def test___init__duration_preparation(self):
        self.assertEqual(self.sequence.duration_preparation, (CONFIG_SEQUENCE['init']['N_burst'] - 1) * CONFIG_SEQUENCE['init']['TR_burst'] + CONFIG_SEQUENCE['init']['N_pulse'] * CONFIG_SEQUENCE['init']['dt_interPulse'] + CONFIG_SEQUENCE['init']['dt_lastBurst'])

    def test___init__duration_recovery(self):
        self.assertEqual(self.sequence.duration_recovery, CONFIG_SEQUENCE['init']['tr'] - (CONFIG_SEQUENCE['init']['N_adc'] * CONFIG_SEQUENCE['init']['es']) - ((CONFIG_SEQUENCE['init']['N_burst'] - 1) * CONFIG_SEQUENCE['init']['TR_burst'] + CONFIG_SEQUENCE['init']['N_pulse'] * CONFIG_SEQUENCE['init']['dt_interPulse'] + CONFIG_SEQUENCE['init']['dt_lastBurst']))

    def test___init__flipAngle(self):
        self.assertEqual(self.sequence.readout_flipAngle, CONFIG_SEQUENCE['init']['readout_flipAngle'])

    def test___init__wrong_TR(self):
        tmp = copy(CONFIG_SEQUENCE['init'])
        tmp['tr'] = self.sequence.duration_preparation + self.sequence.duration_readout - 1e-15
        with self.assertRaises(ValueError):
            Sequence(pulse=self.pulse, **tmp)

    def test___init__wrong_dt_interPulse(self):
        tmp = copy(CONFIG_SEQUENCE['init'])
        tmp['dt_interPulse'] = CONFIG_TUKEY['init']['duration'] - 1e-15
        with self.assertRaises(ValueError):
            Sequence(pulse=self.pulse, **tmp)

    def test___init__wrong_TR_burst(self):
        tmp = copy(CONFIG_SEQUENCE['init'])
        tmp['TR_burst'] = CONFIG_SEQUENCE['init']['N_pulse'] * CONFIG_SEQUENCE['init']['dt_interPulse'] - 1e-15
        with self.assertRaises(ValueError):
            Sequence(pulse=self.pulse, **tmp)

    def test___init__wrong_N_pulsePerOffset_Multiplicity(self):
        tmp = copy(CONFIG_SEQUENCE['init'])
        tmp['N_pulsePerOffset'] = 4
        with self.assertRaises(ValueError):
            Sequence(pulse=self.pulse, **tmp)

    def test_TR_set_wrong(self):
            with self.assertRaises(ValueError):
                self.sequence.tr = self.sequence.duration_preparation + self.sequence.duration_readout - 1e-15

    def test_dt_interPulse_set_wrong(self):
            with self.assertRaises(ValueError):
                self.sequence.dt_interPulse = CONFIG_TUKEY['init']['duration'] - 1e-15

    def test_TR_burst_set_wrong(self):
            with self.assertRaises(ValueError):
                self.sequence.TR_burst = CONFIG_SEQUENCE['init']['N_pulse'] * CONFIG_SEQUENCE['init']['dt_interPulse'] - 1e-15

    def test_N_pulsePerOffset_Multiplicity_set_wrong(self):
            with self.assertRaises(ValueError):
                self.sequence.N_pulsePerOffset = 4

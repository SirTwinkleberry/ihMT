# from brainhack.simulator import SteadyState
from brainhack.sequence import Sequence, Modulation
from brainhack.pulse import Tukey
from brainhack.system import System
from brainhack.simulator import SteadyState

from unittest import TestCase
from numpy import array

from numpy import set_printoptions
from sys import maxsize
set_printoptions(precision=maxsize)

CONFIG_TUKEY = {
    'init': {
        'duration': 1e-3,
        'shape': .3,
        'flipAngle': 299,
        'offset': 7e3,
    },
}

CONFIG_SEQUENCE = {
    'init': {
        'modulation': Modulation.BP,
        'N_pulsePerOffset': 1,
        'N_pulse': 4,
        'N_burst': 10,
        'N_adc': 80,
        'dt_interPulse': 1.5e-3,
        'TR_burst': 1e-1,
        'dt_lastBurst': 1e-3,
        'es': 6e-3,
        'tr': 1.387,
        'readout_flipAngle': 5,
    },
}

CONFIG_SYSTEM = {
    'init': {
        'poolFree_M0': 1,
        'poolFree_T1': 1,
        'poolFree_T2': .1,
        'poolFreeBound_exchangeRate': 10,
        'poolBound_M0': .1,
        'poolBound_T1': 1,
        'poolBound_T2': 1e-5,
        'poolBound_T1D': 1e-2,
    }
}

CONFIG_STEADYSTATE = {
    'compute': {
        'CM':  array([[0.9037829677605914, 0.09037837084448297, 0.0, 1.0], [0.7676252578552804, 0.045410925120816445, 1.52674916515777e-06, 1.0], [0.6599520559568383, 0.010208119191059052, 0.0, 1.0]]),
        'ALT': array([[0.9037829677605914, 0.09037837084448297, 0.0, 1.0], [0.7676252578552804, 0.045410925120816445, 1.52674916515777e-06, 1.0], [0.6700714322545925, 0.013280097321291226, -2.724688446800882e-07, 1.0]]),
        'BP':  array([[0.9037829677605914, 0.09037837084448297, 0.0, 1.0], [0.7676252578552804, 0.045410925120816445, 1.52674916515777e-06, 1.0], [0.6599520559568383, 0.010208119191059052, 0.0, 1.0], [0.6700714322545925, 0.013280097321291226, -2.724688446800882e-07, 1.0]]),
    }
}


class TestSteadyState(TestCase):
    def setUp(self):
        self.pulse = Tukey(**CONFIG_TUKEY['init'])
        self.sequence = Sequence(pulse=self.pulse, **CONFIG_SEQUENCE['init'])
        self.system = System(pulse=self.pulse, **CONFIG_SYSTEM['init'])

    def test_steadyState_CM(self):
        self.sequence.modulation = Modulation.CM
        self.assertTrue((array(SteadyState(self.system, self.sequence)) == CONFIG_STEADYSTATE['compute']['CM']).all())

    def test_steadyState_ALT(self):
        self.sequence.modulation = Modulation.ALT
        self.assertTrue((array(SteadyState(self.system, self.sequence)) == CONFIG_STEADYSTATE['compute']['ALT']).all())

    def test_steadyState_BP(self):
        self.assertTrue((array(SteadyState(self.system, self.sequence)) == CONFIG_STEADYSTATE['compute']['BP']).all())

    def test_steadyState_mismatched_Pulse(self):
        self.sequence.pulse = Tukey(**CONFIG_TUKEY['init'])  # the _onChange_ callbacks of the new pulse will be different
        with self.assertRaises(ValueError):
            SteadyState(self.system, self.sequence)

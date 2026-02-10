# from brainhack.simulator import Simulate
from brainhack.sequence import Sequence, Modulation
from brainhack.pulse import Tukey
from brainhack.system import System
from brainhack.simulator import Simulate

from unittest import TestCase
from numpy import array

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
        'ES': 6e-3,
        'TR': 1.387,
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

CONFIG_SIMULATE = {
    'compute': {
        'CM': array([[0.9037829677605914,  0.090378370844482970,  0.                    , 1.],
                     [0.7676252586373370,  0.045410925323905185,  1.5267491627581326e-06, 1.],
                     [0.6599520592347559,  0.010208120168757757,  0.                    , 1.]]),

        'ALT': array([[0.9037829677605914, 0.090378370844482970,  0.                    , 1.],
                     [0.76762525863733700, 0.045410925323905185,  1.5267491627581326e-06, 1.],
                     [0.67007143512606930, 0.013280098185195757, -2.7246884677924776e-07, 1.]]),

        'BP': array([[0.9037829677605914,  0.090378370844482970,  0.                    , 1.],
                     [0.7676252586373370,  0.045410925323905185,  1.5267491627581326e-06, 1.],
                     [0.6599520592347559,  0.010208120168757757,  0.                    , 1.],
                     [0.6700714351260693,  0.013280098185195757, -2.7246884677924776e-07, 1.]]),
    }
}


class TestSimulate(TestCase):
    def setUp(self):
        self.pulse = Tukey(**CONFIG_TUKEY['init'])
        self.sequence = Sequence(pulse=self.pulse, **CONFIG_SEQUENCE['init'])  # type: ignore
        self.system = System(**CONFIG_SYSTEM['init'])  # type: ignore
        self.system.RFabsorption_Matrix(self.pulse)

    def test_simulate_CM(self):
        self.sequence.modulation = Modulation.CM
        self.assertTrue((array(Simulate(self.system, self.sequence)) == CONFIG_SIMULATE['compute']['CM']).all())

    def test_simulate_ALT(self):
        self.sequence.modulation = Modulation.ALT
        self.assertTrue((array(Simulate(self.system, self.sequence)) == CONFIG_SIMULATE['compute']['ALT']).all())

    def test_simulate_BP(self):
        self.assertTrue((array(Simulate(self.system, self.sequence)) == CONFIG_SIMULATE['compute']['BP']).all())

    def test_simulate_missingAttr_poolBound_Rrf_dualSat(self):
        del self.system.poolBound_Rrf_dualSat
        with self.assertRaises(AttributeError):
            Simulate(self.system, self.sequence)

    def test_simulate_missingAttr_poolBound_Rrf_singleSat_Positive(self):
        del self.system.poolBound_Rrf_singleSat_Positive
        with self.assertRaises(AttributeError):
            Simulate(self.system, self.sequence)

    def test_simulate_missingAttr_poolBound_Rrf_singleSat_Negative(self):
        del self.system.poolBound_Rrf_singleSat_Negative
        with self.assertRaises(AttributeError):
            Simulate(self.system, self.sequence)

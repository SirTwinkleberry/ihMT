from brainhack.meta import Signal
from brainhack.sequence import Sequence
from brainhack.pulse import Tukey
from brainhack.system import System
from brainhack.simulator import Simulator

from unittest import TestCase, skip

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
        'signal': Signal.BPR,
        'N_pulsePerOffset': 1,
        'N_pulse': 4,
        'N_burst': 10,
        'N_adc': 80,
        'N_dummyADC': 0,
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
        'poolBound_lineshapeAsymmetry': 0,
        'poolBound_M0': .1,
        'poolBound_T1': 1,
        'poolBound_T2': 1e-5,
        'poolBound_T1D': 1e-2,
    }
}

CONFIG_SIMULATOR = {
    'init': {
        'output_vectorSlice': slice(None),
        'export_readMatrix': True,
    },
    'compute': {
        'ihMTR_CM':  dict(
            MT0=[0.9037829677605914, 0.09037837084448297, 0.0, 1.0],
            MTs_Positive=[0.76762525270985, 0.04541092351421086, 1.5267491866078584e-06, 1.0],
            MTs_Negative=[0.76762525270985, 0.04541092351421086, 1.5267491866078584e-06, 1.0],
            MTd_CM=[0.6599520300832797, 0.010208111186669097, 0.0, 1.0],
        ),
        'ihMTR_ALT': dict(
            MT0=[0.9037829677605914, 0.09037837084448297, 0.0, 1.0],
            MTs_Positive=[0.76762525270985, 0.04541092351421086, 1.5267491866078584e-06, 1.0],
            MTs_Negative=[0.76762525270985, 0.04541092351421086, 1.5267491866078584e-06, 1.0],
            MTd_ALT=[0.6700714097373646, 0.01328009025363687, -2.7246882836319824e-07, 1.0],
        ),
        'BPR':  dict(
            MT0=[0.9037829677605914, 0.09037837084448297, 0.0, 1.0],
            MTd_ALT=[0.6700714097373646, 0.01328009025363687, -2.7246882836319824e-07, 1.0],
            MTd_CM=[0.6599520300832797, 0.010208111186669097, 0.0, 1.0],
        ),
    }
}


class TestSteadyState(TestCase):
    def setUp(self):
        self.pulse = Tukey(**CONFIG_TUKEY['init'])
        self.sequence = Sequence(pulse=self.pulse, **CONFIG_SEQUENCE['init'])
        self.system = System(pulse=self.pulse, **CONFIG_SYSTEM['init'])
        self.simulator = Simulator(system=self.system, sequence=self.sequence, **CONFIG_SIMULATOR['init'])

    def test_steadyState_CM(self):
        self.sequence.signal = Signal.ihMTR_CM
        out = self.simulator.SteadyState()
        for key, val in out.items():
            out[key] = val.tolist()
        del out['readout']
        self.assertDictEqual(out, CONFIG_SIMULATOR['compute']['ihMTR_CM'])
        # self.assertTrue((array(out) == CONFIG_SIMULATOR['compute']['ihMTR_CM']).all())

    def test_steadyState_ALT(self):
        self.sequence.signal = Signal.ihMTR_ALT
        out = self.simulator.SteadyState()
        for key, val in out.items():
            out[key] = val.tolist()
        del out['readout']
        self.assertDictEqual(out, CONFIG_SIMULATOR['compute']['ihMTR_ALT'])
        # self.assertTrue((array(out) == CONFIG_SIMULATOR['compute']['ihMTR_ALT']).all())

    def test_steadyState_BP(self):
        out = self.simulator.SteadyState()
        for key, val in out.items():
            out[key] = val.tolist()
        del out['readout']
        self.assertDictEqual(out, CONFIG_SIMULATOR['compute']['BPR'])
        # self.assertTrue((array(out) == CONFIG_SIMULATOR['compute']['BPR']).all())

class TestSimulator(TestCase):
    @skip
    def test_steadyState_mismatched_Pulse(self):
        self.sequence.pulse = Tukey(**CONFIG_TUKEY['init'])  # the _onChange_ callbacks of the new pulse will be different
        with self.assertRaises(ValueError):
            self.simulator.SteadyState()

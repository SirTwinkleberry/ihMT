# from brainhack.simulator import Simulate
from brainhack.sequence import Sequence, Modulation
from brainhack.pulses import Tukey
from brainhack.system import System

# from copy import copy
from numpy import array
from unittest import TestCase

CONFIG_TUKEY = {
    'init': {
        'duration': 1e-3,
        'shape': .3,
        'flipAngle': 299,
        'offset': 7e3,
    },
    'compute': {
        'amplitudeIntegral': 0.8500000205357132,
        'powerIntegral': 0.8125000410741003,
        'b1peak': 2.2950107701791806e-05,
        'omegaRMS': 5534.027393037432,
    }
}


class TestSimulate(TestCase):
    pulse = Tukey(**CONFIG_TUKEY['init'])
    pulse.amplitudeIntegral = CONFIG_TUKEY['compute']['amplitudeIntegral']
    pulse.powerIntegral = CONFIG_TUKEY['compute']['powerIntegral']
    pulse.b1peak = CONFIG_TUKEY['compute']['b1peak']
    pulse.omegaRMS = CONFIG_TUKEY['compute']['omegaRMS']

    sequence = Sequence(modulation=Modulation.BP, pulse=pulse, N_pulsePerOffset=1, N_pulse=4, N_burst=10, N_adc=80, dt_interPulse=1.5e-3, TR_burst=1e-1, dt_lastBurst=1e-3, ES=6e-3, TR=3, readout_flipAngle=5)
    sequence.duration_readout = 80 * 6e-3
    sequence.duration_preparation = (10 - 1) * 1e-1 + 1e-3
    sequence.duration_recovery = 3 - 80 * 6e-3 - ((10 - 1) * 1e-1 + 1e-3)

    system = System(poolFree_M0=1, poolFree_T1=1, poolFree_T2=.1, poolFreeBound_exchangeRate=10, poolBound_M0=.1, poolBound_T1=1, poolBound_T2=1e-5, poolBound_T1D=1e-2)
    system.poolFree_Rrf = array([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
    system.poolBound_Rrf_dualSat = array([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
    system.poolBound_Rrf_singleSat_Positive = array([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
    system.poolBound_Rrf_singleSat_Negative = array([[0, 0, 0], [0, 0, 0], [0, 0, 0]])

    def test_simulate_CM(self):
        ...

    def test_simulate_ALT(self):
        ...

    def test_simulate_BP(self):
        ...

    def test_simulate_missingAttr_poolBound_Rrf_dualSat(self):
        ...

    def test_simulate_missingAttr_poolBound_Rrf_singleSat_Positive(self):
        ...

    def test_simulate_missingAttr_poolBound_Rrf_singleSat_Negative(self):
        ...

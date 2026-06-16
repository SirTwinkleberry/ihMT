from ihmt.meta import Signal
from ihmt.sequence import Sequence
from ihmt.pulse import Tukey
from ihmt.system import System
from ihmt.simulator import Simulator

from unittest import TestCase, skip

from numpy import set_printoptions
from sys import maxsize

set_printoptions(precision=maxsize)

CONFIG_TUKEY = {
    "init": {
        "duration": 1e-3,
        "shape": 0.3,
        "flipAngle": 299,
        "offset": 7e3,
    },
}

CONFIG_SEQUENCE = {
    "init": {
        "signal": Signal.BPR,
        "N_pulsePerOffset": 1,
        "N_pulse": 4,
        "N_burst": 10,
        "N_adc": 80,
        "N_dummyADC": 0,
        "dt_interPulse": 1.5e-3,
        "TR_burst": 1e-1,
        "dt_lastBurst": 1e-3,
        "es": 6e-3,
        "tr": 1.387,
        "readout_flipAngle": 5,
    },
}

CONFIG_SYSTEM = {
    "init": {
        "poolFree_M0": 1,
        "poolFree_T1": 1,
        "poolFree_T2": 0.1,
        "poolFreeBound_exchangeRate": 10,
        "poolBound_lineshapeAsymmetry": 0,
        "poolBound_M0": 0.1,
        "poolBound_T1": 1,
        "poolBound_T2": 1e-5,
        "poolBound_T1D": 1e-2,
    }
}

CONFIG_SIMULATOR = {
    "init": {
        "output_vectorSlice": slice(None),
        "export_readMatrix": True,
    },
    "compute": {
        "ihMTR_CM": dict(
            MT0=[0.9037829677605911, 0.09037837084448294, 0.0, 1.0],
            MTs_Positive=[
                0.768369253684603,
                0.0454539042950363,
                1.5281848336861655e-06,
                1.0,
            ],
            MTs_Negative=[
                0.768369253684603,
                0.0454539042950363,
                1.5281848336861655e-06,
                1.0,
            ],
            MTd_CM=[0.6606360409781923, 0.010218152542836825, 0.0, 1.0],
            readout=[
                [0.984485836436591, 0.05771551658429958, 0.0, 0.005982035946064735],
                [0.005749589161890545, 0.9363024474696356, 0.0, 0.0005982035946064736],
                [0.0, 0.0, 0.5488116360940265, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
        ),
        "ihMTR_ALT": dict(
            MT0=[0.9037829677605911, 0.09037837084448294, 0.0, 1.0],
            MTs_Positive=[
                0.768369253684603,
                0.0454539042950363,
                1.5281848336861655e-06,
                1.0,
            ],
            MTs_Negative=[
                0.768369253684603,
                0.0454539042950363,
                1.5281848336861655e-06,
                1.0,
            ],
            MTd_ALT=[
                0.6707639083635117,
                0.013293125187180439,
                -2.727313124262742e-07,
                1.0,
            ],
            readout=[
                [0.984485836436591, 0.05771551658429958, 0.0, 0.005982035946064735],
                [0.005749589161890545, 0.9363024474696356, 0.0, 0.0005982035946064736],
                [0.0, 0.0, 0.5488116360940265, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
        ),
        "BPR": dict(
            MT0=[0.9037829677605911, 0.09037837084448294, 0.0, 1.0],
            MTd_ALT=[
                0.6707639083635117,
                0.013293125187180439,
                -2.727313124262742e-07,
                1.0,
            ],
            MTd_CM=[0.6606360409781923, 0.010218152542836825, 0.0, 1.0],
            readout=[
                [0.984485836436591, 0.05771551658429958, 0.0, 0.005982035946064735],
                [0.005749589161890545, 0.9363024474696356, 0.0, 0.0005982035946064736],
                [0.0, 0.0, 0.5488116360940265, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
        ),
    },
}


class TestSteadyState(TestCase):
    def setUp(self):
        self.pulse = Tukey(**CONFIG_TUKEY["init"])
        self.sequence = Sequence(pulse=self.pulse, **CONFIG_SEQUENCE["init"])
        self.system = System(pulse=self.pulse, **CONFIG_SYSTEM["init"])
        self.simulator = Simulator(
            system=self.system, sequence=self.sequence, **CONFIG_SIMULATOR["init"]
        )

    def test_steadyState_CM(self):
        self.sequence.signal = Signal.ihMTR_CM
        out = self.simulator.SteadyState()
        for key, val in out.items():
            out[key] = val.tolist()
        self.assertDictEqual(out, CONFIG_SIMULATOR["compute"]["ihMTR_CM"])

    def test_steadyState_ALT(self):
        self.sequence.signal = Signal.ihMTR_ALT
        out = self.simulator.SteadyState()
        for key, val in out.items():
            out[key] = val.tolist()
        self.assertDictEqual(out, CONFIG_SIMULATOR["compute"]["ihMTR_ALT"])

    def test_steadyState_BP(self):
        out = self.simulator.SteadyState()
        for key, val in out.items():
            out[key] = val.tolist()
        self.assertDictEqual(out, CONFIG_SIMULATOR["compute"]["BPR"])


class TestSimulator(TestCase):
    @skip
    def test_steadyState_mismatched_Pulse(self):
        self.sequence.pulse = Tukey(
            **CONFIG_TUKEY["init"]
        )  # the _onChange_ callbacks of the new pulse will be different
        with self.assertRaises(ValueError):
            self.simulator.SteadyState()

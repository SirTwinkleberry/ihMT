from brainhack.pulse import _Pulse, Tukey

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
    'compute': {
        'amplitudeIntegral': 0.85,
        'powerIntegral': 0.8125,
        'b1peak': 2.2950108256258665e-05,
        'omegaRMS': 5534.02752670352,
    }
}


class TestPulse(TestCase):
    def test___init__(self):
        with self.assertRaises(NotImplementedError):
            _Pulse()

    @skip("Pulse constructor will raise NotImplementedError")
    def test_value(self):
        mock_pulse = _Pulse()
        with self.assertRaises(NotImplementedError):
            mock_pulse.value(0)

    @skip("Pulse constructor will raise NotImplementedError")
    def test_resetComputedAttributes(self):
        mock_pulse = _Pulse()
        with self.assertRaises(NotImplementedError):
            mock_pulse.resetComputedAttributes()


class TestTukey(TestCase):
    def test___init___Duration(self):
        pulse = Tukey(**CONFIG_TUKEY['init'])
        self.assertEqual(CONFIG_TUKEY['init']['duration'], pulse.duration)

    def test___init___Shape(self):
        pulse = Tukey(**CONFIG_TUKEY['init'])
        self.assertEqual(CONFIG_TUKEY['init']['shape'], pulse.shape)

    def test___init___FlipAngle(self):
        pulse = Tukey(**CONFIG_TUKEY['init'])
        self.assertEqual(CONFIG_TUKEY['init']['flipAngle'], pulse.flipAngle)

    def test___init___Offset(self):
        pulse = Tukey(**CONFIG_TUKEY['init'])
        self.assertEqual(CONFIG_TUKEY['init']['offset'], pulse.offset)

    def test__init__GyromagneticFactor(self):
        pulse = Tukey(**CONFIG_TUKEY['init'])
        self.assertEqual(267513000, pulse.gyromagneticFactor)

    def test__init__AmplitudeIntegral(self):
        pulse = Tukey(**CONFIG_TUKEY['init'])
        self.assertEqual(CONFIG_TUKEY['compute']['amplitudeIntegral'], pulse.amplitudeIntegral)

    def test__init__PowerIntegral(self):
        pulse = Tukey(**CONFIG_TUKEY['init'])
        self.assertEqual(CONFIG_TUKEY['compute']['powerIntegral'], pulse.powerIntegral)

    def test__init__B1peak(self):
        pulse = Tukey(**CONFIG_TUKEY['init'])
        self.assertEqual(CONFIG_TUKEY['compute']['b1peak'], pulse.b1peak)

    def test__init__OmegaRMS(self):
        pulse = Tukey(**CONFIG_TUKEY['init'])
        self.assertEqual(CONFIG_TUKEY['compute']['omegaRMS'], pulse.omegaRMS)

    def test_value_outside_bounds(self):
        pulse = Tukey(**CONFIG_TUKEY['init'])
        duration: float = CONFIG_TUKEY['init']['duration']
        for t in [-.1 * duration, 0, duration, 1.1 * duration]:
            with self.subTest(number=t):
                self.assertEqual(pulse.value(t), 0)

    def test_value_ramping_up(self):
        pulse = Tukey(**CONFIG_TUKEY['init'])
        duration: float = CONFIG_TUKEY['init']['duration']
        shape: float = CONFIG_TUKEY['init']['shape']
        self.assertEqual(pulse.value(.25 * shape * duration), .5)

    def test_value_ramping_down(self):
        pulse = Tukey(**CONFIG_TUKEY['init'])
        duration: float = CONFIG_TUKEY['init']['duration']
        shape: float = CONFIG_TUKEY['init']['shape']
        self.assertEqual(pulse.value(duration - .25 * shape * duration), .5)

    def test_value_plateau(self):
        pulse = Tukey(**CONFIG_TUKEY['init'])
        duration: float = CONFIG_TUKEY['init']['duration']
        shape: float = CONFIG_TUKEY['init']['shape']
        self.assertEqual(pulse.value(.5 * shape * duration), 1)

    def test__resetComputedAttributes(self):
        pulse = Tukey(**CONFIG_TUKEY['init'])
        pulse.amplitudeIntegral
        pulse.powerIntegral
        pulse.b1peak
        pulse.omegaRMS
        self.assertDictEqual(pulse.__dict__, {'_onChange': {}, '_gyromagneticFactor': 267513000, '_shape': 0.3, '_duration': 0.001, '_flipAngle': 299, '_offset': 7000.0, '_amplitudeIntegral': 0.85, '_powerIntegral': 0.8125, '_b1peak': 2.2950108256258665e-05, '_omegaRMS': 5534.02752670352})
        pulse._resetComputedAttributes(['amplitudeIntegral', 'powerIntegral', 'b1peak', 'omegaRMS'])
        self.assertDictEqual(pulse.__dict__, {'_onChange': {}, '_gyromagneticFactor': 267513000, '_shape': 0.3, '_duration': 0.001, '_flipAngle': 299, '_offset': 7000.0})

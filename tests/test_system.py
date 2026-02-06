from brainhack.system import System
from brainhack.pulses import Tukey

from unittest import TestCase
from numpy import sqrt

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
    },
    'compute': {
        'poolBound_omegaLocField': 1. / ( sqrt(15) * 1e-5 ),
        'N_pools': 2,
    }
}


class TestSystem(TestCase):
    mock_system = System
    mock_system.poolFree_M0 = float(CONFIG_SYSTEM['init']['poolFree_M0'])
    mock_system.poolFree_T1 = float(CONFIG_SYSTEM['init']['poolFree_T1'])
    mock_system.poolFree_T2 = float(CONFIG_SYSTEM['init']['poolFree_T2'])
    mock_system.poolFreeBound_exchangeRate = float(CONFIG_SYSTEM['init']['poolFreeBound_exchangeRate'])
    mock_system.poolBound_M0 = float(CONFIG_SYSTEM['init']['poolBound_M0'])
    mock_system.poolBound_T1 = float(CONFIG_SYSTEM['init']['poolBound_T1'])
    mock_system.poolBound_T2 = float(CONFIG_SYSTEM['init']['poolBound_T2'])
    mock_system.poolBound_T1D = float(CONFIG_SYSTEM['init']['poolBound_T1D'])
    mock_system.poolBound_omegaLocField = float(CONFIG_SYSTEM['compute']['poolBound_omegaLocField'])
    mock_system.N_pools = int(CONFIG_SYSTEM['compute']['N_pools'])

    mock_pulse = Tukey(**CONFIG_TUKEY['init'])

    def test___init__poolFree_M0(self):
        self.assertEqual(System(**CONFIG_SYSTEM['init']), mock_system.)

    def test___init__poolFree_T1(self):
        ...

    def test___init__poolFree_T2(self):
        ...

    def test___init__poolFreeBound_exchangeRate(self):
        ...

    def test___init__poolBound_M0(self):
        ...

    def test___init__poolBound_T1(self):
        ...

    def test___init__poolBound_T2(self):
        ...

    def test___init__poolBound_T1D(self):
        ...

    def test___init__poolBound_omegaLocField(self):
        ...

    def test___init__N_pools(self):
        ...

    def test_RFabsorption_Matrix(self):
        ...


class TestLineshapes(TestCase):
    mock_system = System(**CONFIG_SYSTEM['init'])

    mock_pulse = Tukey(**CONFIG_TUKEY['init'])

    def test_Lorentzian(self):
        self.assertEqual(self.mock_system.Lorentzian(self.mock_pulse, self.mock_system.poolBound_T2), 2.6671533855137817e-06)

    def test_Gaussian(self):
        self.assertEqual(self.mock_system.Gaussian(self.mock_pulse, self.mock_system.poolBound_T2), 3.621630854421752e-06)

    def test_SuperLorentzian(self):
        self.assertEqual(self.mock_system.SuperLorentzian(self.mock_pulse, self.mock_system.poolBound_T2), 3.7463817768960933e-06)

    def test_PampelSuperLorentzian(self):
        self.assertEqual(self.mock_system.PampelSuperLorentzian(self.mock_pulse, self.mock_system.poolBound_T2), 3.7463848626091833e-06)

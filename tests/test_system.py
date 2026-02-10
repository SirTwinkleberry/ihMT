from brainhack.system import System
from brainhack.pulse import Tukey

from unittest import TestCase
from numpy import sqrt, array

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
        'poolFree_Rrf': array( [[-0.15831671499986222,  0.,          0.],
                                [ 0.,                   0.,          0.],
                                [ 0.,                   0.,          0.]] ),

        'poolBound_Rrf_dualSat': array( [[-0.,    0.,                  0.             ],
                                         [ 0., -360.4495719010987,     0.             ],
                                         [ 0.,    0.,              -1045.9034362745224]] ),

        'poolBound_Rrf_singleSat_Positive': array( [[-0.,    0.,                          0.             ],
                                                    [ 0., -360.4495719010987,      15853400.179037085    ],
                                                    [ 0.,    0.02378010026855563,     -1045.9034362745224]] ),

        'poolBound_Rrf_singleSat_Negative': array( [[-0.,    0.,                          0.             ],
                                                    [ 0., -360.4495719010987,     -15853400.179037085    ],
                                                    [ 0.,   -0.02378010026855563,     -1045.9034362745224]] ),
    }
}


class TestSystem(TestCase):
    def setUp(self):
        self.system = System(**CONFIG_SYSTEM['init'])  # type: ignore

    def test___init__poolFree_M0(self):
        self.assertEqual(self.system.poolFree_M0, CONFIG_SYSTEM['init']['poolFree_M0'])

    def test___init__poolFree_T1(self):
        self.assertEqual(self.system.poolFree_T1, CONFIG_SYSTEM['init']['poolFree_T1'])

    def test___init__poolFree_T2(self):
        self.assertEqual(self.system.poolFree_T2, CONFIG_SYSTEM['init']['poolFree_T2'])

    def test___init__poolFreeBound_exchangeRate(self):
        self.assertEqual(self.system.poolFreeBound_exchangeRate, CONFIG_SYSTEM['init']['poolFreeBound_exchangeRate'])

    def test___init__poolBound_M0(self):
        self.assertEqual(self.system.poolBound_M0, CONFIG_SYSTEM['init']['poolBound_M0'])

    def test___init__poolBound_T1(self):
        self.assertEqual(self.system.poolBound_T1, CONFIG_SYSTEM['init']['poolBound_T1'])

    def test___init__poolBound_T2(self):
        self.assertEqual(self.system.poolBound_T2, CONFIG_SYSTEM['init']['poolBound_T2'])

    def test___init__poolBound_T1D(self):
        self.assertEqual(self.system.poolBound_T1D, CONFIG_SYSTEM['init']['poolBound_T1D'])

    def test___init__poolBound_omegaLocField(self):
        self.assertEqual(self.system.poolBound_omegaLocField, CONFIG_SYSTEM['compute']['poolBound_omegaLocField'])

    def test___init__N_pools(self):
        self.assertEqual(self.system.N_pools, CONFIG_SYSTEM['compute']['N_pools'])

    def test_RFabsorption_Matrix_poolFree_Rrf(self):
        pulse = Tukey(**CONFIG_TUKEY['init'])
        self.system.RFabsorption_Matrix(pulse)
        self.assertTrue((self.system.poolFree_Rrf == CONFIG_SYSTEM['compute']['poolFree_Rrf']).all())

    def test_RFabsorption_Matrix_poolBound_Rrf_dualSat(self):
        pulse = Tukey(**CONFIG_TUKEY['init'])
        self.system.RFabsorption_Matrix(pulse)
        self.assertTrue((self.system.poolBound_Rrf_dualSat == CONFIG_SYSTEM['compute']['poolBound_Rrf_dualSat']).all())

    def test_RFabsorption_Matrix_poolBound_Rrf_singleSat_Positive(self):
        pulse = Tukey(**CONFIG_TUKEY['init'])
        self.system.RFabsorption_Matrix(pulse)
        self.assertTrue((self.system.poolBound_Rrf_singleSat_Positive == CONFIG_SYSTEM['compute']['poolBound_Rrf_singleSat_Positive']).all())

    def test_RFabsorption_Matrix_poolBound_Rrf_singleSat_Negative(self):
        pulse = Tukey(**CONFIG_TUKEY['init'])
        self.system.RFabsorption_Matrix(pulse)
        self.assertTrue((self.system.poolBound_Rrf_singleSat_Negative == CONFIG_SYSTEM['compute']['poolBound_Rrf_singleSat_Negative']).all())


class TestLineshapes(TestCase):
    def setUp(self):
        self.system = System(**CONFIG_SYSTEM['init'])  # type: ignore
        self.pulse = Tukey(**CONFIG_TUKEY['init'])

    def test_Lorentzian(self):
        self.assertEqual(self.system.Lorentzian(self.pulse, self.system.poolBound_T2), 2.6671533855137817e-06)

    def test_Gaussian(self):
        self.assertEqual(self.system.Gaussian(self.pulse, self.system.poolBound_T2), 3.621630854421752e-06)

    def test_SuperLorentzian(self):
        self.assertEqual(self.system.SuperLorentzian(self.pulse, self.system.poolBound_T2), 3.7463817768960933e-06)

    def test_PampelSuperLorentzian(self):
        self.assertEqual(self.system.PampelSuperLorentzian(self.pulse, self.system.poolBound_T2), 3.7463848626091833e-06)

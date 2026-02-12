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
    }
}

CONFIG_SYSTEM = {
    'init': {
        'pulse': Tukey(**CONFIG_TUKEY['init']),
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
        'poolBound_omegaLocalField': 1. / ( sqrt(15) * 1e-5 ),
        'N_pools': 2,
        'poolFree_Rrf': array( [[-0.15831673065100935, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]] ),
        'poolBound_Rrf_dualSat': array( [[0.0, 0.0, 0.0], [0.0, -360.4496075350448, 0.0], [0.0, 0.0, -1045.90353967225]] ),
        'poolBound_Rrf_singleSat_Negative': array( [[0.0, 0.0, 0.0], [0.0, -360.4496075350448, -15853401.74629989], [0.0, -0.02378010261944984, -1045.90353967225]] ),
        'poolBound_Rrf_singleSat_Positive': array( [[0.0, 0.0, 0.0], [0.0, -360.4496075350448, 15853401.74629989], [0.0, 0.02378010261944984, -1045.90353967225]] ),
    }
}


class TestSystem(TestCase):
    def setUp(self):
        self.system = System(**CONFIG_SYSTEM['init'])

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

    def test___init__poolBound_omegaLocalField(self):
        self.assertEqual(self.system.poolBound_omegaLocalField, CONFIG_SYSTEM['compute']['poolBound_omegaLocalField'])

    def test___init__N_pools(self):
        self.assertEqual(self.system.N_pools, CONFIG_SYSTEM['compute']['N_pools'])

    def test_RFabsorption_Matrix_poolFree_Rrf(self):
        self.assertTrue((self.system.poolFree_Rrf == CONFIG_SYSTEM['compute']['poolFree_Rrf']).all())

    def test_RFabsorption_Matrix_poolBound_Rrf_dualSat(self):
        self.assertTrue((self.system.poolBound_Rrf_dualSat == CONFIG_SYSTEM['compute']['poolBound_Rrf_dualSat']).all())

    def test_RFabsorption_Matrix_poolBound_Rrf_singleSat_Positive(self):
        self.assertTrue((self.system.poolBound_Rrf_singleSat_Positive == CONFIG_SYSTEM['compute']['poolBound_Rrf_singleSat_Positive']).all())

    def test_RFabsorption_Matrix_poolBound_Rrf_singleSat_Negative(self):
        self.assertTrue((self.system.poolBound_Rrf_singleSat_Negative == CONFIG_SYSTEM['compute']['poolBound_Rrf_singleSat_Negative']).all())

    def test_resetComputedAttributes_poolBound_RFabsorptionMatrices(self):
        self.system.poolBound_T2 = CONFIG_SYSTEM['init']['poolBound_T2'] * 1e3
        self.assertTrue((self.system.poolBound_Rrf_dualSat != CONFIG_SYSTEM['compute']['poolBound_Rrf_dualSat']).any())
        self.assertTrue((self.system.poolBound_Rrf_singleSat_Positive != CONFIG_SYSTEM['compute']['poolBound_Rrf_singleSat_Positive']).any())
        self.assertTrue((self.system.poolBound_Rrf_singleSat_Negative != CONFIG_SYSTEM['compute']['poolBound_Rrf_singleSat_Negative']).any())

    def test_resetComputedAttributes_poolFree_Rrf(self):
        self.system.poolFree_T2 = CONFIG_SYSTEM['init']['poolFree_T2'] * 1e3
        self.assertTrue((self.system.poolFree_Rrf != CONFIG_SYSTEM['compute']['poolFree_Rrf']).any())

    def test_resetComputedAttributes_poolBound_omegaLocalField(self):
        self.system.poolBound_T2 = CONFIG_SYSTEM['init']['poolBound_T2'] * 1e3
        self.assertTrue(self.system.poolBound_omegaLocalField != CONFIG_SYSTEM['compute']['poolBound_omegaLocalField'])

    def test_resetComputedAttributes_N_pools_from_poolFree_T2(self):
        self.system.poolFree_T2 = array([CONFIG_SYSTEM['init']['poolFree_T2'], CONFIG_SYSTEM['init']['poolFree_T2']]).flatten()
        with self.assertRaises(RuntimeError):
            self.system.N_pools

    def test_resetComputedAttributes_N_pools_from_poolBound_T2(self):
        self.system.poolBound_T2 = array([CONFIG_SYSTEM['init']['poolBound_T2'], CONFIG_SYSTEM['init']['poolBound_T2']]).flatten()
        with self.assertRaises(RuntimeError):
            self.system.N_pools

    def test_resetComputedAttributes_N_pools_from_poolBound_T1D(self):
        self.system.poolBound_T1D = array([CONFIG_SYSTEM['init']['poolBound_T1D'], CONFIG_SYSTEM['init']['poolBound_T1D']]).flatten()
        with self.assertRaises(RuntimeError):
            self.system.N_pools


class TestLineshapes(TestCase):
    def setUp(self):
        self.system = System(**CONFIG_SYSTEM['init'])

    def test_Lorentzian(self):
        self.assertEqual(self.system.Lorentzian(self.system.poolBound_T2), 2.6671533855137817e-06)

    def test_Gaussian(self):
        self.assertEqual(self.system.Gaussian(self.system.poolBound_T2), 3.621630854421752e-06)

    def test_SuperLorentzian(self):
        self.assertEqual(self.system.SuperLorentzian(self.system.poolBound_T2), 3.7463817768960933e-06)

    def test_PampelSuperLorentzian(self):
        self.assertEqual(self.system.PampelSuperLorentzian(self.system.poolBound_T2), 3.7463848626091833e-06)

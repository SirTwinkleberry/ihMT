"""
tests/test_system.py
Copyright (C) 2026  Timothy Anderson

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from ihmt.system import System
from ihmt.pulse import Tukey

from unittest import TestCase, skip
from numpy import sqrt, array

from numpy import set_printoptions
from sys import maxsize

set_printoptions(precision=maxsize)

CONFIG_TUKEY = {
    "init": {
        "duration": 1e-3,
        "shape": 0.3,
        "flipAngle": 299,
        "offset": 7e3,
    }
}

CONFIG_SYSTEM = {
    "init": {
        "pulse": Tukey(**CONFIG_TUKEY["init"]),
        "poolFree_M0": 1,
        "poolFree_T1": 1,
        "poolFree_T2": 0.1,
        "poolFreeBound_exchangeRate": 10,
        "poolBound_lineshapeAsymmetry": 0,
        "poolBound_M0": 0.1,
        "poolBound_T1": 1,
        "poolBound_T2": 1e-5,
        "poolBound_T1D": 1e-2,
    },
    "compute": {
        "poolBound_omegaLocalField": 1.0 / (sqrt(15) * 1e-5),
        "N_pools": 2,
        "poolFree_Rrf": array(
            [[-0.15831672264766541, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
        ),
        "poolBound_Rrf_dualSat": array(
            [
                [0.0, 0.0, 0.0],
                [0.0, -360.44973207272835, -0.0],
                [0.0, -0.0, -1045.903901038725],
            ]
        ),
        "poolBound_Rrf_singleSat_Negative": array(
            [
                [0.0, 0.0, 0.0],
                [0.0, -360.44973207272835, -15853407.223753296],
                [0.0, -0.023780110835629947, -1045.903901038725],
            ]
        ),
        "poolBound_Rrf_singleSat_Positive": array(
            [
                [0.0, 0.0, 0.0],
                [0.0, -360.44973207272835, 15853407.223753296],
                [0.0, 0.023780110835629947, -1045.903901038725],
            ]
        ),
    },
}


class TestSystem(TestCase):
    def setUp(self):
        self.system = System(**CONFIG_SYSTEM["init"])

    def test___init__poolFree_M0(self):
        self.assertEqual(self.system.poolFree_M0, CONFIG_SYSTEM["init"]["poolFree_M0"])

    def test___init__poolFree_T1(self):
        self.assertEqual(self.system.poolFree_T1, CONFIG_SYSTEM["init"]["poolFree_T1"])

    def test___init__poolFree_T2(self):
        self.assertEqual(self.system.poolFree_T2, CONFIG_SYSTEM["init"]["poolFree_T2"])

    def test___init__poolFreeBound_exchangeRate(self):
        self.assertEqual(
            self.system.poolFreeBound_exchangeRate,
            CONFIG_SYSTEM["init"]["poolFreeBound_exchangeRate"],
        )

    def test___init__poolBound_M0(self):
        self.assertEqual(
            self.system.poolBound_M0, CONFIG_SYSTEM["init"]["poolBound_M0"]
        )

    def test___init__poolBound_T1(self):
        self.assertEqual(
            self.system.poolBound_T1, CONFIG_SYSTEM["init"]["poolBound_T1"]
        )

    def test___init__poolBound_T2(self):
        self.assertEqual(
            self.system.poolBound_T2, CONFIG_SYSTEM["init"]["poolBound_T2"]
        )

    def test___init__poolBound_T1D(self):
        self.assertEqual(
            self.system.poolBound_T1D, CONFIG_SYSTEM["init"]["poolBound_T1D"]
        )

    def test___init__poolBound_omegaLocalField(self):
        self.assertEqual(
            self.system.poolBound_omegaLocalField,
            CONFIG_SYSTEM["compute"]["poolBound_omegaLocalField"],
        )

    def test___init__N_pools(self):
        self.assertEqual(self.system.N_pools, CONFIG_SYSTEM["compute"]["N_pools"])

    def test_RFabsorption_Matrix_poolFree_Rrf(self):
        self.assertTrue(
            (self.system.poolFree_Rrf == CONFIG_SYSTEM["compute"]["poolFree_Rrf"]).all()
        )

    def test_RFabsorption_Matrix_poolBound_Rrf_dualSat(self):
        self.assertTrue(
            (
                self.system.poolBound_Rrf_dualSat
                == CONFIG_SYSTEM["compute"]["poolBound_Rrf_dualSat"]
            ).all()
        )

    def test_RFabsorption_Matrix_poolBound_Rrf_singleSat_Positive(self):
        self.assertTrue(
            (
                self.system.poolBound_Rrf_singleSat_Positive
                == CONFIG_SYSTEM["compute"]["poolBound_Rrf_singleSat_Positive"]
            ).all()
        )

    def test_RFabsorption_Matrix_poolBound_Rrf_singleSat_Negative(self):
        self.assertTrue(
            (
                self.system.poolBound_Rrf_singleSat_Negative
                == CONFIG_SYSTEM["compute"]["poolBound_Rrf_singleSat_Negative"]
            ).all()
        )

    def test_resetComputedAttributes_poolBound_RFabsorptionMatrices(self):
        self.system.poolBound_T2 = CONFIG_SYSTEM["init"]["poolBound_T2"] * 1e3
        self.assertTrue(
            (
                self.system.poolBound_Rrf_dualSat
                != CONFIG_SYSTEM["compute"]["poolBound_Rrf_dualSat"]
            ).any()
        )
        self.assertTrue(
            (
                self.system.poolBound_Rrf_singleSat_Positive
                != CONFIG_SYSTEM["compute"]["poolBound_Rrf_singleSat_Positive"]
            ).any()
        )
        self.assertTrue(
            (
                self.system.poolBound_Rrf_singleSat_Negative
                != CONFIG_SYSTEM["compute"]["poolBound_Rrf_singleSat_Negative"]
            ).any()
        )

    def test_resetComputedAttributes_poolFree_Rrf(self):
        self.system.poolFree_T2 = CONFIG_SYSTEM["init"]["poolFree_T2"] * 1e3
        self.assertTrue(
            (self.system.poolFree_Rrf != CONFIG_SYSTEM["compute"]["poolFree_Rrf"]).any()
        )

    def test_resetComputedAttributes_poolBound_omegaLocalField(self):
        self.system.poolBound_T2 = CONFIG_SYSTEM["init"]["poolBound_T2"] * 1e3
        self.assertTrue(
            self.system.poolBound_omegaLocalField
            != CONFIG_SYSTEM["compute"]["poolBound_omegaLocalField"]
        )

    def test_errorFromMismatchedDimensions_with_poolFree_T1(self):
        with self.assertRaises(ValueError):
            self.system.poolFree_T1 = array(
                [
                    CONFIG_SYSTEM["init"]["poolFree_T1"],
                    CONFIG_SYSTEM["init"]["poolFree_T1"],
                ]
            ).flatten()

    def test_errorFromMismatchedDimensions_with_poolFree_T2(self):
        with self.assertRaises(ValueError):
            self.system.poolFree_T2 = array(
                [
                    CONFIG_SYSTEM["init"]["poolFree_T2"],
                    CONFIG_SYSTEM["init"]["poolFree_T2"],
                ]
            ).flatten()

    def test_errorFromMismatchedDimensions_with_poolBound_T1(self):
        with self.assertRaises(ValueError):
            self.system.poolBound_T1 = array(
                [
                    CONFIG_SYSTEM["init"]["poolBound_T1"],
                    CONFIG_SYSTEM["init"]["poolBound_T1"],
                ]
            ).flatten()

    def test_errorFromMismatchedDimensions_with_poolBound_T2(self):
        with self.assertRaises(ValueError):
            self.system.poolBound_T2 = array(
                [
                    CONFIG_SYSTEM["init"]["poolBound_T2"],
                    CONFIG_SYSTEM["init"]["poolBound_T2"],
                ]
            ).flatten()

    def test_errorFromMismatchedDimensions_with_poolBound_T1D(self):
        with self.assertRaises(ValueError):
            self.system.poolBound_T1D = array(
                [
                    CONFIG_SYSTEM["init"]["poolBound_T1D"],
                    CONFIG_SYSTEM["init"]["poolBound_T1D"],
                ]
            ).flatten()

    def test_reset_computed(self):
        computeds = [
            "magnetization_recovery",
            "relaxation",
            "poolFree_Rrf",
            "poolBound_Rrf_dualSat",
            "poolBound_Rrf_singleSat_Positive",
            "poolBound_Rrf_singleSat_Negative",
            "N_poolFree",
            "N_poolBound",
            "N_pools",
        ]
        for computed in computeds:
            getattr(self.system, computed)
            delattr(self.system, computed)
            self.assertFalse(hasattr(self.system, f"_{computed}"))
            getattr(self.system, computed)
            getattr(self.system, computed)
            self.assertTrue(hasattr(self.system, f"_{computed}"))

    def test_copy(self):
        tmp = self.system.copy()
        self.assertTrue((tmp.poolFree_Rrf == self.system.poolFree_Rrf).all())
        self.assertTrue((tmp.poolFree_M0 == self.system.poolFree_M0).all())
        self.assertTrue((tmp.poolFree_T1 == self.system.poolFree_T1).all())
        self.assertTrue((tmp.poolFree_T2 == self.system.poolFree_T2).all())
        self.assertTrue(
            (
                tmp.poolFreeBound_exchangeRate == self.system.poolFreeBound_exchangeRate
            ).all()
        )
        self.assertTrue(
            (
                tmp.poolBound_Rrf_singleSat_Positive
                == self.system.poolBound_Rrf_singleSat_Positive
            ).all()
        )
        self.assertTrue(
            (
                tmp.poolBound_Rrf_singleSat_Negative
                == self.system.poolBound_Rrf_singleSat_Negative
            ).all()
        )
        self.assertTrue(
            (tmp.poolBound_Rrf_dualSat == self.system.poolBound_Rrf_dualSat).all()
        )
        self.assertTrue(
            (
                tmp.poolBound_lineshapeAsymmetry
                == self.system.poolBound_lineshapeAsymmetry
            ).all()
        )
        self.assertTrue((tmp.poolBound_M0 == self.system.poolBound_M0).all())
        self.assertTrue((tmp.poolBound_T1 == self.system.poolBound_T1).all())
        self.assertTrue((tmp.poolBound_T2 == self.system.poolBound_T2).all())
        self.assertTrue((tmp.poolBound_T1D == self.system.poolBound_T1D).all())
        self.assertTrue(
            (
                tmp.poolBound_omegaLocalField == self.system.poolBound_omegaLocalField
            ).all()
        )
        self.assertTrue(
            (tmp.magnetization_recovery == self.system.magnetization_recovery).all()
        )
        self.assertTrue((tmp.relaxation == self.system.relaxation).all())
        self.assertTrue(tmp.N_poolFree == self.system.N_poolFree)
        self.assertTrue(tmp.N_poolBound == self.system.N_poolBound)
        self.assertTrue(tmp.N_pools == self.system.N_pools)
        self.assertNotEqual(tmp._get_onChanges(), self.system._get_onChanges())
        self.assertTrue(tmp.pulse.shape, self.system.pulse.shape)
        self.assertTrue(tmp.pulse.duration, self.system.pulse.duration)
        self.assertTrue(tmp.pulse.flipAngle, self.system.pulse.flipAngle)
        self.assertTrue(tmp.pulse.offset, self.system.pulse.offset)
        self.assertNotEqual(
            tmp.pulse._get_onChanges(), self.system.pulse._get_onChanges()
        )


class TestLineshapes(TestCase):
    def setUp(self):
        self.system = System(**CONFIG_SYSTEM["init"])

    def test_Lorentzian(self):
        self.assertTrue(
            (
                self.system.Lorentzian(
                    self.system.poolBound_T2, self.system.pulse.offset
                )
                == array(1.6758218963854485e-05)
            ).all()
        )

    def test_Gaussian(self):
        self.assertTrue(
            (
                self.system.Gaussian(self.system.poolBound_T2, self.system.pulse.offset)
                == array(2.2755377772531e-05)
            ).all()
        )

    def test_SuperLorentzian(self):
        self.assertTrue(
            (
                self.system.SuperLorentzian(
                    self.system.poolBound_T2, self.system.pulse.offset
                )
                == array([2.3539210935678883e-05])
            ).all()
        )

    def test_PampelSuperLorentzian(self):
        self.assertTrue(
            (
                self.system.PampelSuperLorentzian(
                    self.system.poolBound_T2, self.system.pulse.offset
                )
                == array(2.3539220258601342e-05)
            ).all()
        )

    def test_Cylindrical(self):
        with self.assertRaises(NotImplementedError):
            self.system.Cylindrical(self.system.poolBound_T2, self.system.pulse.offset)

    def test_DispersedCylindrical(self):
        with self.assertRaises(NotImplementedError):
            self.system.DispersedCylindrical(
                self.system.poolBound_T2, self.system.pulse.offset
            )

from brainhack.config import default

from unittest import TestCase

DEFAULT: dict[str, bool | int | float | str] = {
    'B1rel': 1,
    'M0a': 1,
    'T1f': 1,
    'T2f': 0.1,
    'R': 10,
    'M0b': 0.1,
    'T1b': 1,
    'T1D': 1.0e-2,
    'T2b': 1.0e-5,
    'pw': 1.0e-3,
    'dt': 1.5e-3,
    'es': 6.0e-3,
    'tr': 3,
    'turbo': 80,
    'np': 4,
    'nb': 10,
    'btr': 1.0e-1,
    'btrlast': 1.0e-3,
    'fa_sat': 200,
    'fa_rage': 5,
    'FLAG_Sine_Modulation': "BP",
    'N_altern': 1,
    'r_tukey': 0.3,
    'outPrefix': './output/',
    'export': True,
    'offset': 7000,
}


class TestImport(TestCase):
    def test_default(self):
        self.assertEqual(default, DEFAULT)

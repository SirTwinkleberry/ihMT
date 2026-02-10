from brainhack.run import SingleRun

from pathlib import Path
from copy import copy
from unittest import TestCase
from numpy import array
from scipy.io import loadmat  # type: ignore
from yaml import dump
from subprocess import check_output, STDOUT, CalledProcessError

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
    'tr': 1.387,
    'turbo': 80,
    'np': 4,
    'nb': 10,
    'btr': 1.0e-1,
    'btrlast': 1.0e-3,
    'fa_sat': 299,
    'fa_rage': 5,
    'FLAG_Sine_Modulation': "BP",
    'N_altern': 1,
    'r_tukey': 0.3,
    'outputDir': str(Path(__file__).parent / 'output'),
    'filePrefix': '',
    'export': True,
    'offset': 7000,
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


def dumpConfig(export: bool, modulation: str):
    tmp = copy(DEFAULT)
    tmp['export'] = export
    tmp['FLAG_Sine_Modulation'] = modulation
    with open(Path(tmp['outputDir']) / 'config.yaml', 'w') as file:  # type: ignore
        dump(tmp, file)


class TestRun_withoutExport(TestCase):
    @classmethod
    def setUpClass(cls):
        Path(DEFAULT['outputDir']).mkdir(parents=False, exist_ok=False)  # type: ignore

    @classmethod
    def tearDownClass(cls):
        Path(DEFAULT['outputDir']).rmdir()  # type: ignore

    def tearDown(self):
        (Path(DEFAULT['outputDir']) / 'config.yaml').unlink(missing_ok=True)  # type: ignore
        (Path(DEFAULT['outputDir']) / 'simulation.mat').unlink(missing_ok=True)  # type: ignore

    def test_run_SingleRun_CM_noExport(self):
        dumpConfig(export=False, modulation='CM')
        try:
            output = check_output([
                'python',
                str(Path(__file__).parents[1] / 'brainhack' / 'run.py'),
                str(Path(DEFAULT['outputDir']) / 'config.yaml'),  # type: ignore
            ], stderr=STDOUT)
            self.assertEqual(output, b'[0.9037829677605914, 0.09037837084448297, 0.0, 1.0]\n[0.767625258637337, 0.045410925323905185, 1.5267491627581326e-06, 1.0]\n[0.6599520592347559, 0.010208120168757757, 0.0, 1.0]\n')
        except CalledProcessError as e:
            raise RuntimeError(e.output.decode('utf-8'))

    def test_run_SingleRun_CM_checkExport(self):
        dumpConfig(export=True, modulation='CM')
        try:
            check_output([
                'python',
                str(Path(__file__).parents[1] / 'brainhack' / 'run.py'),
                str(Path(DEFAULT['outputDir']) / 'config.yaml'),  # type: ignore
            ], stderr=STDOUT)

            mat = loadmat(Path(DEFAULT['outputDir']).resolve() / (DEFAULT['filePrefix'] + 'simulation.mat'))  # type: ignore
            base = loadmat(Path(__file__).parent / 'simulator_test_singleRun_CM_checkExport.mat')  # type: ignore

            self.assertTrue((mat['MT0'] == base['MT0']).all())  # type: ignore
            self.assertTrue((mat['MTs'] == base['MTs']).all())  # type: ignore
            self.assertTrue((mat['MTd_CM'] == base['MTd_CM']).all())  # type: ignore
            del mat['__header__'], mat['MT0'], mat['MTs'], mat['MTd_CM']
            del base['__header__'], base['MT0'], base['MTs'], base['MTd_CM']

            self.assertDictEqual(mat, base)  # type: ignore
        except CalledProcessError as e:
            raise RuntimeError(e.output.decode('utf-8'))

    def test_run_SingleRun_ALT_noExport(self):
        dumpConfig(export=False, modulation='ALT')
        try:
            output = check_output([
                'python',
                str(Path(__file__).parents[1] / 'brainhack' / 'run.py'),
                str(Path(DEFAULT['outputDir']) / 'config.yaml'),  # type: ignore
            ], stderr=STDOUT)
            self.assertEqual(output, b'[0.9037829677605914, 0.09037837084448297, 0.0, 1.0]\n[0.767625258637337, 0.045410925323905185, 1.5267491627581326e-06, 1.0]\n[0.6700714351260693, 0.013280098185195757, -2.7246884677924776e-07, 1.0]\n')
        except CalledProcessError as e:
            raise RuntimeError(e.output.decode('utf-8'))

    def test_run_SingleRun_ALT_checkExport(self):
        dumpConfig(export=True, modulation='ALT')
        try:
            check_output([
                'python',
                str(Path(__file__).parents[1] / 'brainhack' / 'run.py'),
                str(Path(DEFAULT['outputDir']) / 'config.yaml'),  # type: ignore
            ], stderr=STDOUT)

            mat = loadmat(Path(DEFAULT['outputDir']).resolve() / (DEFAULT['filePrefix'] + 'simulation.mat'))  # type: ignore
            base = loadmat(Path(__file__).parent / 'simulator_test_singleRun_ALT_checkExport.mat')  # type: ignore

            self.assertTrue((mat['MT0'] == base['MT0']).all())  # type: ignore
            self.assertTrue((mat['MTs'] == base['MTs']).all())  # type: ignore
            self.assertTrue((mat['MTd_ALT'] == base['MTd_ALT']).all())  # type: ignore
            del mat['__header__'], mat['MT0'], mat['MTs'], mat['MTd_ALT']
            del base['__header__'], base['MT0'], base['MTs'], base['MTd_ALT']

            self.assertDictEqual(mat, base)  # type: ignore
        except CalledProcessError as e:
            raise RuntimeError(e.output.decode('utf-8'))

    def test_run_SingleRun_BP_noExport(self):
        dumpConfig(export=False, modulation='BP')
        try:
            output = check_output([
                'python',
                str(Path(__file__).parents[1] / 'brainhack' / 'run.py'),
                str(Path(DEFAULT['outputDir']) / 'config.yaml'),  # type: ignore
            ], stderr=STDOUT)
            self.assertEqual(output, b'[0.9037829677605914, 0.09037837084448297, 0.0, 1.0]\n[0.767625258637337, 0.045410925323905185, 1.5267491627581326e-06, 1.0]\n[0.6599520592347559, 0.010208120168757757, 0.0, 1.0]\n[0.6700714351260693, 0.013280098185195757, -2.7246884677924776e-07, 1.0]\n')
        except CalledProcessError as e:
            raise RuntimeError(e.output.decode('utf-8'))

    def test_run_SingleRun_BP_checkExport(self):
        dumpConfig(export=True, modulation='BP')
        try:
            check_output([
                'python',
                str(Path(__file__).parents[1] / 'brainhack' / 'run.py'),
                str(Path(DEFAULT['outputDir']) / 'config.yaml'),  # type: ignore
            ], stderr=STDOUT)

            mat = loadmat(Path(DEFAULT['outputDir']).resolve() / (DEFAULT['filePrefix'] + 'simulation.mat'))  # type: ignore
            base = loadmat(Path(__file__).parent / 'simulator_test_singleRun_BP_checkExport.mat')  # type: ignore

            self.assertTrue((mat['MT0'] == base['MT0']).all())  # type: ignore
            self.assertTrue((mat['MTs'] == base['MTs']).all())  # type: ignore
            self.assertTrue((mat['MTd_CM'] == base['MTd_CM']).all())  # type: ignore
            self.assertTrue((mat['MTd_ALT'] == base['MTd_ALT']).all())  # type: ignore
            del mat['__header__'], mat['MT0'], mat['MTs'], mat['MTd_CM'], mat['MTd_ALT']
            del base['__header__'], base['MT0'], base['MTs'], base['MTd_CM'], base['MTd_ALT']

            self.assertDictEqual(mat, base)  # type: ignore
        except CalledProcessError as e:
            raise RuntimeError(e.output.decode('utf-8'))

    def test_run_SingleRun_wrongModulation(self):
        dumpConfig(export=False, modulation='None')
        with self.assertRaises(ValueError):
            try:
                output = check_output([
                    'python',
                    str(Path(__file__).parents[1] / 'brainhack' / 'run.py'),
                    str(Path(DEFAULT['outputDir']) / 'config.yaml'),  # type: ignore
                ], stderr=STDOUT)
                print(output)
            except CalledProcessError as e:
                if "Incorrect `FLAG_Sine_Modulation` variable. Must be any one of `CM`, `ALT`, or `BP`." in str(e.output):
                    raise ValueError("Incorrect `FLAG_Sine_Modulation` variable. Must be any one of `CM`, `ALT`, or `BP`")
                raise RuntimeError(e.output.decode('utf-8'))

    def test_run_wrongNumberOfArguments(self):
        with self.assertRaises(SyntaxError):
            try:
                check_output([
                    'python',
                    str(Path(__file__).parents[1] / 'brainhack' / 'run.py'),
                ], stderr=STDOUT)
            except CalledProcessError as e:
                if "Running command with the wrong number of arguments." in str(e.output):
                    raise SyntaxError("Running command with the wrong number of arguments.")
                raise RuntimeError(e.output.decode('utf-8'))


class TestSingleRun(TestCase):
    success = False

    @classmethod
    def setUpClass(cls):
        Path(DEFAULT['outputDir']).mkdir(parents=False, exist_ok=False)  # type: ignore
        cls.success = True

    @classmethod
    def tearDownClass(cls):
        if cls.success:
            Path(DEFAULT['outputDir']).rmdir()  # type: ignore

    def tearDown(self):
        (Path(DEFAULT['outputDir']) / 'simulation.mat').unlink(missing_ok=True)  # type: ignore

    def test_singleRun_CM_noExport(self):
        params = copy(DEFAULT)
        params['FLAG_Sine_Modulation'] = 'CM'
        params['export'] = False
        self.assertTrue((SingleRun(**params) == CONFIG_SIMULATE['compute']['CM']).all())  # type: ignore

    def test_singleRun_CM_checkExport(self):
        params = copy(DEFAULT)
        params['FLAG_Sine_Modulation'] = 'CM'

        SingleRun(**params)  # type: ignore
        mat = loadmat(Path(params['outputDir']).resolve() / (params['filePrefix'] + 'simulation.mat'))  # type: ignore
        base = loadmat(Path(__file__).parent / 'simulator_test_singleRun_CM_checkExport.mat')  # type: ignore

        self.assertTrue((mat['MT0'] == base['MT0']).all())  # type: ignore
        self.assertTrue((mat['MTs'] == base['MTs']).all())  # type: ignore
        self.assertTrue((mat['MTd_CM'] == base['MTd_CM']).all())  # type: ignore
        del mat['__header__'], mat['MT0'], mat['MTs'], mat['MTd_CM']
        del base['__header__'], base['MT0'], base['MTs'], base['MTd_CM']

        self.assertDictEqual(mat, base)  # type: ignore

    def test_singleRun_ALT_noExport(self):
        params = copy(DEFAULT)
        params['FLAG_Sine_Modulation'] = 'ALT'
        params['export'] = False
        self.assertTrue((SingleRun(**params) == CONFIG_SIMULATE['compute']['ALT']).all())  # type: ignore

    def test_singleRun_ALT_checkExport(self):
        params = copy(DEFAULT)
        params['FLAG_Sine_Modulation'] = 'ALT'

        SingleRun(**params)  # type: ignore
        mat = loadmat(Path(params['outputDir']).resolve() / (params['filePrefix'] + 'simulation.mat'))  # type: ignore
        base = loadmat(Path(__file__).parent / 'simulator_test_singleRun_ALT_checkExport.mat')  # type: ignore

        self.assertTrue((mat['MT0'] == base['MT0']).all())  # type: ignore
        self.assertTrue((mat['MTs'] == base['MTs']).all())  # type: ignore
        self.assertTrue((mat['MTd_ALT'] == base['MTd_ALT']).all())  # type: ignore
        del mat['__header__'], mat['MT0'], mat['MTs'], mat['MTd_ALT']
        del base['__header__'], base['MT0'], base['MTs'], base['MTd_ALT']

        self.assertDictEqual(mat, base)  # type: ignore

    def test_singleRun_BP_noExport(self):
        params = copy(DEFAULT)
        params['export'] = False
        self.assertTrue((SingleRun(**params) == CONFIG_SIMULATE['compute']['BP']).all())  # type: ignore

    def test_singleRun_BP_checkExport(self):
        params = copy(DEFAULT)

        SingleRun(**params)  # type: ignore
        mat = loadmat(Path(params['outputDir']).resolve() / (params['filePrefix'] + 'simulation.mat'))  # type: ignore
        base = loadmat(Path(__file__).parent / 'simulator_test_singleRun_BP_checkExport.mat')  # type: ignore

        self.assertTrue((mat['MT0'] == base['MT0']).all())  # type: ignore
        self.assertTrue((mat['MTs'] == base['MTs']).all())  # type: ignore
        self.assertTrue((mat['MTd_CM'] == base['MTd_CM']).all())  # type: ignore
        self.assertTrue((mat['MTd_ALT'] == base['MTd_ALT']).all())  # type: ignore
        del mat['__header__'], mat['MT0'], mat['MTs'], mat['MTd_CM'], mat['MTd_ALT']
        del base['__header__'], base['MT0'], base['MTs'], base['MTd_CM'], base['MTd_ALT']

        self.assertDictEqual(mat, base)  # type: ignore

    def test_singleRun_wrongModulation(self):
        params = copy(DEFAULT)
        params['FLAG_Sine_Modulation'] = 'None'

        with self.assertRaises(ValueError):
            SingleRun(**params)  # type: ignore

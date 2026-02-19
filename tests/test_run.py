from brainhack.run import SingleRun

from pathlib import Path
from copy import deepcopy as copy
from unittest import TestCase
from numpy import array
from scipy.io import loadmat
from yaml import dump
from subprocess import check_output, STDOUT, CalledProcessError

from numpy import set_printoptions
from sys import maxsize
set_printoptions(precision=maxsize)

DEFAULT: dict[str, bool | int | float | str] = {
    'run': {
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
    },

    'log': {
        'version': 1,
        'disable_existing_loggers': False,

        'formatters': {
            'standard': {
                'format': "%(message)s"
            },
            'error': {
                'format': "%(asctime)s - %(name)s - %(levelname)s <PID %(process)d:%(processName)s> %(name)s.%(funcName)s(): %(message)s"
            },
        },

        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',  # NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
                'formatter': 'standard',
                'stream': 'ext://sys.stdout',
            },

            'error_console': {
                'class': 'logging.StreamHandler',
                'level': 'ERROR',  # NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
                'formatter': 'error',
                'stream': 'ext://sys.stderr',
            },
        },

        'root': {
            'level': 'DEBUG',
            # handlers: [console, error_console]
            'handlers': ['console', 'error_console'],
        },
    },
}

CONFIG_STEADYSTATE = {
    'compute': {
        'CM':  array([[0.9037829677605914, 0.09037837084448297, 0.0, 1.0], [0.7676252578552804, 0.045410925120816445, 1.52674916515777e-06, 1.0], [0.6599520559568383, 0.010208119191059052, 0.0, 1.0]]),
        'ALT': array([[0.9037829677605914, 0.09037837084448297, 0.0, 1.0], [0.7676252578552804, 0.045410925120816445, 1.52674916515777e-06, 1.0], [0.6700714322545925, 0.013280097321291226, -2.724688446800882e-07, 1.0]]),
        'BP':  array([[0.9037829677605914, 0.09037837084448297, 0.0, 1.0], [0.7676252578552804, 0.045410925120816445, 1.52674916515777e-06, 1.0], [0.6599520559568383, 0.010208119191059052, 0.0, 1.0], [0.6700714322545925, 0.013280097321291226, -2.724688446800882e-07, 1.0]]),
    }
}


def dumpConfig(export: bool, modulation: str):
    tmp = copy(DEFAULT)
    tmp['run']['export'] = export
    tmp['run']['FLAG_Sine_Modulation'] = modulation
    with open(Path(tmp['run']['outputDir']) / 'config.yaml', 'w') as file:
        dump(tmp, file)


class TestRun_withoutExport(TestCase):
    @classmethod
    def setUpClass(cls):
        Path(DEFAULT['run']['outputDir']).mkdir(parents=False, exist_ok=False)

    @classmethod
    def tearDownClass(cls):
        Path(DEFAULT['run']['outputDir']).rmdir()

    def tearDown(self):
        (Path(DEFAULT['run']['outputDir']) / 'config.yaml').unlink(missing_ok=True)
        (Path(DEFAULT['run']['outputDir']) / 'simulation.mat').unlink(missing_ok=True)

    def test_run_SingleRun_CM_noExport(self):
        dumpConfig(export=False, modulation='CM')
        try:
            output = check_output([
                'python',
                str(Path(__file__).parents[1] / 'brainhack' / 'run.py'),
                str(Path(DEFAULT['run']['outputDir']) / 'config.yaml'),
            ], stderr=STDOUT)
            self.assertEqual(output, str.encode('\n'.join([str(sublist) for sublist in CONFIG_STEADYSTATE['compute']['CM'].tolist()]) + '\n'))
        except CalledProcessError as e:
            raise RuntimeError(e.output.decode('utf-8'))

    def test_run_SingleRun_CM_checkExport(self):
        dumpConfig(export=True, modulation='CM')
        try:
            check_output([
                'python',
                str(Path(__file__).parents[1] / 'brainhack' / 'run.py'),
                str(Path(DEFAULT['run']['outputDir']) / 'config.yaml'),
            ], stderr=STDOUT)

            mat = loadmat(Path(DEFAULT['run']['outputDir']).resolve() / (DEFAULT['run']['filePrefix'] + 'simulation.mat'))
            base = loadmat(Path(__file__).parent / 'simulator_test_singleRun_CM_checkExport.mat')

            self.assertTrue((mat['MT0'] == base['MT0']).all())
            self.assertTrue((mat['MTs'] == base['MTs']).all())
            self.assertTrue((mat['MTd_CM'] == base['MTd_CM']).all())
            del mat['__header__'], mat['MT0'], mat['MTs'], mat['MTd_CM']
            del base['__header__'], base['MT0'], base['MTs'], base['MTd_CM']

            self.assertDictEqual(mat, base)
        except CalledProcessError as e:
            raise RuntimeError(e.output.decode('utf-8'))

    def test_run_SingleRun_ALT_noExport(self):
        dumpConfig(export=False, modulation='ALT')
        try:
            output = check_output([
                'python',
                str(Path(__file__).parents[1] / 'brainhack' / 'run.py'),
                str(Path(DEFAULT['run']['outputDir']) / 'config.yaml'),
            ], stderr=STDOUT)
            self.assertEqual(output, str.encode('\n'.join([str(sublist) for sublist in CONFIG_STEADYSTATE['compute']['ALT'].tolist()]) + '\n'))
        except CalledProcessError as e:
            raise RuntimeError(e.output.decode('utf-8'))

    def test_run_SingleRun_ALT_checkExport(self):
        dumpConfig(export=True, modulation='ALT')
        try:
            check_output([
                'python',
                str(Path(__file__).parents[1] / 'brainhack' / 'run.py'),
                str(Path(DEFAULT['run']['outputDir']) / 'config.yaml'),
            ], stderr=STDOUT)

            mat = loadmat(Path(DEFAULT['run']['outputDir']).resolve() / (DEFAULT['run']['filePrefix'] + 'simulation.mat'))
            base = loadmat(Path(__file__).parent / 'simulator_test_singleRun_ALT_checkExport.mat')

            self.assertTrue((mat['MT0'] == base['MT0']).all())
            self.assertTrue((mat['MTs'] == base['MTs']).all())
            self.assertTrue((mat['MTd_ALT'] == base['MTd_ALT']).all())
            del mat['__header__'], mat['MT0'], mat['MTs'], mat['MTd_ALT']
            del base['__header__'], base['MT0'], base['MTs'], base['MTd_ALT']

            self.assertDictEqual(mat, base)
        except CalledProcessError as e:
            raise RuntimeError(e.output.decode('utf-8'))

    def test_run_SingleRun_BP_noExport(self):
        dumpConfig(export=False, modulation='BP')
        try:
            output = check_output([
                'python',
                str(Path(__file__).parents[1] / 'brainhack' / 'run.py'),
                str(Path(DEFAULT['run']['outputDir']) / 'config.yaml'),
            ], stderr=STDOUT)
            self.assertEqual(output, str.encode('\n'.join([str(sublist) for sublist in CONFIG_STEADYSTATE['compute']['BP'].tolist()]) + '\n'))
        except CalledProcessError as e:
            raise RuntimeError(e.output.decode('utf-8'))

    def test_run_SingleRun_BP_checkExport(self):
        dumpConfig(export=True, modulation='BP')
        try:
            check_output([
                'python',
                str(Path(__file__).parents[1] / 'brainhack' / 'run.py'),
                str(Path(DEFAULT['run']['outputDir']) / 'config.yaml'),
            ], stderr=STDOUT)

            mat = loadmat(Path(DEFAULT['run']['outputDir']).resolve() / (DEFAULT['run']['filePrefix'] + 'simulation.mat'))
            base = loadmat(Path(__file__).parent / 'simulator_test_singleRun_BP_checkExport.mat')

            self.assertTrue((mat['MT0'] == base['MT0']).all())
            self.assertTrue((mat['MTs'] == base['MTs']).all())
            self.assertTrue((mat['MTd_CM'] == base['MTd_CM']).all())
            self.assertTrue((mat['MTd_ALT'] == base['MTd_ALT']).all())
            del mat['__header__'], mat['MT0'], mat['MTs'], mat['MTd_CM'], mat['MTd_ALT']
            del base['__header__'], base['MT0'], base['MTs'], base['MTd_CM'], base['MTd_ALT']

            self.assertDictEqual(mat, base)
        except CalledProcessError as e:
            raise RuntimeError(e.output.decode('utf-8'))

    def test_run_SingleRun_wrongModulation(self):
        dumpConfig(export=False, modulation='None')
        with self.assertRaises(ValueError):
            try:
                check_output([
                    'python',
                    str(Path(__file__).parents[1] / 'brainhack' / 'run.py'),
                    str(Path(DEFAULT['run']['outputDir']) / 'config.yaml'),
                ], stderr=STDOUT)
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
                    'blablabla',
                    'blablaBis'
                ], stderr=STDOUT)
            except CalledProcessError as e:
                if "Running command with the wrong number of arguments." in str(e.output):
                    raise SyntaxError("Running command with the wrong number of arguments.")
                raise RuntimeError(e.output.decode('utf-8'))


class TestSingleRun(TestCase):
    @classmethod
    def setUpClass(cls):
        Path(DEFAULT['run']['outputDir']).mkdir(parents=False, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        Path(DEFAULT['run']['outputDir']).rmdir()

    def tearDown(self):
        (Path(DEFAULT['run']['outputDir']) / 'simulation.mat').unlink(missing_ok=True)

    def test_singleRun_CM_noExport(self):
        params = copy(DEFAULT['run'])
        params['FLAG_Sine_Modulation'] = 'CM'
        params['export'] = False
        self.assertTrue((SingleRun(**params) == CONFIG_STEADYSTATE['compute']['CM']).all())

    def test_singleRun_CM_checkExport(self):
        params = copy(DEFAULT['run'])
        params['FLAG_Sine_Modulation'] = 'CM'

        SingleRun(**params)
        # (Path(params['outputDir']).resolve() / (params['filePrefix'] + 'simulation.mat')).copy(Path(params['outputDir']).resolve().parent / 'simulator_test_singleRun_CM_checkExport.mat')
        mat = loadmat(Path(params['outputDir']).resolve() / (params['filePrefix'] + 'simulation.mat'))
        base = loadmat(Path(__file__).parent / 'simulator_test_singleRun_CM_checkExport.mat')

        self.assertTrue((mat['MT0'] == base['MT0']).all())
        self.assertTrue((mat['MTs'] == base['MTs']).all())
        self.assertTrue((mat['MTd_CM'] == base['MTd_CM']).all())
        del mat['__header__'], mat['MT0'], mat['MTs'], mat['MTd_CM']
        del base['__header__'], base['MT0'], base['MTs'], base['MTd_CM']

        self.assertDictEqual(mat, base)

    def test_singleRun_ALT_noExport(self):
        params = copy(DEFAULT['run'])
        params['FLAG_Sine_Modulation'] = 'ALT'
        params['export'] = False
        self.assertTrue((SingleRun(**params) == CONFIG_STEADYSTATE['compute']['ALT']).all())

    def test_singleRun_ALT_checkExport(self):
        params = copy(DEFAULT['run'])
        params['FLAG_Sine_Modulation'] = 'ALT'

        SingleRun(**params)
        # (Path(params['outputDir']).resolve() / (params['filePrefix'] + 'simulation.mat')).copy(Path(params['outputDir']).resolve().parent / 'simulator_test_singleRun_ALT_checkExport.mat')
        mat = loadmat(Path(params['outputDir']).resolve() / (params['filePrefix'] + 'simulation.mat'))
        base = loadmat(Path(__file__).parent / 'simulator_test_singleRun_ALT_checkExport.mat')

        self.assertTrue((mat['MT0'] == base['MT0']).all())
        self.assertTrue((mat['MTs'] == base['MTs']).all())
        self.assertTrue((mat['MTd_ALT'] == base['MTd_ALT']).all())
        del mat['__header__'], mat['MT0'], mat['MTs'], mat['MTd_ALT']
        del base['__header__'], base['MT0'], base['MTs'], base['MTd_ALT']

        self.assertDictEqual(mat, base)

    def test_singleRun_BP_noExport(self):
        params = copy(DEFAULT['run'])
        params['export'] = False
        self.assertTrue((SingleRun(**params) == CONFIG_STEADYSTATE['compute']['BP']).all())

    def test_singleRun_BP_checkExport(self):
        params = copy(DEFAULT['run'])

        SingleRun(**params)
        # (Path(params['outputDir']).resolve() / (params['filePrefix'] + 'simulation.mat')).copy(Path(params['outputDir']).resolve().parent / 'simulator_test_singleRun_BP_checkExport.mat')
        mat = loadmat(Path(params['outputDir']).resolve() / (params['filePrefix'] + 'simulation.mat'))
        base = loadmat(Path(__file__).parent / 'simulator_test_singleRun_BP_checkExport.mat')

        self.assertTrue((mat['MT0'] == base['MT0']).all())
        self.assertTrue((mat['MTs'] == base['MTs']).all())
        self.assertTrue((mat['MTd_CM'] == base['MTd_CM']).all())
        self.assertTrue((mat['MTd_ALT'] == base['MTd_ALT']).all())
        del mat['__header__'], mat['MT0'], mat['MTs'], mat['MTd_CM'], mat['MTd_ALT']
        del base['__header__'], base['MT0'], base['MTs'], base['MTd_CM'], base['MTd_ALT']

        self.assertDictEqual(mat, base)

    def test_singleRun_wrongModulation(self):
        params = copy(DEFAULT['run'])
        params['FLAG_Sine_Modulation'] = 'None'

        with self.assertRaises(ValueError):
            SingleRun(**params)

from brainhack.meta import Signal
from brainhack.run import SingleRun

from pathlib import Path
from copy import deepcopy as copy
from unittest import TestCase
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
        'poolBound_lineshapeAsymmetry': 0,
        'M0b': 0.1,
        'T1b': 1,
        'T1D': 1.0e-2,
        'T2b': 1.0e-5,
        'pw': 1.0e-3,
        'dt': 1.5e-3,
        'es': 6.0e-3,
        'tr': 1.387,
        'turbo': 80,
        'N_dummyADC': 0,
        'np': 4,
        'nb': 10,
        'btr': 1.0e-1,
        'btrlast': 1.0e-3,
        'fa_sat': 299,
        'fa_rage': 5,
        'FLAG_Signal': "BPR",
        'N_altern': 1,
        'r_tukey': 0.3,
        'outputDir': str(Path(__file__).parent / 'output'),
        'filePrefix': '',
        'export': True,
        'offset': 7000,
        'output_fullVector': True,
        'export_read': True,
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

CONFIG_SIMULATOR = {
    'init': {
        'output_vectorSlice': slice(None),
        'export_readMatrix': True,
    },
    'compute': {
        'ihMTR_CM':  dict(
            MT0=[0.9037829677605911, 0.09037837084448294, 0.0, 1.0],
            MTs_Positive=[0.768369253684603, 0.0454539042950363, 1.5281848336861655e-06, 1.0],
            MTs_Negative=[0.768369253684603, 0.0454539042950363, 1.5281848336861655e-06, 1.0],
            MTd_CM=[0.6606360409781923, 0.010218152542836825, 0.0, 1.0],
            readout=[[0.984485836436591, 0.05771551658429958, 0.0, 0.005982035946064735], [0.005749589161890545, 0.9363024474696356, 0.0, 0.0005982035946064736], [0.0, 0.0, 0.5488116360940265, 0.0], [0.0, 0.0, 0.0, 1.0]]
        ),
        'ihMTR_ALT': dict(
            MT0=[0.9037829677605911, 0.09037837084448294, 0.0, 1.0],
            MTs_Positive=[0.768369253684603, 0.0454539042950363, 1.5281848336861655e-06, 1.0],
            MTs_Negative=[0.768369253684603, 0.0454539042950363, 1.5281848336861655e-06, 1.0],
            MTd_ALT=[0.6707639083635117, 0.013293125187180439, -2.727313124262742e-07, 1.0],
            readout=[[0.984485836436591, 0.05771551658429958, 0.0, 0.005982035946064735], [0.005749589161890545, 0.9363024474696356, 0.0, 0.0005982035946064736], [0.0, 0.0, 0.5488116360940265, 0.0], [0.0, 0.0, 0.0, 1.0]]
        ),
        'BPR':  dict(
            MT0=[0.9037829677605911, 0.09037837084448294, 0.0, 1.0],
            MTd_ALT=[0.6707639083635117, 0.013293125187180439, -2.727313124262742e-07, 1.0],
            MTd_CM=[0.6606360409781923, 0.010218152542836825, 0.0, 1.0],
            readout=[[0.984485836436591, 0.05771551658429958, 0.0, 0.005982035946064735], [0.005749589161890545, 0.9363024474696356, 0.0, 0.0005982035946064736], [0.0, 0.0, 0.5488116360940265, 0.0], [0.0, 0.0, 0.0, 1.0]]
        ),
    }
}

def dumpConfig(export: bool, signal: str):
    tmp = copy(DEFAULT)
    tmp['run']['export'] = export
    tmp['run']['FLAG_Signal'] = signal
    # tmp['run']['filePrefix'] = f'{signal}_'
    with open(Path(tmp['run']['outputDir']) / 'config.yaml', 'w') as file:
        dump(tmp, file)


class TestRun_withoutExport(TestCase):
    @classmethod
    def setUpClass(cls):
        Path(DEFAULT['run']['outputDir']).mkdir(parents=False, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        Path(DEFAULT['run']['outputDir']).rmdir()

    def tearDown(self):
        (Path(DEFAULT['run']['outputDir']) / 'config.yaml').unlink(missing_ok=True)
        (Path(DEFAULT['run']['outputDir']) / 'simulation.mat').unlink(missing_ok=True)

    def test_run_SingleRun_CM_noExport(self):
        dumpConfig(export=False, signal='ihMTR_CM')
        try:
            output = check_output([
                'python',
                str(Path(__file__).parents[1] / 'brainhack' / 'run.py'),
                str(Path(DEFAULT['run']['outputDir']) / 'config.yaml'),
            ], stderr=STDOUT)
            self.assertEqual(output, str.encode('\n'.join([f'{key}: {str(sublist)}' for key, sublist in CONFIG_SIMULATOR['compute']['ihMTR_CM'].items()]) + '\n'))
        except CalledProcessError as e:
            raise RuntimeError(e.output.decode('utf-8'))

    def test_run_SingleRun_CM_checkExport(self):
        dumpConfig(export=True, signal='ihMTR_CM')
        try:
            check_output([
                'python',
                str(Path(__file__).parents[1] / 'brainhack' / 'run.py'),
                str(Path(DEFAULT['run']['outputDir']) / 'config.yaml'),
            ], stderr=STDOUT)

            mat = loadmat(Path(DEFAULT['run']['outputDir']).resolve() / (DEFAULT['run']['filePrefix'] + 'simulation.mat'))
            base = loadmat(Path(__file__).parent / 'simulator_test_singleRun_CM_checkExport.mat')

            self.assertTrue((mat['MT0'] == base['MT0']).all())
            self.assertTrue((mat['MTs_Positive'] == base['MTs_Positive']).all())
            self.assertTrue((mat['MTs_Negative'] == base['MTs_Negative']).all())
            self.assertTrue((mat['MTd_CM'] == base['MTd_CM']).all())
            self.assertTrue((mat['readout'] == base['readout']).all())
            del mat['__header__'], mat['MT0'], mat['MTs_Positive'], mat['MTs_Negative'], mat['MTd_CM'], mat['readout']
            del base['__header__'], base['MT0'], base['MTs_Positive'], base['MTs_Negative'], base['MTd_CM'], base['readout']

            self.assertDictEqual(mat, base)
        except CalledProcessError as e:
            raise RuntimeError(e.output.decode('utf-8'))

    def test_run_SingleRun_ALT_noExport(self):
        dumpConfig(export=False, signal='ihMTR_ALT')
        try:
            output = check_output([
                'python',
                str(Path(__file__).parents[1] / 'brainhack' / 'run.py'),
                str(Path(DEFAULT['run']['outputDir']) / 'config.yaml'),
            ], stderr=STDOUT)
            self.assertEqual(output, str.encode('\n'.join([f'{key}: {str(sublist)}' for key, sublist in CONFIG_SIMULATOR['compute']['ihMTR_ALT'].items()]) + '\n'))
        except CalledProcessError as e:
            raise RuntimeError(e.output.decode('utf-8'))

    def test_run_SingleRun_ALT_checkExport(self):
        dumpConfig(export=True, signal='ihMTR_ALT')
        try:
            check_output([
                'python',
                str(Path(__file__).parents[1] / 'brainhack' / 'run.py'),
                str(Path(DEFAULT['run']['outputDir']) / 'config.yaml'),
            ], stderr=STDOUT)

            mat = loadmat(Path(DEFAULT['run']['outputDir']).resolve() / (DEFAULT['run']['filePrefix'] + 'simulation.mat'))
            base = loadmat(Path(__file__).parent / 'simulator_test_singleRun_ALT_checkExport.mat')

            self.assertTrue((mat['MT0'] == base['MT0']).all())
            self.assertTrue((mat['MTs_Positive'] == base['MTs_Positive']).all())
            self.assertTrue((mat['MTs_Negative'] == base['MTs_Negative']).all())
            self.assertTrue((mat['MTd_ALT'] == base['MTd_ALT']).all())
            self.assertTrue((mat['readout'] == base['readout']).all())
            del mat['__header__'], mat['MT0'], mat['MTs_Positive'], mat['MTs_Negative'], mat['MTd_ALT'], mat['readout']
            del base['__header__'], base['MT0'], base['MTs_Positive'], base['MTs_Negative'], base['MTd_ALT'], base['readout']

            self.assertDictEqual(mat, base)
        except CalledProcessError as e:
            raise RuntimeError(e.output.decode('utf-8'))

    def test_run_SingleRun_BP_noExport(self):
        dumpConfig(export=False, signal='BPR')
        try:
            output = check_output([
                'python',
                str(Path(__file__).parents[1] / 'brainhack' / 'run.py'),
                str(Path(DEFAULT['run']['outputDir']) / 'config.yaml'),
            ], stderr=STDOUT)
            self.assertEqual(output, str.encode('\n'.join([f'{key}: {str(sublist)}' for key, sublist in CONFIG_SIMULATOR['compute']['BPR'].items()]) + '\n'))
        except CalledProcessError as e:
            raise RuntimeError(e.output.decode('utf-8'))

    def test_run_SingleRun_BP_checkExport(self):
        dumpConfig(export=True, signal='BPR')
        try:
            check_output([
                'python',
                str(Path(__file__).parents[1] / 'brainhack' / 'run.py'),
                str(Path(DEFAULT['run']['outputDir']) / 'config.yaml'),
            ], stderr=STDOUT)

            mat = loadmat(Path(DEFAULT['run']['outputDir']).resolve() / (DEFAULT['run']['filePrefix'] + 'simulation.mat'))
            base = loadmat(Path(__file__).parent / 'simulator_test_singleRun_BP_checkExport.mat')

            self.assertTrue((mat['MT0'] == base['MT0']).all())
            self.assertTrue((mat['MTd_CM'] == base['MTd_CM']).all())
            self.assertTrue((mat['MTd_ALT'] == base['MTd_ALT']).all())
            self.assertTrue((mat['readout'] == base['readout']).all())
            del mat['__header__'], mat['MT0'], mat['MTd_CM'], mat['MTd_ALT'], mat['readout']
            del base['__header__'], base['MT0'], base['MTd_CM'], base['MTd_ALT'], base['readout']

            self.assertDictEqual(mat, base)
        except CalledProcessError as e:
            raise RuntimeError(e.output.decode('utf-8'))

    def test_run_SingleRun_wrongSignal(self):
        dumpConfig(export=False, signal='None')
        with self.assertRaises(ValueError):
            try:
                check_output([
                    'python',
                    str(Path(__file__).parents[1] / 'brainhack' / 'run.py'),
                    str(Path(DEFAULT['run']['outputDir']) / 'config.yaml'),
                ], stderr=STDOUT)
            except CalledProcessError as e:
                if "Incorrect signal flag. Must be any one or combinations of" in str(e.output):
                    raise ValueError("Incorrect signal flag. Must be any one or combinations of ...")
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
        params['FLAG_Signal'] = 'ihMTR_CM'
        params['export'] = False
        out = SingleRun(**params)
        for key, val in out.items():
            out[key] = val.tolist()
        # del out['readout']
        self.assertDictEqual(out, CONFIG_SIMULATOR['compute']['ihMTR_CM'])

    def test_singleRun_CM_checkExport(self):
        params = copy(DEFAULT['run'])
        params['FLAG_Signal'] = 'ihMTR_CM'

        SingleRun(**params)
        # (Path(params['outputDir']).resolve() / (params['filePrefix'] + 'simulation.mat')).copy(Path(params['outputDir']).resolve().parent / 'simulator_test_singleRun_CM_checkExport.mat')
        mat = loadmat(Path(params['outputDir']).resolve() / (params['filePrefix'] + 'simulation.mat'))
        base = loadmat(Path(__file__).parent / 'simulator_test_singleRun_CM_checkExport.mat')

        self.assertTrue((mat['MT0'] == base['MT0']).all())
        self.assertTrue((mat['MTs_Positive'] == base['MTs_Positive']).all())
        self.assertTrue((mat['MTs_Negative'] == base['MTs_Negative']).all())
        self.assertTrue((mat['MTd_CM'] == base['MTd_CM']).all())
        self.assertTrue((mat['readout'] == base['readout']).all())
        del mat['__header__'], mat['MT0'], mat['MTs_Positive'], mat['MTs_Negative'], mat['MTd_CM'], mat['readout']
        del base['__header__'], base['MT0'], base['MTs_Positive'], base['MTs_Negative'], base['MTd_CM'], base['readout']

        self.assertDictEqual(mat, base)

    def test_singleRun_ALT_noExport(self):
        params = copy(DEFAULT['run'])
        params['FLAG_Signal'] = 'ihMTR_ALT'
        params['export'] = False
        out = SingleRun(**params)
        for key, val in out.items():
            out[key] = val.tolist()
        # del out['readout']
        self.assertDictEqual(out, CONFIG_SIMULATOR['compute']['ihMTR_ALT'])

    def test_singleRun_ALT_checkExport(self):
        params = copy(DEFAULT['run'])
        params['FLAG_Signal'] = 'ihMTR_ALT'

        SingleRun(**params)
        # (Path(params['outputDir']).resolve() / (params['filePrefix'] + 'simulation.mat')).copy(Path(params['outputDir']).resolve().parent / 'simulator_test_singleRun_ALT_checkExport.mat')
        mat = loadmat(Path(params['outputDir']).resolve() / (params['filePrefix'] + 'simulation.mat'))
        base = loadmat(Path(__file__).parent / 'simulator_test_singleRun_ALT_checkExport.mat')

        self.assertTrue((mat['MT0'] == base['MT0']).all())
        self.assertTrue((mat['MTs_Positive'] == base['MTs_Positive']).all())
        self.assertTrue((mat['MTs_Negative'] == base['MTs_Negative']).all())
        self.assertTrue((mat['MTd_ALT'] == base['MTd_ALT']).all())
        self.assertTrue((mat['readout'] == base['readout']).all())
        del mat['__header__'], mat['MT0'], mat['MTs_Positive'], mat['MTs_Negative'], mat['MTd_ALT'], mat['readout']
        del base['__header__'], base['MT0'], base['MTs_Positive'], base['MTs_Negative'], base['MTd_ALT'], base['readout']

        self.assertDictEqual(mat, base)

    def test_singleRun_BP_noExport(self):
        params = copy(DEFAULT['run'])
        params['export'] = False
        out = SingleRun(**params)
        for key, val in out.items():
            out[key] = val.tolist()
        # del out['readout']
        self.assertDictEqual(out, CONFIG_SIMULATOR['compute']['BPR'])

    def test_singleRun_BP_checkExport(self):
        params = copy(DEFAULT['run'])

        SingleRun(**params)
        # (Path(params['outputDir']).resolve() / (params['filePrefix'] + 'simulation.mat')).copy(Path(params['outputDir']).resolve().parent / 'simulator_test_singleRun_BP_checkExport.mat')
        mat = loadmat(Path(params['outputDir']).resolve() / (params['filePrefix'] + 'simulation.mat'))
        base = loadmat(Path(__file__).parent / 'simulator_test_singleRun_BP_checkExport.mat')

        self.assertTrue((mat['MT0'] == base['MT0']).all())
        self.assertTrue((mat['MTd_CM'] == base['MTd_CM']).all())
        self.assertTrue((mat['MTd_ALT'] == base['MTd_ALT']).all())
        self.assertTrue((mat['readout'] == base['readout']).all())
        del mat['__header__'], mat['MT0'], mat['MTd_CM'], mat['MTd_ALT'], mat['readout']
        del base['__header__'], base['MT0'], base['MTd_CM'], base['MTd_ALT'], base['readout']

        self.assertDictEqual(mat, base)

    def test_singleRun_wrongSignal(self):
        params = copy(DEFAULT['run'])
        params['FLAG_Signal'] = 'None'

        with self.assertRaises(ValueError):
            SingleRun(**params)

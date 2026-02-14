from brainhack.config import default

from typing import Any
from unittest import TestCase

DEFAULT: dict[str, dict[str, Any]] = {
    'run': {'B1rel': 1, 'M0a': 1, 'T1f': 1, 'T2f': 0.1, 'R': 10, 'M0b': 0.1, 'T1b': 1, 'T1D': 0.01, 'T2b': 1e-05, 'pw': 0.001, 'dt': 0.0015, 'es': 0.006, 'tr': 3, 'turbo': 80, 'np': 4, 'nb': 10, 'btr': 0.1, 'btrlast': 0.001, 'fa_sat': 200, 'fa_rage': 5, 'FLAG_Sine_Modulation': 'BP', 'N_altern': 1, 'r_tukey': 0.3, 'outputDir': './output/', 'filePrefix': '', 'export': True, 'offset': 7000},
    'log': {'version': 1, 'disable_existing_loggers': False, 'formatters': {'standard': {'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'}, 'error': {'format': '%(asctime)s - %(name)s - %(levelname)s <PID %(process)d:%(processName)s> %(name)s.%(funcName)s(): %(message)s'}}, 'handlers': {'root_file_handler': {'class': 'logging.FileHandler', 'level': 'INFO', 'formatter': 'standard', 'filename': './output/logs.txt', 'mode': 'w'}, 'debug_root_file_handler': {'class': 'logging.FileHandler', 'level': 'DEBUG', 'formatter': 'error', 'filename': './output/logs_debug.txt', 'mode': 'w'}, 'console': {'class': 'logging.StreamHandler', 'level': 'INFO', 'formatter': 'standard', 'stream': 'ext://sys.stdout'}, 'error_console': {'class': 'logging.StreamHandler', 'level': 'ERROR', 'formatter': 'error', 'stream': 'ext://sys.stderr'}}, 'root': {'level': 'DEBUG', 'handlers': ['console', 'error_console', 'root_file_handler', 'debug_root_file_handler']}}
}


class TestImport(TestCase):
    def test_default(self):
        self.assertEqual(default, DEFAULT)

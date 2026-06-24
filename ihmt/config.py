"""
ihmt/config.py
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

from logging import getLogger, NullHandler
from pathlib import Path
from yaml import safe_load, safe_dump
from typing import Any
from copy import deepcopy

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug("`config` module loaded successfully")


class Config(dict):
    def __init__(self, mapping: Any):
        super().__init__(mapping)

        self._check_run_keys()
        self._check_log_keys()

    def to_filename(self, fullpath: str | Path):
        with open(Path(fullpath), "w") as f:
            safe_dump(self, f)

    def copy(self):
        return deepcopy(self)

    def _check_run_keys(self): ...

    def _check_log_keys(self): ...


BP_3T: Config
MC_3T: Config
CM_3T: Config
ALT_3T: Config

BP_7T: Config
MC_7T: Config
CM_7T: Config
ALT_7T: Config

_configNames = [
    "BP_3T",
    "MC_3T",
    "CM_3T",
    "ALT_3T",
    "BP_7T",
    "MC_7T",
    "CM_7T",
    "ALT_7T",
]

logging: dict
with open(Path(__file__).parent / "configs" / "logging.yaml") as f:
    logging = safe_load(f)

default: Config
with open(Path(__file__).parent / "configs" / "default.yaml") as f:
    default = Config(safe_load(f))

for filename in _configNames:
    path = Path(__file__).parent / "configs" / (filename + ".yaml")
    with open(path, "r") as f:
        try:
            exec(f"{filename}" + " = Config({'run': safe_load(f)} | {'log': logging})")
            logger.debug(f"<{path}> configuration file loaded successfully.")
        except Exception as e:
            logger.error(e)

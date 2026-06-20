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
from yaml import safe_load  # noqa: F401
from typing import Any

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug("`config` module loaded successfully")


default: Config
BP_3T: Config
MC_3T: Config
BP_7T: Config
MC_7T: Config


class Config(dict):
    def __init__(self, mapping: Any):
        super().__init__(mapping)

    def as_dict(self): ...

    def to_file(self): ...

    def __getitem__(self, subscript: str):
        return dict.__getitem__(self, subscript)


for file in (Path(__file__).parent / "configs").glob("*.yaml"):
    with open(file, "r") as f:
        try:
            exec(f"{file.stem} = safe_load(f)")
            logger.debug(f"<{file}> configuration file loaded successfully.")
        except Exception as e:
            logger.error(e)

from logging import getLogger, NullHandler
from pathlib import Path
from yaml import safe_load  # noqa: F401
from typing import Any

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug('`config` module loaded successfully')


default: Config
BP_3T  : Config
MC_3T  : Config
BP_7T  : Config
MC_7T  : Config


class Config(dict):
    def __init__(self, mapping: Any):
        super().__init__(mapping)

    def as_dict(self):
        ...

    def to_file(self):
        ...

    def __getitem__(self, subscript: str):
        return dict.__getitem__(self, subscript)


for file in (Path(__file__).parent / 'configs').glob('*.yaml'):
    with open(file, 'r') as f:
        try:
            exec(f'{file.stem} = safe_load(f)')
            logger.debug(f"<{file}> configuration file loaded successfully.")
        except Exception as e:
            logger.error(e)

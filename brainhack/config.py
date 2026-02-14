from logging import getLogger, NullHandler
from pathlib import Path
from yaml import safe_load  # noqa: F401
from sys import path
try:
    path.index(str(Path(__file__).parents[1].resolve()))
except ValueError:
    path.append(str(Path(__file__).parents[1].resolve()))

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug('`config` module loaded successfully')


default: dict['str', bool | int | float | str]

for file in (Path(__file__).parent / 'configs').glob('*.yaml'):
    with open(file, 'r') as f:
        exec(f'{file.stem} = safe_load(f)')

from logging import getLogger, NullHandler
from pathlib import Path
from yaml import safe_load  # noqa: F401

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug('`config` module loaded successfully')


default: dict['str', bool | int | float | str]

for file in (Path(__file__).parent / 'configs').glob('*.yaml'):
    with open(file, 'r') as f:
        try:
            exec(f'{file.stem} = safe_load(f)')
            logger.debug(f"<{file}> configuration file loaded successfully.")
        except Exception as e:
            logger.error(e)

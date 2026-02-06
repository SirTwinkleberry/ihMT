from pathlib import Path
from yaml import safe_load  # type: ignore # noqa: F401


default: dict['str', bool | int | float | str]

for file in (Path(__file__).parent / 'configs').glob('*.yaml'):
    with open(file, 'r') as f:
        exec(f'{file.stem} = safe_load(f)')

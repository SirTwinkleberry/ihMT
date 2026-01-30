from pathlib import Path
from yaml import safe_load


for file in (Path(__file__).parent / 'configs').glob('*.yaml'):
    with open(file, 'r') as f:
        exec(f'{file.stem} = safe_load(f)')

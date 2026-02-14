from logging import getLogger, NullHandler, StreamHandler, INFO
from logging.config import dictConfig
from sys import maxsize
from typing import Any
from scipy.io import savemat
from numpy import float64, set_printoptions
from numpy.typing import NDArray
from yaml import safe_load
from sys import argv
from pathlib import Path
from sys import path
try:
    path.index(str(Path(__file__).parents[1].resolve()))
except ValueError:
    path.append(str(Path(__file__).parents[1].resolve()))

from brainhack.pulse import Tukey
from brainhack.sequence import Sequence, Modulation
from brainhack.system import System
from brainhack.simulator import SteadyState

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug('`run` module loaded successfully')


def SingleRun(M0a: float, T1f: float, T2f: float, R: float, M0b: float, T1b: float, T1D: float, T2b: float, pw: float, dt: float, es: float, tr: float, turbo: int, np: int, nb: int, btr: float, btrlast: float, fa_sat: float, fa_rage: float, FLAG_Sine_Modulation: str, N_altern: int, r_tukey: float, outputDir: str, filePrefix: str, export: bool, offset: float, *args: Any, **kwargs: Any) -> tuple[NDArray[float64], ...]:
    """_summary_

    Parameters
    ----------
    M0a : float
        _description_
    T1f : float
        _description_
    T2f : float
        _description_
    R : float
        _description_
    M0b : float
        _description_
    T1b : float
        _description_
    T1D : float
        _description_
    T2b : float
        _description_
    pw : float
        _description_
    dt : float
        _description_
    es : float
        _description_
    tr : float
        _description_
    turbo : int
        _description_
    np : int
        _description_
    nb : int
        _description_
    btr : float
        _description_
    btrlast : float
        _description_
    fa_sat : float
        _description_
    fa_rage : float
        _description_
    FLAG_Sine_Modulation : str
        _description_
    N_altern : int
        _description_
    r_tukey : float
        _description_
    outputDirr : str
        _description_
    filePrefix : str
        _description_
    export : bool
        _description_
    offset : float
        _description_

    Returns
    -------
    tuple[NDArray[float64], ...]
        _description_

    Raises
    ------
    RuntimeError
        _description_
    """
    logger.debug(locals())

    if FLAG_Sine_Modulation.upper() == "CM":
        modulation = Modulation.CM
    elif FLAG_Sine_Modulation.upper() == "ALT":
        modulation = Modulation.ALT
    elif FLAG_Sine_Modulation.upper() == "BP":
        modulation = Modulation.BP
    else:
        raise ValueError("Incorrect `FLAG_Sine_Modulation` variable. Must be any one of `CM`, `ALT`, or `BP`.")

    pulse = Tukey(
        duration=pw,
        shape=r_tukey,
        flipAngle=fa_sat,
        offset=offset
    )
    sequence = Sequence(
        modulation=modulation,
        pulse=pulse,
        N_pulsePerOffset=N_altern,
        N_pulse=np,
        N_burst=nb,
        N_adc=turbo,
        dt_interPulse=dt,
        TR_burst=btr,
        dt_lastBurst=btrlast,
        es=es,
        tr=tr,
        readout_flipAngle=fa_rage
    )
    system = System(
        pulse=pulse,
        poolFree_M0=M0a,
        poolFree_T1=T1f,
        poolFree_T2=T2f,
        poolFreeBound_exchangeRate=R,
        poolBound_M0=M0b,
        poolBound_T1=T1b,
        poolBound_T2=T2b,
        poolBound_T1D=T1D
    )

    arrays: tuple[NDArray[float64], ...] = SteadyState(system, sequence)

    if export:
        Path(outputDir).resolve().mkdir(parents=True, exist_ok=True)

        outDict: dict[str, NDArray[float64]] = {
            'MT0': arrays[0],
            'MTs': arrays[1],
        }

        for i, MTd in enumerate(arrays[2:]):
            suffix: str = ''
            if Modulation.BP in modulation:
                if i == 0:
                    suffix = 'CM'
                elif i == 1:
                    suffix = 'ALT'
                else:
                    RuntimeError("`MTds` should not be larger than 2 elements (CM, ALT)")
            elif Modulation.ALT in modulation:
                suffix = 'ALT'
            elif Modulation.CM in modulation:
                suffix = 'CM'
            else:
                NotImplementedError("`modulation` has flag enabled outside of implemented list.")

            outDict[f'MTd_{suffix}'] = MTd

        savemat(Path(outputDir).resolve() / (filePrefix + 'simulation.mat'), outDict, do_compression=True)

    return arrays


if __name__ == '__main__':
    if len(argv) > 2:
        raise SyntaxError(
            f"""
            Running command with the wrong number of arguments.
            Expecting: `{argv[0]} [path/to/config.yaml]`
            Received: `{' '.join(argv)}`
            """
        )
    if len(argv) == 2:
        with open(argv[1], 'r') as file:
            config = safe_load(file)
            configPath = Path(argv[1]).resolve()
    else:
        from config import default
        config = default
        configPath = Path(__file__) / 'configs' / 'default.yaml'

    if 'log' in config.keys():
        dictConfig(config['log'])
        log = getLogger()
        log.debug(f'Logging configuration successful! Configuration file found at <{configPath}>.')
    else:
        log = getLogger()
        log.addHandler(StreamHandler())
        log.setLevel(INFO)

    if 'run' not in config.keys():
        log.critical(f'Missing `run` category from configuration file <{configPath}>.')
        raise ValueError(f'Missing `run` category from configuration file <{configPath}>.')

    set_printoptions(precision=maxsize)
    for output in SingleRun(**config['run']):
        log.info(output.tolist())

# Note:
# This current (incomplete) version has implemented logic for 1 free pool and 1 bound pool only
# There needs to be a generalization of the construction of the operators in system.py and simulator.py
# The Simulate function in simulator.py also does not include logic to return signal values on a readout basis
# The general nomenclature (variable, function, class, and file names) is open to changes
# Parameter names in the Main function of main.py should match exactly the names of the parameters in the config files for Main(**config) to work as intended
# The choice of using json (comments not possible within the file) or yaml (comments possible within the file) config files is left open, my personal favorite is yaml

from logging import getLogger, NullHandler, StreamHandler, INFO
from logging.config import dictConfig
from datetime import datetime
from sys import maxsize
from typing import Any
from scipy.io import savemat
from numpy import int64, float64, set_printoptions
from numpy.typing import NDArray
from yaml import safe_load
from sys import argv
from pathlib import Path
from copy import deepcopy

from brainhack.pulse import Tukey
from brainhack.sequence import Sequence, Modulation
from brainhack.system import System
from brainhack.simulator import Simulator

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug('`run` module loaded successfully')


def SingleRun(M0a: float, T1f: float, T2f: float, R: float, M0b: float, T1b: float, T1D: float, T2b: float, pw: float, dt: float, es: float, tr: float, turbo: int, N_dummyADC: int, np: int, nb: int, btr: float, btrlast: float, fa_sat: float, fa_rage: float, FLAG_Sine_Modulation: str, N_altern: int, r_tukey: float, outputDir: str, filePrefix: str, export: bool, offset: float, output_fullVector: bool, export_read: bool, *args: Any, **kwargs: Any) -> dict[str, NDArray[float64]]:
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
    N_dummyADC : int
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
    export_read : bool
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
        error = f"Incorrect `FLAG_Sine_Modulation` variable. Must be any one of `CM`, `ALT`, or `BP`. Received `{repr(FLAG_Sine_Modulation)}`."
        logger.critical(error)
        raise ValueError(error)

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
        N_dummyADC=N_dummyADC,
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

    simulator = Simulator(
        system=system, 
        sequence=sequence,
        output_vectorSlice=slice(None) if output_fullVector else slice(1),
        export_readMatrix=export_read
    )

    arrays: dict[str, NDArray[float64]] = simulator.SteadyState()

    if export:
        Path(outputDir).resolve().mkdir(parents=True, exist_ok=True)
        savemat(Path(outputDir).resolve() / (filePrefix + 'simulation.mat'), arrays, do_compression=True)

    return arrays


def ManyRuns(simulator: Simulator, range_keys: list[str], ranges: dict[str, NDArray[int64 | float64]], data: dict[list[int64 | float64]]):
    if len(range_keys) == 0:
        for key, val in simulator.SteadyState().items():
            data[key].append(val[0])
        return
    attribute = range_keys.pop(0)

    path = simulator.pulse if hasattr(simulator.pulse, attribute) else simulator.system
    for val in ranges[attribute]:
        setattr(path, attribute, val)
        ManyRuns(simulator, deepcopy(range_keys), ranges, data)


if __name__ == '__main__':
    if len(argv) > 2:
        error = f"""Running command with the wrong number of arguments.
        Expecting: `{argv[0]} [path/to/config.yaml]`
        Received: `{' '.join(argv)}`
        """
        raise SyntaxError(error)
    if len(argv) == 2:
        with open(argv[1], 'r') as file:
            config = safe_load(file)
            configPath = Path(argv[1]).resolve()
    else:
        from brainhack.config import default
        config = default
        configPath = Path(__file__) / 'configs' / 'default.yaml'

    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')

    Path(config['run']['outputDir']).mkdir(parents=True, exist_ok=True)
    if 'handlers' in config['log'].keys():
        for handler in config['log']['handlers']:
            if 'filename' in config['log']['handlers'][handler].keys():
                tmp = Path(config['log']['handlers'][handler]['filename'])
                tmp.parent.mkdir(parents=True, exist_ok=True)
                config['log']['handlers'][handler]['filename'] = tmp.parent / f'{timestamp}_{tmp.stem}{tmp.suffix}'

    rootLogger = getLogger()

    if 'log' in config.keys():
        dictConfig(config['log'])
        rootLogger.debug(f'Logging configuration successful! Configuration file found at <{configPath}>.')
    else:
        rootLogger.addHandler(StreamHandler())
        rootLogger.setLevel(INFO)

    if 'run' not in config.keys():
        error = f'Missing `run` category from configuration file <{configPath}>.'
        rootLogger.critical(error)
        raise ValueError(error)

    set_printoptions(precision=maxsize)
    for key, value in SingleRun(**config['run']).items():
        rootLogger.info(f'{key}: {value.tolist()}')

# Note:
# This current (incomplete) version has implemented logic for 1 free pool and 1 bound pool only
# There needs to be a generalization of the construction of the operators in system.py and simulator.py
# A utility function could be designed such that given a steady state vector and a readout matrix, signal value signal computed at each readout even
# The general nomenclature (variable, function, class, and file names) is open to changes
# Parameter names in the SingleRun function of run.py should match exactly the names of the parameters in the config files for SingleRun(**config) to work as intended
# The choice of using json (comments not possible within the file) or yaml (comments possible within the file) config files is left open, my personal favorite is yaml,
# new python projects tend to favor .toml configuration files...
# TODO:
# 1. Corrector - Find a way to deep copy the full simulator object and subobjects
# 2. Generic - Apply NDarray.setflags(write=False) where necessary
# 3. Generic - Write tests
# 4. Notebook - Detail how-tos

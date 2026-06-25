"""
ihmt/run.py
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

from logging import getLogger, NullHandler, StreamHandler, INFO
from logging.config import dictConfig
from datetime import datetime
from sys import maxsize
from typing import Any
from scipy.io import savemat
from numpy import set_printoptions, array, ndarray
from numpy.typing import NDArray
from yaml import safe_load
from sys import argv
from pathlib import Path
from copy import deepcopy

from ihmt.meta import Signal
from ihmt.pulse import Tukey
from ihmt.sequence import Sequence
from ihmt.system import System
from ihmt.simulator import Simulator

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug("`run` module loaded successfully")


def SingleRun(
    M0a: float,
    T1f: float,
    T2f: float,
    R: float,
    M0b: float,
    T1b: float,
    T1D: float,
    T2b: float,
    poolBound_lineshapeAsymmetry: float,
    pw: float,
    dt: float,
    es: float,
    tr: float,
    turbo: int,
    N_dummyADC: int,
    np: int,
    nb: int,
    btr: float,
    btrlast: float,
    fa_sat: float,
    fa_rage: float,
    FLAG_Signal: str,
    N_altern: int,
    r_tukey: float,
    outputDir: str,
    filePrefix: str,
    export: bool,
    offset: float,
    output_fullVector: bool,
    export_read: bool,
    *args: Any,
    **kwargs: Any,
) -> dict[str, ndarray]:
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
    poolBound_lineshapeAsymmetry: float
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
    FLAG_Signal : str
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
    dict[str, ndarray]
        _description_

    Raises
    ------
    RuntimeError
        _description_
    """
    logger.debug(locals())

    signal = Signal.from_str(FLAG_Signal)

    pulse = Tukey(
        duration=pw,
        shape=r_tukey,
        flipAngle=fa_sat,
        offset=offset,
    )
    sequence = Sequence(
        signal=signal,
        pulse=pulse,
        N_pulsePerOffset=N_altern,
        N_pulse=np,
        N_burst=nb,
        N_totalADC=turbo,
        N_dummyADC=N_dummyADC,
        dt_interPulse=dt,
        TR_burst=btr,
        dt_lastBurst=btrlast,
        es=es,
        tr=tr,
        readout_flipAngle=fa_rage,
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
        poolBound_T1D=T1D,
        poolBound_lineshapeAsymmetry=poolBound_lineshapeAsymmetry,
    )

    simulator = Simulator(
        system=system,
        sequence=sequence,
        output_vectorSlice=slice(None) if output_fullVector else slice(1),
        export_readMatrix=export_read,
        output_fullVector=output_fullVector,
    )

    arrays: dict[str, ndarray] = simulator.SteadyState()

    if export:
        Path(outputDir).resolve().mkdir(parents=True, exist_ok=True)
        savemat(
            Path(outputDir).resolve() / (filePrefix + "simulation.mat"),
            arrays,
            do_compression=True,
        )

    return arrays


def GridRuns(
    simulator: Simulator,
    range_keys: list[str],
    ranges: dict[str, ndarray],
    safe: bool = False,
) -> dict[str, ndarray]:
    def _runs(range_keys):
        if len(range_keys) == 0:
            for key, val in simulator.SteadyState().items():
                data[key].append(val)  # type: ignore
            return
        attribute = range_keys.pop(0)

        if hasattr(simulator, attribute):
            path = simulator
        elif hasattr(simulator.system, attribute):
            path = simulator.system
        elif hasattr(simulator.pulse, attribute):
            path = simulator.pulse
        elif hasattr(simulator.sequence, attribute):
            path = simulator.sequence
        else:
            raise AttributeError(
                f"Attribute could not be found in the simulator, its pulse, system, or sequence. Received `{attribute}`."
            )

        for val in ranges[attribute]:
            setattr(path, attribute, val)
            _runs(deepcopy(range_keys))

    if not safe:
        simulator = simulator.copy()

    data: dict[str, list] = {key: [] for key in Signal.keys() | {"readout"}}  # type: ignore
    _runs(range_keys.copy())

    data: dict[str, ndarray] = {key: array(val) for key, val in data.items() if val}

    # Get (shape of ranges, shape of output vector)
    shape = list(len(ranges[key]) for key in range_keys)
    for key in data.keys():
        data[key] = data[key].reshape(shape + list(data[key].shape[1:]))
        if key != "readout":
            data[key] = data[key].transpose((-1, *range(len(shape))))

    [value.setflags(write=False) for value in data.values()]

    return data


def SampledRuns(
    simulator: Simulator,
    samplers: dict[str, ndarray],
    grids: dict[str, ndarray],
    safe: bool = False,
) -> dict[str, ndarray]:
    raise NotImplementedError


if __name__ == "__main__":
    if len(argv) > 2:
        error = f"""Running command with the wrong number of arguments.
        Expecting: `{argv[0]} [path/to/config.yaml]`
        Received: `{' '.join(argv)}`
        """
        raise SyntaxError(error)
    if len(argv) == 2:
        with open(argv[1], "r") as file:
            config = safe_load(file)
            configPath = Path(argv[1]).resolve()
    else:
        from ihmt.config import default

        config = default
        configPath = Path(__file__) / "configs" / "default.yaml"

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    Path(config["run"]["outputDir"]).mkdir(parents=True, exist_ok=True)
    if "handlers" in config["log"].keys():
        for handler in config["log"]["handlers"]:
            if "filename" in config["log"]["handlers"][handler].keys():
                tmp = Path(config["log"]["handlers"][handler]["filename"])
                tmp.parent.mkdir(parents=True, exist_ok=True)
                config["log"]["handlers"][handler]["filename"] = (
                    tmp.parent / f"{timestamp}_{tmp.stem}{tmp.suffix}"
                )

    rootLogger = getLogger()

    if "log" in config.keys():
        dictConfig(config["log"])
        rootLogger.debug(
            f"Logging configuration successful! Configuration file found at <{configPath}>."
        )
    else:
        rootLogger.addHandler(StreamHandler())
        rootLogger.setLevel(INFO)

    if "run" not in config.keys():
        error = f"Missing `run` category from configuration file <{configPath}>."
        rootLogger.critical(error)
        raise ValueError(error)

    set_printoptions(precision=maxsize)
    for key, value in SingleRun(**config["run"]).items():
        rootLogger.info(f"{key}: {value.tolist()}")

from .pulses import Tukey
from .sequence import Sequence, Modulation
from .system import System
from .simulator import Simulate

from typing import Any
from scipy.io import savemat  # type: ignore
from numpy import float64
from numpy.typing import NDArray
from yaml import safe_load
from sys import argv


def Main(B1rel: float, M0a: float, T1f: float, T2f: float, R: float, M0b: float, T1b: float, T1D: float, T2b: float, pw: float, dt: float, es: float, tr: float, turbo: int, np: int, nb: int, btr: float, btrlast: float, fa_sat: float, fa_rage: float, FLAG_Sine_Modulation: str, N_altern: int, r_tukey: float, outPrefix: str, export: bool, offset: float, *args: Any, **kwargs: Any) -> tuple[NDArray[float64], ...]:
    """_summary_

    Parameters
    ----------
    B1rel : float
        _description_
    T1f : float
        _description [s]_
    T2f : float
        _description [s]_
    R : float
        _description [per s]_
    M0b : float
        _description_
    T1b : float
        _description [s]_
    T1D : float
        _description [s]_
    T2b : float
        _description [s]_
    pw : float
        _description [s]_
    dt : float
        _description [s]_
    es : float
        _description [s]_
    tr : float
        _description [s]_
    turbo : int
        _description_
    np : int
        _description_
    nb : int
        _description_
    btr : float
        _description [s]_
    btrlast : float
        _description [s]_
    fa_sat : float
        _description [°]_
    fa_rage : float
        _description [°]_
    FLAG_Sine_Modulation : str
        _description_
    N_altern : int
        _description_
    r_tukey : float
        _description_
    outPrefix : str
        _description_
    export : bool
        _description_

    Returns
    -------
    tuple[ndarray[float]]
        _description_

    Raises
    ------
    RuntimeError
        _description_
    """

    if FLAG_Sine_Modulation.upper() == "CM":
        modulation = Modulation.CM
    elif FLAG_Sine_Modulation.upper() == "ALT":
        modulation = Modulation.ALT
    elif FLAG_Sine_Modulation.upper() == "BP":
        modulation = Modulation.BP
    else:
        raise RuntimeError("Incorrect `FLAG_Sine_Modulation` variable. Must be any one of `CM`, `ALT`, or `BP`.")

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
        ES=es,
        TR=tr,
        readout_flipAngle=fa_rage
    )
    system = System(
        M0a=M0a,
        M0b=M0b,
        T1f=T1f,
        T1b=T1b,
        T1D=T1D,
        T2f=T2f,
        T2b=T2b,
        R=R
    )

    system.RFabsorption_Matrix(sequence.pulse)
    arrays: tuple[NDArray[float64], ...] = Simulate(system, sequence)

    if export:
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

        savemat(outPrefix + 'simulation.mat', outDict, do_compression=True)

    return arrays


if __name__ == '__main__':
    if len(argv) != 2:
        raise RuntimeError(
            f"""
            Running command with the wrong number of arguments.
            Expecting: `{argv[0]} path/to/config.yaml`
            Received: `{' '.join(argv)}`
            """
        )
    with open(argv[1], 'r') as file:
        config = safe_load(file)

    for output in Main(**config):
        print(output)

# Note:
# This current (incomplete) version has implemented logic for 1 free pool and 1 bound pool only
# There needs to be a generalization of the construction of the operators in system.py and simulator.py
# The Simulate function in simulator.py also does not include logic to return signal values on a readout basis
# The general nomenclature (variable, function, class, and file names) is open to changes
# Parameter names in the Main function of main.py should match exactly the names of the parameters in the config files for Main(**config) to work as intended
# The choice of using json (comments not possible within the file) or yaml (comments possible within the file) config files is left open, my personal favorite is yaml

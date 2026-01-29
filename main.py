# To Do

from pulses import Tukey
from sequence import Sequence, Modulation
from system import System
from simulator import Simulate
from scipy.io import savemat
from numpy import ndarray
from json import load
# or
from yaml import safe_load


def Main(B1rel: float, T1f: float, T2f: float, R: float, M0b: float, T1b: float, T1D: float, T2b: float, pw: float, dt: float, es: float, tr: float, turbo: int, np: int, nb: int, btr: float, btrlast: float, fa_sat: float, fa_rage: float, FLAG_Sine_Modulation: str, N_altern: int, r_tukey: float, outPrefix: str, export: bool, *args, **kwargs) -> tuple[ndarray[float]]:
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
    
    pulse = Tukey(...)
    sequence = Sequence(modulation, pulse, ...)
    system = System(...)
    
    MT0, *ihMTs = Simulate(system, sequence)

    if export:
        # savemat(...)
        ...

    return MT0, *ihMTs


if __name__ == '__main__':
    with open('path/to/file.json', 'r') as file:
        config = load(file)
    # or
    with open('path/to/file.yaml', 'r') as file:
        config = safe_load(file)

    Main(**config)

# Note:
# This current (incomplete) version has implemented logic for 1 free pool and 1 bound pool only
# There needs to be a generalization of the construction of the operators in system.py and simulator.py
# The Simulate function in simulator.py also does not include logic to return signal values on a readout basis
# The general nomenclature (variable, function, class, and file names) is open to changes
# Parameter names in the Main function of main.py should match exaxctly the names of the parameters in the config files for Main(**config) to work as intended
# The choice of using json (comments not possible within the file) or yaml (comments possible within the file) config files is left open, my personal favorite is yaml

from logging import getLogger, NullHandler
from numpy import linspace, array, meshgrid
from numpy.typing import NDArray, float, int
from scipy.interpolate import PchipInterpolator, LinearNDInterpolator, RegularGridInterpolator
from copy import deepcopy

from brainhack.simulator import Simulator

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug('`corrector` module loaded successfully')


class Corrector():
    _ranges: dict[str, NDArray[int | float]]
    _simulator: Simulator

    _simulated: dict[str, NDArray[int | float]]
    _nominals: dict[str, float]
    _interpolants: dict[str, PchipInterpolator]

    _correctable = ('MT0', 'MTs', 'MTd_CM', 'MTd_ALT', 'ihMT_CM', 'ihMT_ALT', 'BP', 'BP', 'MTsR', 'MTdR_CM', 'MTdR_ALT', 'ihMTR_CM', 'ihMTR_ALT', 'BPR')

    @staticmethod
    def simple(simulator: Simulator) -> Corrector:
        return Corrector({'flipAngle': linspace(.1, 1.5, 36)}, simulator)

    def __init__(self, simulator: Simulator, ranges: dict[str, NDArray[int | float]]):
        self.simulator = simulator
        self.ranges = ranges

    def apply(self, data: dict[str, NDArray[int | float]], clean: bool):
        shape = None
        for _, dat in data.items():
            if shape is None:
                shape = dat.shape
                continue

            if dat.shape != shape:
                raise ValueError('Arrays in data dictionary need to match shape.')

        parameters = array([data[key].flatten() for key in self.ranges.keys()]).T

        corrected: dict[str, NDArray[int | float]] = dict()
        for correctable in self.correctable:
            if correctable in data.keys():
                if correctable not in self.interpolants.keys():
                    self._create_interpolants(correctable)

                corrector = self.nominals[correctable] / self.interpolants[correctable](parameters)
                corrected[correctable] = data[correctable] * corrector.reshape(shape)

        if clean:
            del self.simulated
            del self.nominals

        return corrected

    def _create_interpolants(self, correctable: str):
        if correctable not in self._correctable:
            raise ValueError("Unknown correctable key.")

        if 'R' in correctable:
            if 'invMT0' not in self.simulated.keys():
                self.simulated['invMT0'] = 1. / self.simulated['MT0']

        if correctable not in self.simulated.keys():
            self._composite(correctable)

        # interpolator = PchipInterpolator if len(self.ranges) == 1 else LinearNDInterpolator
        interpolator = PchipInterpolator if len(self.ranges) == 1 else RegularGridInterpolator
        self.interpolants[correctable] = interpolator(tuple(val for val in self.ranges.values()), self.simulated[correctable])

    def _run(self, simulator: Simulator, ranges: list[str], values: dict[list[int | float]]):
        if len(ranges) == 0:
            for key, val in simulator.SteadyState().items():
                values[key].append(val)
            return

        attribute = ranges.pop(0)

        for val in self.ranges[attribute]:
            if attribute in simulator.pulse.__dict__.keys():
                setattr(simulator.pulse, attribute, val)
            else:
                setattr(simulator.system, attribute, val)

            self._run(simulator, ranges, values)

    def _composite(self, composite: str):
        match composite:
            case 'ihMT_CM':
                data = 2 * (self.simulated['MTs'] - self.simulated['MTd_CM'])
            case 'ihMT_ALT':
                data = 2 * (self.simulated['MTs'] - self.simulated['MTd_ALT'])

            case 'BP':
                data = 2 * (self.simulated['MTd_ALT'] - self.simulated['MTd_CM'])

            case 'MTsR':
                data = 100 - 100 * self.simulated['MTs'] * self.simulated['invMT0']

            case 'MTdR_CM':
                data = 100 - 100 * self.simulated['MTd_CM'] * self.simulated['invMT0']
            case 'MTdR_ALT':
                data = 100 - 100 * self.simulated['MTd_ALT'] * self.simulated['invMT0']

            case 'ihMTR_CM':
                data = 100 * self.simulated['ihMT_CM'] * self.simulated['invMT0']
            case 'ihMTR_ALT':
                data = 100 * self.simulated['ihMT_ALT'] * self.simulated['invMT0']

            case 'BPR':
                data = 100 * self.simulated['BP'] * self.simulated['invMT0']

        self.simulated[composite] = data

    #####
    # BELOW: property getters and setters
    #####
    @property
    def nominals(self) -> dict[str, float]:
        if not hasattr(self, '_nominals'):
            self.nominals = self.simulator.SteadyState()
        return self._nominals

    @nominals.setter
    def nominals(self, val: dict[str, float]):
        self._nominals = val

    @property
    def simulated(self) -> dict[str, NDArray[int | float]]:
        if not hasattr(self, '_simulated'):
            shape = tuple(len(range) for range in self.ranges.values())
            data = {key: [] for key in self.nominals.keys()}
            self._run(deepcopy(self.simulator), list(self.ranges.keys()), data)
            self.simulated = {key: dat.reshape(shape) for key, dat in data.items()}
        return self._simulated

    @simulated.setter
    def simulated(self, val: dict[str, NDArray[int | float]]):
        self._simulated = val

from logging import getLogger, NullHandler
from numpy import linspace, array, float64, int64
from numpy.typing import NDArray
from scipy.interpolate import PchipInterpolator, RegularGridInterpolator
from copy import deepcopy

from brainhack.meta import _Event
from brainhack.simulator import Simulator

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug('`corrector` module loaded successfully')


class Corrector(_Event):
    _ranges: dict[str, NDArray[int64 | float64]]
    _simulator: Simulator

    _simulated: dict[str, NDArray[int64 | float64]]
    _nominals: dict[str, float]
    _interpolants: dict[str, PchipInterpolator | RegularGridInterpolator]

    _correctable = ('MT0', 'MTs', 'MTd_CM', 'MTd_ALT', 'ihMT_CM', 'ihMT_ALT', 'BP', 'BP', 'MTsR', 'MTdR_CM', 'MTdR_ALT', 'ihMTR_CM', 'ihMTR_ALT', 'BPR')

    _classAttributes: tuple[str] = ('ranges', 'simulator', 'simulated', 'nominals', 'interpolants', 'correctable')

    @staticmethod
    def simple(simulator: Simulator) -> Corrector:
        return Corrector(simulator=simulator, ranges={'flipAngle': linspace(.1, 1.5, 36)})

    def __init__(self, simulator: Simulator, ranges: dict[str, NDArray[int64 | float64]]):
        self.simulator = simulator
        self.ranges = ranges

        self.onChange('ranges', [self._reset_computed_attributes(['simulated', 'nominals', 'interpolants'])])
        self.onChange('simulator', [self._reset_computed_attributes(['simulated', 'nominals', 'interpolants'])])

    def apply(self, data: dict[str, NDArray[int64 | float64]], clean: bool):
        shape = None
        for _, dat in data.items():
            if shape is None:
                shape = dat.shape
                continue

            if dat.shape != shape:
                raise ValueError('Arrays in data dictionary need to match shape.')

        parameters = array([data[key].flatten() for key in self.ranges.keys()]).T

        corrected: dict[str, NDArray[int64 | float64]] = dict()
        for correctable in self.correctable:
            if correctable in data.keys():
                if correctable not in self.interpolants.keys():
                    self._create_interpolants(correctable)

                corrector = self.nominals[correctable] / self.interpolants[correctable](parameters)
                corrected[correctable] = data[correctable] * corrector.reshape(shape)

        if clean:
            del self._simulated
            del self._nominals

        return corrected

    def _create_interpolants(self, correctable: str):
        if correctable not in self.correctable:
            raise ValueError("Unknown correctable key.")

        if 'R' in correctable:
            if 'invMT0' not in self.simulated.keys():
                self._simulated['invMT0'] = 1. / self.simulated['MT0']

        if correctable not in self.simulated.keys():
            self._composite(correctable)

        # interpolator = PchipInterpolator if len(self.ranges) == 1 else LinearNDInterpolator
        interpolator = PchipInterpolator if len(self.ranges) == 1 else RegularGridInterpolator
        self._interpolants[correctable] = interpolator(tuple(val for val in self.ranges.values()), self.simulated[correctable])

    def _run(self, simulator: Simulator, ranges: list[str], values: dict[list[int64 | float64]]):
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

        self._simulated[composite] = data

    #####
    # BELOW: property getters and setters
    #####
    @property
    def ranges(self) -> dict[str, NDArray[int64 | float64]]:
        return self._ranges

    @ranges.setter
    def ranges(self, val: dict[str, NDArray[int64 | float64]]):
        self._ranges = val
        self._changed('ranges')

    @property
    def simulator(self) -> Simulator:
        return self._simulator

    @simulator.setter
    def simulator(self, val: Simulator):
        self._simulator = val
        self._changed('simulator')

    @property  # immutable for the user, so only getter is defined
    def simulated(self) -> dict[str, NDArray[int64 | float64]]:
        if not hasattr(self, '_simulated'):
            shape = tuple(len(range) for range in self.ranges.values())
            data = {key: [] for key in self._nominals.keys()}
            self._run(deepcopy(self.simulator), list(self.ranges.keys()), data)
            self._simulated = {key: dat.reshape(shape) for key, dat in data.items()}
        return self._simulated

    @property  # immutable for the user, so only getter is defined
    def nominals(self) -> dict[str, float]:
        if not hasattr(self, '_nominals'):
            self._nominals = self.simulator.SteadyState()
        return self._nominals

    @property  # immutable for the user, so only getter is defined
    def interpolants(self) -> dict[str, PchipInterpolator | RegularGridInterpolator]:
        return self._interpolants

    @property  # immutable for the user, so only getter is defined
    def correctable(self) -> tuple[str]:
        return self._correctable

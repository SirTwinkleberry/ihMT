from logging import getLogger, NullHandler
from numpy import linspace, array, float64, int64, meshgrid, vstack, nan, ones
from numpy.typing import NDArray
from functools import partial
from scipy.interpolate import PchipInterpolator, RegularGridInterpolator
from copy import deepcopy

from brainhack.meta import _Event, Signal, CompositeDictionary
from brainhack.simulator import Simulator
from brainhack.run import GridRuns

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug('`corrector` module loaded successfully')


class Corrector(_Event):
    _ranges: dict[str, NDArray[int64 | float64]]
    _simulator: Simulator

    _simulated: dict[str, NDArray[int64 | float64]]
    _nominals: dict[str, float]
    _interpolants: dict[str, PchipInterpolator | RegularGridInterpolator]

    _classAttributes: tuple[str] = ('ranges', 'simulator', 'simulated', 'mesh', 'nominals', 'interpolants')

    @staticmethod
    def Simple(simulator: Simulator) -> Corrector:
        return Corrector(simulator=simulator, ranges={'flipAngle': simulator.pulse.flipAngle * linspace(.1, 1.5, 141)})

    def __init__(self, simulator: Simulator, ranges: dict[str, NDArray[int64 | float64]]):
        self.simulator = simulator
        self.ranges = ranges

        self.onChange('ranges', [lambda: self._reset_computed_attributes(['simulated', 'nominals', 'interpolants'])])
        self.onChange('simulator', [lambda: self._reset_computed_attributes(['simulated', 'nominals', 'interpolants'])])

    def copy(self) -> Corrector:
        return Corrector(self.simulator.copy(), deepcopy(self.ranges))

    def apply(self, parameter_maps: dict[str, NDArray[int64 | float64]], data_maps: dict[Signal, NDArray[int64 | float64]]) -> CompositeDictionary[Signal, NDArray[int64 | float64]]:
        for key in self.ranges.keys():
            if key not in parameter_maps.keys():
                raise KeyError(f"Missing key `{key}` in parameter map dictionary.")

        for key in data_maps.keys():
            if type(key) != Signal:
                raise TypeError(f"Accepting `{type(Signal)}` flags only. Received `{type(key)}`.")

        shape = None
        for key, val in (parameter_maps | data_maps).items():
            if shape is None:
                shape = val.shape
                continue
            if val.shape != shape:
                raise ValueError(f'Arrays need to match shape. Received shape `{val.shape}` for array `{key}` while trying to match shape `{shape}`.')

        mask = ones(shape).astype(bool) if 'mask' not in parameter_maps.keys() else parameter_maps['mask'].astype(bool)

        parameters = vstack([parameter_maps[key][mask].flatten() for key in self.ranges.keys()]).T

        corrected: dict[Signal, NDArray[int64 | float64]] = dict()
        for key, value in data_maps.items():
            corrected[key] = value.copy().astype(float64)
            corrected[key][mask] *= (self.nominals[key] / self.interpolants[key](parameters)).squeeze()

        return CompositeDictionary(corrected)

    #####
    # BELOW: property getters and setters
    #####
    @property
    def ranges(self) -> dict[str, NDArray[int64 | float64]]:
        return self._ranges

    @ranges.setter
    def ranges(self, val: dict[str, NDArray[int64 | float64]]):
        self._ranges = deepcopy(val)
        for val in self._ranges.values():
            val.setflags(write=False)
        self._changed('ranges')

    @property
    def simulator(self) -> Simulator:
        return self._simulator

    @simulator.setter
    def simulator(self, val: Simulator):
        self._simulator = val
        self._changed('simulator')

    @property  # immutable for the user, so only getter is defined
    def simulated(self) -> CompositeDictionary[str, NDArray[int64 | float64]]:
        if not hasattr(self, '_simulated'):
            sim = self.simulator.copy()
            sim.output_vectorSlice = slice(1)
            sim.export_readMatrix = False
            self._simulated = CompositeDictionary(GridRuns(sim, list(self.ranges.keys()), self.ranges, safe=True)).squeeze()
        return self._simulated

    @property  # immutable for the user, so only getter is defined
    def mesh(self) -> dict[str, NDArray[int64 | float64]]:
        if not hasattr(self, '_mesh'):
            tmp = dict()
            mesh = meshgrid(*list(self.ranges.values()), indexing='ij', sparse=True)
            for key, val in zip(self.ranges.keys(), mesh):
                tmp[key] = val
                tmp[key].setflags(write=False)
            self._mesh = tmp
        return self._mesh

    @property  # immutable for the user, so only getter is defined
    def nominals(self) -> CompositeDictionary[str, float]:
        if not hasattr(self, '_nominals'):
            tmp = self.simulator.output_vectorSlice
            self.simulator.output_vectorSlice = slice(1)
            self._nominals = CompositeDictionary(self.simulator.SteadyState())
            self.simulator.output_vectorSlice = tmp
        return self._nominals

    @property  # immutable for the user, so only getter is defined
    def interpolants(self):
        if not hasattr(self, '_interpolants'):
            self._interpolants = InterpolantDictionary(
                interpolator=PchipInterpolator if len(self.ranges) == 1 else partial(RegularGridInterpolator, bounds_error=False, fill_value=nan),
                ranges=self.ranges,
                simulated=self.simulated
            )
        return self._interpolants


class InterpolantDictionary(dict):
    def __init__(self, interpolator: PchipInterpolator | RegularGridInterpolator, ranges: dict[str, NDArray[int64 | float64]], simulated: CompositeDictionary[str, NDArray[int64 | float64]]):
        self._interpolator = interpolator
        self._ranges = tuple(ranges.values())
        self._simulated = simulated

        if len(self._ranges) == 1:
            self._ranges = tuple(self._ranges[0].tolist())

        super().__init__()

    def __getitem__(self, subscript: Signal):
        if type(subscript) != Signal:
            raise TypeError(f"Accepting `{type(Signal)}` flags only. Received `{type(subscript)}`.")

        if subscript == Signal.ALL:
            for subscript in Signal.values():
                if (subscript != Signal.ALL) and (subscript not in self.keys()):
                    try:
                        dict.__setitem__(self, subscript, self._interpolator(self._ranges, self._simulated[subscript]))
                    except Exception as _:
                        pass
            return self

        elif (subscript not in self.keys()) and (subscript in Signal.values()):
            dict.__setitem__(self, subscript, self._interpolator(self._ranges, self._simulated[subscript]))

        return dict.__getitem__(self, subscript)

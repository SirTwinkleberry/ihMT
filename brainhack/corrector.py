from logging import getLogger, NullHandler
from numpy import linspace, array, float64, int64, meshgrid, vstack
from numpy.typing import NDArray
from scipy.interpolate import PchipInterpolator, RegularGridInterpolator
from enum import Flag, auto

from brainhack.meta import _Event
from brainhack.simulator import Simulator
from brainhack.run import ManyRuns

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug('`corrector` module loaded successfully')


class Correctable(Flag):
    MT0       = auto()
    MTs       = auto()
    MTd_CM    = auto()
    MTd_ALT   = auto()
    ihMT_CM   = MTs      | MTd_CM
    ihMT_ALT  = MTs      | MTd_ALT
    BP        = MTd_CM   | MTd_ALT
    MTsR      = MTs      | MT0
    MTdR_CM   = MTd_CM   | MT0
    MTdR_ALT  = MTd_ALT  | MT0
    ihMTR_CM  = ihMT_CM  | MT0
    ihMTR_ALT = ihMT_ALT | MT0
    BPR       = BP       | MT0

    @classmethod
    def values(cls):
        return cls._member_map_.values()

    @classmethod
    def keys(cls):
        return cls._member_map_.keys()

    @classmethod
    def items(cls):
        return cls._member_map_.items()


class Corrector(_Event):
    _ranges: dict[str, NDArray[int64 | float64]]
    _simulator: Simulator

    _simulated: dict[str, NDArray[int64 | float64]]
    _nominals: dict[str, float]
    _interpolants: dict[str, PchipInterpolator | RegularGridInterpolator]

    _classAttributes: tuple[str] = ('ranges', 'simulator', 'simulated', 'mesh', 'nominals', 'interpolants')

    @staticmethod
    def Simple(simulator: Simulator) -> Corrector:
        return Corrector(simulator=simulator, ranges={'poolFree_T1': array([1., 1.5, 2.]), 'flipAngle': simulator.pulse.flipAngle * linspace(.1, 1.5, 141)})

    def __init__(self, simulator: Simulator, ranges: dict[str, NDArray[int64 | float64]]):
        self.simulator = simulator
        self.ranges = ranges

        self.onChange('ranges', [lambda: self._reset_computed_attributes(['simulated', 'nominals', 'interpolants'])])
        self.onChange('simulator', [lambda: self._reset_computed_attributes(['simulated', 'nominals', 'interpolants'])])

    def apply(self, parameter_maps: dict[str, NDArray[int64 | float64]], data_maps: dict[Correctable, NDArray[int64 | float64]]):
        for key in self.ranges.keys():
            if key not in parameter_maps.keys():
                raise KeyError(f"Missing key `{key}` in parameter map dictionary.")

        for key in data_maps.keys():
            if type(key) != Correctable:
                raise TypeError(f"Accepting `{type(Correctable)}` flags only. Received `{type(key)}`.")

        shape = None
        for key, val in (parameter_maps | data_maps).items():
            if shape is None:
                shape = val.shape
                continue
            if val.shape != shape:
                raise ValueError(f'Arrays need to match shape. Received shape `{val.shape}` for array `{key}` while trying to match shape `{shape}`.')

        parameters = vstack([parameter_maps[key].flatten() for key in self.ranges.keys()]).T

        corrected: dict[Correctable, NDArray[int64 | float64]] = dict()
        for key, value in data_maps.items():
            corrector = self.nominals[key] / self.interpolants[key](parameters)
            corrected[key] = value * corrector.reshape(shape)
            corrected[key].setflags(write=False)

        return corrected

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
    def simulated(self) -> CompositeDictionary[str, NDArray[int64 | float64]]:
        if not hasattr(self, '_simulated'):
            tmp = dict()
            shape = tuple(len(range) for range in self.ranges.values())
            data = {key: [] for key in Correctable.keys()}
            # TODO: Find a way to deep copy the full simulator object and subobjects
            # and send that to _simulate instead to avoid changing object attributes
            self.simulator.export_readMatrix = False
            ManyRuns(self.simulator, list(self.ranges.keys()), self.ranges, data)

            for key, dat in data.items():
                if len(dat) > 0:
                    tmp[key] = array(dat).reshape(shape)
                    tmp[key].setflags(write=False)
            self._simulated = CompositeDictionary(tmp)

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
            self._nominals = CompositeDictionary(self.simulator.SteadyState())
        return self._nominals

    @property  # immutable for the user, so only getter is defined
    def interpolants(self):
        if not hasattr(self, '_interpolants'):
            self._interpolants = InterpolantDictionary(
                interpolator=PchipInterpolator if len(self.ranges) == 1 else RegularGridInterpolator,
                ranges=self.ranges,
                simulated=self.simulated
            )
        return self._interpolants


class InterpolantDictionary(dict):
    def __init__(self, interpolator: PchipInterpolator | RegularGridInterpolator, ranges: dict[str, NDArray[int64 | float64]], simulated: dict[str, NDArray[int64 | float64]]):
        self._interpolator = interpolator
        self._ranges = tuple(ranges.values())
        self._simulated = simulated
        super().__init__()

    def __getitem__(self, subscript: Correctable):
        if type(subscript) != Correctable:
            raise TypeError(f"Accepting `{type(Correctable)}` flags only. Received `{type(subscript)}`.")
        name = subscript.name
        if (name not in self.keys()) and (name in Correctable.keys()):
            dict.__setitem__(self, name, self._interpolator(self._ranges, self._simulated[subscript]))
        return dict.__getitem__(self, name)


class CompositeDictionary(dict):
    def __getitem__(self, subscript: Correctable):
        if type(subscript) != Correctable:
            raise TypeError(f"Accepting `{type(Correctable)}` flags only. Received `{type(subscript)}`.")
        subscript = subscript.name
        if (subscript not in self.keys()) and (subscript in Correctable.keys()):
            self._composite(subscript)
        return dict.__getitem__(self, subscript)

    def _composite(self, composite: str):
        match composite:
            case Correctable.ihMT_CM.name:
                data = 2 * (self[Correctable.MTs] - self[Correctable.MTd_CM])
            case Correctable.ihMT_ALT.name:
                data = 2 * (self[Correctable.MTs] - self[Correctable.MTd_ALT])
            case Correctable.BP.name:
                data = 2 * (self[Correctable.MTd_ALT] - self[Correctable.MTd_CM])
            case Correctable.MTsR.name:
                data = 100 - 100 * self[Correctable.MTs] * self._invMT0
            case Correctable.MTdR_CM.name:
                data = 100 - 100 * self[Correctable.MTd_CM] * self._invMT0
            case Correctable.MTdR_ALT.name:
                data = 100 - 100 * self[Correctable.MTd_ALT] * self._invMT0
            case Correctable.ihMTR_CM.name:
                data = 100 * self[Correctable.ihMT_CM] * self._invMT0
            case Correctable.ihMTR_ALT.name:
                data = 100 * self[Correctable.ihMT_ALT] * self._invMT0
            case Correctable.BPR.name:
                data = 100 * self[Correctable.BP] * self._invMT0
        data.setflags(write=False)
        dict.__setitem__(self, composite, data)

    #####
    # BELOW: property getters and setters
    #####
    @property
    def _invMT0(self):
        if not hasattr(self, '__invMT0'):
            self.__invMT0 = 1. / self[Correctable.MT0]
            self.__invMT0.setflags(write=False)
        return self.__invMT0

from logging import getLogger, NullHandler
from numpy import float64
from numpy.typing import NDArray

from brainhack.meta import _Event, Signal
from brainhack.simulator import Simulator

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug('`trajector` module loaded successfully')


class Trajector(_Event):
    def __init__(self, trajectory: tuple[tuple[int]], simulator: Simulator, *args, **kwargs):
        ...

    @staticmethod
    def CartesianSpiral_CentricOut(simulator: Simulator, *args, **kwargs) -> Trajector:
        trajectory = None
        return Trajector(trajectory, simulator)

    @staticmethod
    def CentricOut_Linear(simulator: Simulator, *args, **kwargs) -> Trajector:
        trajectory = None
        return Trajector(trajectory, simulator)

    @staticmethod
    def Linear_Linear(simulator: Simulator, *args, **kwargs) -> Trajector:
        trajectory = None
        return Trajector(trajectory, simulator)

    def VectorialPointSpreadFunction(self) -> NDArray[float64]:
        # D?
        ...

    def PointSpreadFunction(self) -> NDArray[float64]:
        # 2D or 3D
        ...

    def LineSpreadFunction(self) -> NDArray[float64]:
        # 1D
        ...
    
    def EdgeSpreadFunction(self) -> NDArray[float64]:
        # 1D
        ...

    def VectorialOpticalTransferFunction(self) -> NDArray[float64]:
        # D?
        ...

    def OpticalTransferFunction(self) -> NDArray[float64]:
        # 2D or 3D
        ...

    def ModulationTransferFunction(self) -> NDArray[float64]:
        # 2D or 3D
        ...

    def PhaseTransferFunction(self) -> NDArray[float64]:
        # 2D or 3D
        ...


class TrajectorDictionary(dict):
    ...

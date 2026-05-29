from logging import getLogger, NullHandler
from numpy import float64, equal, mod
from numpy.linalg import matrix_power, inv
from numpy.typing import NDArray

from brainhack.meta import _Event, CompositeDictionary
from brainhack.simulator import Simulator

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug('`trajector` module loaded successfully')


class Trajector(_Event):
    def __init__(self, trajectory: tuple[tuple[int]], simulator: Simulator, *args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def CartesianSpiral_CentricOut(simulator: Simulator, *args, **kwargs) -> Trajector:
        raise NotImplementedError
        trajectory = None
        return Trajector(trajectory, simulator)

    @staticmethod
    def CentricOut_Linear(simulator: Simulator, *args, **kwargs) -> Trajector:
        raise NotImplementedError
        trajectory = None
        return Trajector(trajectory, simulator)

    @staticmethod
    def Linear_Linear(simulator: Simulator, *args, **kwargs) -> Trajector:
        raise NotImplementedError
        trajectory = None
        return Trajector(trajectory, simulator)

    @staticmethod
    def check_integer_only(array: NDArray[float64]):
        return equal(mod(array, 1), 0).all()

    @staticmethod
    def readouts(simulator: Simulator, stable: bool = True, *args, **kwargs) -> CompositeDictionary[str, NDArray[float64]]:
        tmp = simulator.export_readMatrix, simulator.output_vectorSlice
        simulator.export_readMatrix, simulator.output_vectorSlice = True, slice(None)

        data = simulator.SteadyState()

        simulator.export_readMatrix, simulator.output_vectorSlice = tmp

        if stable:
            readouts = {key: [] for key in data.keys() if key != 'readout'}
            for adc in range(simulator.sequence.N_adc):
                readoutMatrix = matrix_power(data['readout'], adc - simulator.sequence.N_dummyADC)
                for key in readouts.keys():
                    readouts[key].append(readoutMatrix @ data[key])
        else:
            invReadout = inv(data['readout'])
            readouts = {key: [matrix_power(invReadout, simulator.sequence.N_dummyADC) @ data[key]] for key in data if key != 'readout'}

            for key in readouts.keys():
                for _ in range(1, simulator.sequence.N_adc):
                    readouts[key].append(data['readout'] @ readouts[key][-1])

        return CompositeDictionary(readouts).T


    def VectorialPointSpreadFunction(self) -> NDArray[float64]:
        # D?
        raise NotImplementedError

    def PointSpreadFunction(self) -> NDArray[float64]:
        # 2D or 3D
        raise NotImplementedError

    def LineSpreadFunction(self) -> NDArray[float64]:
        # 1D
        raise NotImplementedError
    
    def EdgeSpreadFunction(self) -> NDArray[float64]:
        # 1D
        raise NotImplementedError

    def VectorialOpticalTransferFunction(self) -> NDArray[float64]:
        # D?
        raise NotImplementedError

    def OpticalTransferFunction(self) -> NDArray[float64]:
        # 2D or 3D
        raise NotImplementedError

    def ModulationTransferFunction(self) -> NDArray[float64]:
        # 2D or 3D
        raise NotImplementedError

    def PhaseTransferFunction(self) -> NDArray[float64]:
        # 2D or 3D
        raise NotImplementedError


class TrajectorDictionary(dict):
    ...
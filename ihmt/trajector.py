from logging import getLogger, NullHandler
from numpy import ndarray, number, equal, mod
from numpy.linalg import matrix_power, inv

from ihmt.meta import _Event, CompositeDictionary
from ihmt.simulator import Simulator

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug("`trajector` module loaded successfully")


class Trajector(_Event):
    def __init__(
        self,
        N_readoutDirection: int,
        N_inPlaneDirection: tuple[int, int],
        trajectory: tuple[tuple[int, int, int]],
        simulator: Simulator,
        *args,
        **kwargs
    ):
        raise NotImplementedError

    @staticmethod
    def CartesianSpiral_CentricOut(simulator: Simulator, *args, **kwargs) -> Trajector:
        raise NotImplementedError
        trajectory = None
        return Trajector(trajectory, simulator)

    @staticmethod
    def CentricOut_Linear(simulator: Simulator, *args, **kwargs) -> Trajector:
        raise NotImplementedError
        N = simulator.sequence.N_adc - simulator.sequence.N_dummyADC
        dims = (N, N)
        trajectory = None
        return Trajector(trajectory, simulator)

    @staticmethod
    def Linear_Linear(simulator: Simulator, *args, **kwargs) -> Trajector:
        raise NotImplementedError
        trajectory = None
        return Trajector(trajectory, simulator)

    @staticmethod
    def readouts(
        simulator: Simulator, stable: bool = True, *args, **kwargs
    ) -> CompositeDictionary[str, ndarray[number]]:
        tmp = simulator.export_readMatrix, simulator.output_vectorSlice
        simulator.export_readMatrix, simulator.output_vectorSlice = True, slice(None)

        data = simulator.SteadyState()

        simulator.export_readMatrix, simulator.output_vectorSlice = tmp

        if stable:
            readouts = {key: [] for key in data.keys() if key != "readout"}
            for adc in range(simulator.sequence.N_adc):
                readoutMatrix = matrix_power(
                    data["readout"], adc - simulator.sequence.N_dummyADC
                )
                for key in readouts.keys():
                    readouts[key].append(readoutMatrix @ data[key])
        else:
            invReadout = inv(data["readout"])
            readouts = {
                key: [
                    matrix_power(invReadout, simulator.sequence.N_dummyADC) @ data[key]
                ]
                for key in data
                if key != "readout"
            }

            for key in readouts.keys():
                for _ in range(1, simulator.sequence.N_adc):
                    readouts[key].append(data["readout"] @ readouts[key][-1])

        return CompositeDictionary(readouts).T

    @staticmethod
    def _check_integer_only(array: ndarray[number]):
        return equal(mod(array, 1), 0).all()

    def VectorialPointSpreadFunction(self) -> ndarray[number]:
        # D?
        raise NotImplementedError

    def PointSpreadFunction(self) -> ndarray[number]:
        # 2D or 3D
        raise NotImplementedError

    def LineSpreadFunction(self) -> ndarray[number]:
        # 1D
        raise NotImplementedError

    def EdgeSpreadFunction(self) -> ndarray[number]:
        # 1D
        raise NotImplementedError

    def VectorialOpticalTransferFunction(self) -> ndarray[number]:
        # D?
        raise NotImplementedError

    def OpticalTransferFunction(self) -> ndarray[number]:
        # 2D or 3D
        raise NotImplementedError

    def ModulationTransferFunction(self) -> ndarray[number]:
        # 2D or 3D
        raise NotImplementedError

    def PhaseTransferFunction(self) -> ndarray[number]:
        # 2D or 3D
        raise NotImplementedError


class TrajectorDictionary(dict): ...

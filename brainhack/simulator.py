from logging import getLogger, NullHandler
from numpy import zeros, eye, vstack, hstack, round, deg2rad, cos, ndarray, number, complex128, iscomplex
from numpy.linalg import matrix_power, eig
from scipy.linalg import expm
from typing import Any

from brainhack.meta import _Event, Signal, check_value_is_valid
from brainhack.pulse import Pulse
from brainhack.system import System
from brainhack.sequence import Sequence

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug('`simulator` module loaded successfully')


class Simulator(_Event):
    _output_vectorSlice: bool
    _export_readMatrix: bool
    _system: System
    _sequence: Sequence

    _pulse: Pulse

    _classAttributes: tuple[str] = ('output_vectorSlice', 'export_readMatrix', 'system', 'sequence', 'pulse')

    def __init__(self, system: System, sequence: Sequence, output_vectorSlice: slice, export_readMatrix: bool, *args: Any, **kwargs: Any):
        """_summary_

        Parameters
        ----------
        system : System
            _description_
        sequence : Sequence
            _description_
        export_readMatrix : bool
            _description_

        Raises
        ------
        ValueError
            _description_
        """
        self.system = system
        self.sequence = sequence
        self.output_vectorSlice = output_vectorSlice
        self.export_readMatrix = export_readMatrix
        self.pulse = sequence.pulse

        self.onChange('pulse', [lambda: setattr(self.sequence, 'pulse', self.pulse), lambda: setattr(self.system, 'pulse', self.pulse), self._check_pulse_match])

        self._check_pulse_match()

    def copy(self) -> Simulator:
        system = self.system.copy()
        sequence = self.sequence.copy()
        sequence.pulse = system.pulse
        return Simulator(system, sequence, self.output_vectorSlice, self.export_readMatrix)

    def _check_pulse_match(self):
        if self.sequence.pulse != self.system.pulse:
            error = f'Mismatched RF pulse between sequence and system. Received {self.sequence.pulse} (sequence) and {self.system.pulse} (system).'
            logger.critical(error)
            raise ValueError(error)

    def SteadyState(self) -> dict[str, ndarray[number]]:
        """_summary_

        Array in steady-state is the eigenvector associated to eigenvalue=1 (last column here)
        Indeed: eigenequation is <Av = lv> with l the eigenvalue of A associated to the eigenvector v
        Meanwhile: steady state equation is <Av = v>. We can identify both equations by setting l = 1.
        For l = 1, v_1 is the steady state eigenvector of A, i.e., the steady state magnetization of A.
        Eigenvectors are always defined up to a scaling factor. The last element of v_1 is also necessarily non-zero.
        The last element of v_1, present because of the homogeneization of matrix A, is not associated to a physical quantity.
        We choose the normalization where this last element of v_1 is unity, so we rescale v_1 by the scalar <1. / v_1[-1]>

        Returns
        -------
        tuple[ndarray[number], ...]
            _description_
        """
        self._check_pulse_match()

        sys = self.system
        seq = self.sequence
        output: dict[str, ndarray[number]] = dict()

        mat_REX = vstack([hstack([sys.relaxation, sys.magnetization_recovery]), zeros((1, 1 + sys.N_poolFree + 2 * sys.N_poolBound))])

        # Readout & Recovery
        evol_relax_interReadRF: ndarray[number] = expm(mat_REX * seq.es)
        evol_relax_recovery: ndarray[number] = expm(mat_REX * seq.duration_recovery)
        evol_rf_readoutInstantAction = eye(1 + sys.N_poolFree + 2 * sys.N_poolBound)
        evol_rf_readoutInstantAction[0, 0] = cos(deg2rad(seq.readout_flipAngle))
        read: ndarray[number] = evol_relax_interReadRF @ evol_rf_readoutInstantAction
        evol_RAGE: ndarray[number] = evol_relax_recovery @ matrix_power(read, seq.N_adc - seq.N_dummyADC)
        evol_dummyRAGE: ndarray[number] = matrix_power(read, seq.N_dummyADC)

        if Signal.MT0 in seq.signal:
            evol_relax_fullPrep: ndarray[number] = expm(mat_REX * seq.duration_preparation)
        v_MT0 = eig(round(evol_dummyRAGE @ (evol_relax_fullPrep @ evol_RAGE), 16))[1][:, -1]
        if (v_MT0.dtype == complex128) and (not iscomplex(v_MT0).any()):
            v_MT0 = v_MT0.real
        output['MT0'] = v_MT0[self.output_vectorSlice] / v_MT0[-1]

        if (Signal.MTs in seq.signal) or (Signal.MTd_ALT in seq.signal) or (Signal.MTd_CM in seq.signal):
            evol_relax_interPulse: ndarray[number] = expm(mat_REX * (seq.dt_interPulse - seq.pulse.duration))
            evol_relax_TR_burst: ndarray[number] = expm(mat_REX * (seq.TR_burst - seq.N_pulse * seq.dt_interPulse))
            evol_relax_lastBurst: ndarray[number] = expm(mat_REX * (seq.dt_lastBurst - seq.N_pulse * seq.dt_interPulse))

            if (Signal.MTs in seq.signal) or (Signal.MTd_ALT in seq.signal):
                evol_rf_singleSat_Positive: ndarray[number] = expm(
                    vstack([
                        hstack( [ sys.poolBound_Rrf_singleSat_Positive + sys.poolFree_Rrf + sys.relaxation, sys.magnetization_recovery ] ),
                        zeros( (1, 1 + sys.N_poolFree + 2 * sys.N_poolBound) )
                    ]) * seq.pulse.duration
                )

                evol_rf_singleSat_Negative: ndarray[number] = expm(
                    vstack([
                        hstack( [ sys.poolBound_Rrf_singleSat_Negative + sys.poolFree_Rrf + sys.relaxation, sys.magnetization_recovery ] ),
                        zeros( (1, 1 + sys.N_poolFree + 2 * sys.N_poolBound) )
                    ]) * seq.pulse.duration
                )

                if Signal.MTs_Positive in seq.signal:
                    evol_MTsat_single: ndarray[number] = (evol_relax_lastBurst @ matrix_power(evol_relax_interPulse @ evol_rf_singleSat_Positive, seq.N_pulse)) \
                        @ matrix_power(evol_relax_TR_burst @ matrix_power(evol_relax_interPulse @ evol_rf_singleSat_Positive, seq.N_pulse), seq.N_burst - 1)
                    v_MTs_Positive = eig(round(evol_dummyRAGE @ (evol_MTsat_single @ evol_RAGE), 16))[1][:, -1]
                    if (v_MTs_Positive.dtype == complex128) and (not iscomplex(v_MTs_Positive).any()):
                        v_MTs_Positive = v_MTs_Positive.real
                    output['MTs_Positive'] = v_MTs_Positive[self.output_vectorSlice] / v_MTs_Positive[-1]

                if Signal.MTs_Negative in seq.signal:
                    if (sys.poolBound_lineshapeAsymmetry != 0).any():
                        evol_MTsat_single: ndarray[number] = (evol_relax_lastBurst @ matrix_power(evol_relax_interPulse @ evol_rf_singleSat_Negative, seq.N_pulse)) \
                            @ matrix_power(evol_relax_TR_burst @ matrix_power(evol_relax_interPulse @ evol_rf_singleSat_Negative, seq.N_pulse), seq.N_burst - 1)
                        v_MTs_Negative = eig(round(evol_dummyRAGE @ (evol_MTsat_single @ evol_RAGE), 16))[1][:, -1]
                        if (v_MTs_Negative.dtype == complex128) and (not iscomplex(v_MTs_Negative).any()):
                            v_MTs_Negative = v_MTs_Negative.real
                        output['MTs_Negative'] = v_MTs_Negative[self.output_vectorSlice] / v_MTs_Negative[-1]
                    else:
                        output['MTs_Negative'] = output['MTs_Positive']

                if Signal.MTd_ALT in seq.signal:
                    evol_MTsat_dual_ALT: ndarray[number] = evol_relax_lastBurst @ matrix_power(
                            matrix_power(evol_relax_interPulse @ evol_rf_singleSat_Negative, seq.N_pulsePerOffset)
                            @ matrix_power(evol_relax_interPulse @ evol_rf_singleSat_Positive, seq.N_pulsePerOffset),
                            int(.5 * seq.N_pulse / seq.N_pulsePerOffset)
                        ) \
                        @ matrix_power(evol_relax_TR_burst @ matrix_power(
                                matrix_power(evol_relax_interPulse @ evol_rf_singleSat_Negative, seq.N_pulsePerOffset)
                                @ matrix_power(evol_relax_interPulse @ evol_rf_singleSat_Positive, seq.N_pulsePerOffset),
                                int(.5 * seq.N_pulse / seq.N_pulsePerOffset)
                            ),
                            seq.N_burst - 1
                        )
                    v_MTd_ALT = eig(round(evol_dummyRAGE @ (evol_MTsat_dual_ALT @ evol_RAGE), 16))[1][:, -1]
                    if (v_MTd_ALT.dtype == complex128) and (not iscomplex(v_MTd_ALT).any()):
                        v_MTd_ALT = v_MTd_ALT.real
                    output['MTd_ALT'] = v_MTd_ALT[self.output_vectorSlice] / v_MTd_ALT[-1]

            if Signal.MTd_CM in seq.signal:
                evol_rf_dualSat_SM: ndarray[number] = expm(
                    vstack([
                        hstack( [ sys.poolBound_Rrf_dualSat + sys.poolFree_Rrf + sys.relaxation, sys.magnetization_recovery ] ),
                        zeros( (1, 1 + sys.N_poolFree + 2 * sys.N_poolBound) )
                    ]) * seq.pulse.duration
                )

                evol_MTsat_dual_CM: ndarray[number] = (evol_relax_lastBurst @ matrix_power(evol_relax_interPulse @ evol_rf_dualSat_SM, seq.N_pulse)) \
                    @ matrix_power(evol_relax_TR_burst @ matrix_power(evol_relax_interPulse @ evol_rf_dualSat_SM, seq.N_pulse), seq.N_burst - 1)
                v_MTd_CM = eig(round(evol_dummyRAGE @ (evol_MTsat_dual_CM @ evol_RAGE), 16))[1][:, -1]
                if (v_MTd_CM.dtype == complex128) and (not iscomplex(v_MTd_CM).any()):
                    v_MTd_CM = v_MTd_CM.real
                output['MTd_CM'] = v_MTd_CM[self.output_vectorSlice] / v_MTd_CM[-1]

        if self.export_readMatrix:
            output['readout'] = read

        [value.setflags(write=False) for value in output.values()]

        return output

    #####
    # BELOW: property getters and setters
    #####
    @property
    def output_vectorSlice(self) -> slice:
        return self._output_vectorSlice

    @output_vectorSlice.setter
    def output_vectorSlice(self, val: slice):
        check_value_is_valid(self, val, slice, None, 'output_vectorSlice')
        self._output_vectorSlice = val
        self._changed('output_vectorSlice')

    @property
    def export_readMatrix(self) -> bool:
        return self._export_readMatrix

    @export_readMatrix.setter
    def export_readMatrix(self, val: bool):
        check_value_is_valid(self, val, bool, None, 'export_readMatrix')
        self._export_readMatrix = val
        self._changed('export_readMatrix')

    @property
    def system(self) -> System:
        return self._system

    @system.setter
    def system(self, val: System):
        self._system = val
        self._changed('system')

    @property
    def sequence(self) -> Sequence:
        return self._sequence

    @sequence.setter
    def sequence(self, val: Sequence):
        self._sequence = val
        self._changed('sequence')

    @property
    def pulse(self) -> Pulse:
        return self._pulse

    @pulse.setter
    def pulse(self, val: Pulse):
        self._pulse = val
        self._changed('pulse')

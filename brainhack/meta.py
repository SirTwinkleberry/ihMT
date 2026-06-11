from logging import getLogger, NullHandler
from operator import le, lt, gt, ge, eq, add, sub, mul, truediv
from typing import Any
from collections.abc import Callable
from numpy import pi, cos, sin, tan, array, array_equal, nan_to_num, errstate, round, ndarray, number, atleast_1d, atleast_2d
from enum import Flag, auto
from copy import deepcopy

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug('`meta` module loaded successfully')

_2pi = 2. * pi
_inv_2pi = 1. / _2pi
_rad2deg = 180. / pi
_deg2rad = pi / 180.


class Signal(Flag):
    MT0           = auto()
    MTs_Positive  = auto()
    MTs_Negative  = auto()
    MTd_CM        = auto()
    MTd_ALT       = auto()
    MTs           = MTs_Positive | MTs_Negative
    ihMT_CM       = MTs          | MTd_CM
    ihMT_ALT      = MTs          | MTd_ALT
    BP            = MTd_CM       | MTd_ALT
    MTsR_Positive = MTs_Positive | MT0
    MTsR_Negative = MTs_Negative | MT0
    MTsR          = MTs          | MT0
    MTdR_CM       = MTd_CM       | MT0
    MTdR_ALT      = MTd_ALT      | MT0
    ihMTR_CM      = ihMT_CM      | MT0
    ihMTR_ALT     = ihMT_ALT     | MT0
    BPR           = BP           | MT0
    ALL           = BP   | MTs   | MT0

    @classmethod
    def values(cls):
        return cls._member_map_.values()

    @classmethod
    def keys(cls):
        return cls._member_map_.keys()

    @classmethod
    def items(cls):
        return cls._member_map_.items()

    @classmethod
    def from_str(cls, key: str):
        match key.upper():
            case 'MT0':
                return cls.MT0
            case 'MTS_POSITIVE':
                return cls.MTs_Positive
            case 'MTS_NEGATIVE':
                return cls.MTs_Negative
            case 'MTS':
                return cls.MTs
            case 'MTD_CM':
                return cls.MTd_CM
            case 'MTD_ALT':
                return cls.MTd_ALT
            case 'IHMT_CM':
                return cls.ihMT_CM
            case 'IHMT_ALT':
                return cls.ihMT_ALT
            case 'BP':
                return cls.BP
            case 'MTSR_POSITIVE':
                return cls.MTsR_Positive
            case 'MTSR_NEGATIVE':
                return cls.MTsR_Negative
            case 'MTSR':
                return cls.MTsR
            case 'MTDR_CM':
                return cls.MTdR_CM
            case 'MTDR_ALT':
                return cls.MTdR_ALT
            case 'IHMTR_CM':
                return cls.ihMTR_CM
            case 'IHMTR_ALT':
                return cls.ihMTR_ALT
            case 'BPR':
                return cls.BPR
            case 'ALL':
                return cls.ALL
            case _:
                error = f"Incorrect signal flag. Must be any one or combinations of {tuple(cls.keys())}. Received `{repr(key)}`."
                logger.critical(error)
                raise ValueError(error)


def check_value_is_valid(obj: Any, val_to_check: Any, type_to_check: type, operators: None | list[tuple[Callable, int | float]], attribute_name: str) -> bool:
    error = None
    match type_to_check.__name__:
        case slice.__name__ | Frequency.__name__ | AngularFrequency.__name__ | Duration.__name__ | Angle.__name__:
            if type(val_to_check) is not type_to_check:
                error = f'`{attribute_name}` of `{obj.__class__.__name__}` must be of type `{type_to_check}`. Received: `{repr(val_to_check)}` of type `{type(val_to_check)}`.'
        case ScalarOrVector.__name__:
            try:
                tmp = atleast_1d(val_to_check)
                if len(tmp.shape) != 1:
                    raise ValueError('')
            except Exception as _:
                error = f'`{attribute_name}` of `{obj.__class__.__name__}` must be safely castable to `{type_to_check}`. Received: `{repr(val_to_check)}`.'
        case ScalarOrMatrix.__name__:
            try:
                tmp = atleast_2d(val_to_check)
                if len(tmp.shape) != 2:
                    raise ValueError('')
            except Exception as _:
                error = f'`{attribute_name}` of `{obj.__class__.__name__}` must be safely castable to `{type_to_check}`. Received: `{repr(val_to_check)}`.'
        case _:
            if type_to_check(val_to_check) != val_to_check:
                error = f'`{attribute_name}` of `{obj.__class__.__name__}` must be safely castable to `{type_to_check}`. Received: `{repr(val_to_check)}`.'

    if error is not None:
        logger.critical(error)
        raise ValueError(error)

    if operators is not None:
        for operator, bound in operators:
            match operator.__name__:
                case le.__name__:
                    boundStr = f'less or equal to {bound}'
                case lt.__name__:
                    boundStr = f'less than {bound}'
                case ge.__name__:
                    boundStr = f'greater or equal to {bound}'
                case gt.__name__:
                    boundStr = f'greater than {bound}'
                case eq.__name__:
                    boundStr = f'equal to {bound}'
                case _:
                    error = f"Operator {operator} was not implemented."
                    logger.critical(error)
                    raise NotImplementedError(error)

            if operator(atleast_1d(val_to_check), bound).any():
                error = f'`{attribute_name}` of `{obj.__class__.__name__}` cannot be {boundStr}. Received: `{repr(val_to_check)}`.'
                logger.critical(error)
                raise ValueError(error)

    return True

class CompositeDictionary(dict):
    def __init__(self, mapping: Any, /):
        data = dict()
        for key, value in dict(mapping).items():
            if key == 'readout':
                continue
            value = array(value)
            if value.size:
                value.setflags(write=False)
                if not isinstance(key, Signal):
                    key = Signal.from_str(key)
                data[key] = value
        super().__init__(data)

    def __getitem__(self, subscript: Signal) -> CompositeDictionary | ndarray[number]:
        if type(subscript) != Signal:
            raise TypeError(f"Accepting `{type(Signal)}` flags only. Received `{type(subscript)}`.")

        if subscript == Signal.ALL:
            with errstate(divide='ignore', invalid='ignore'):
                for subscript in Signal.values():
                    if (subscript != Signal.ALL) and (subscript not in self.keys()):
                        try:
                            self._composite(subscript)
                        except Exception as _:
                            pass
            return self

        elif (subscript not in self.keys()) and (subscript in Signal.values()):
            self._composite(subscript)

        return dict.__getitem__(self, subscript)

    def _composite(self, composite: str):
        match composite:
            case Signal.MTs:
                data = .5 * (self[Signal.MTs_Positive] + self[Signal.MTs_Negative])
            case Signal.ihMT_CM:
                data = 2 * (self[Signal.MTs] - self[Signal.MTd_CM])
            case Signal.ihMT_ALT:
                data = 2 * (self[Signal.MTs] - self[Signal.MTd_ALT])
            case Signal.BP:
                data = 2 * (self[Signal.MTd_ALT] - self[Signal.MTd_CM])
            case Signal.MTsR_Positive:
                data = 100 - 100 * self[Signal.MTs_Positive] * self._invMT0
            case Signal.MTsR_Negative:
                data = 100 - 100 * self[Signal.MTs_Negative] * self._invMT0
            case Signal.MTsR:
                data = 100 - 100 * self[Signal.MTs] * self._invMT0
            case Signal.MTdR_CM:
                data = 100 - 100 * self[Signal.MTd_CM] * self._invMT0
            case Signal.MTdR_ALT:
                data = 100 - 100 * self[Signal.MTd_ALT] * self._invMT0
            case Signal.ihMTR_CM:
                data = 100 * self[Signal.ihMT_CM] * self._invMT0
            case Signal.ihMTR_ALT:
                data = 100 * self[Signal.ihMT_ALT] * self._invMT0
            case Signal.BPR:
                data = 100 * self[Signal.BP] * self._invMT0
            case _:
                error = f"Incorrect signal flag. Must be any one or combinations of {tuple(Signal.keys())}. Received `{repr(composite)}`."
                logger.critical(error)
                raise ValueError(error)

        data.setflags(write=False)
        dict.__setitem__(self, composite, data)

    def _math(self, other: Any, operator: Callable) -> CompositeDictionary:
        if not isinstance(other, CompositeDictionary):
            try:
                other = CompositeDictionary(other)
            except Exception as _:
                pass
        with errstate(invalid='ignore', divide='ignore'):
            if isinstance(other, CompositeDictionary):
                return CompositeDictionary({key: operator(self[key], other[key]) for key in self.keys() | other.keys()})
            else:
                return CompositeDictionary({key: operator(self[key], other) for key in self.keys()})

    def __eq__(self, other):
        if not isinstance(other, CompositeDictionary):
            try:
                other = CompositeDictionary(other)
            except Exception as _:
                return False
        for key in self.keys() | other.keys():
            key = Signal.from_str(key)
            if not array_equal(self[key], other[key]):
                return False
        return True

    def __add__(self, other) -> CompositeDictionary:
        return self._math(other, add)

    def __sub__(self, other) -> CompositeDictionary:
        return self._math(other, sub)

    def __mul__(self, other) -> CompositeDictionary:
        return self._math(other, mul)

    def __truediv__(self, other) -> CompositeDictionary:
        return self._math(other, truediv)

    def squeeze(self):
        return CompositeDictionary({key: val.squeeze() for key, val in self.items()})

    def __str__(self, round_decimals: None | int = None, nan_to_0: bool = False):
        string = f'Shape: {self[list(self.keys())[0]].shape}\n'
        for key in self.keys():
            val = deepcopy(self[key])
            if round_decimals is not None:
                val = round(val, round_decimals)
            if nan_to_0:
                val = nan_to_num(val, nan=0, posinf=0, neginf=0)
            string += f'{str(key.name).rjust(13)} = {val.tolist()}\n'
        return string

    #####
    # BELOW: property getters and setters
    #####
    @property
    def T(self) -> CompositeDictionary:
        return CompositeDictionary({key: val.T for key, val in self.items()})

    @property
    def _invMT0(self) -> ndarray[number]:
        if not hasattr(self, '__invMT0'):
            self.__invMT0 = 1. / self[Signal.MT0]
            self.__invMT0.setflags(write=False)
        return self.__invMT0


class _Event():
    _classAttributes: tuple[str]

    _onChanges: dict[str, list[Callable]]

    def onChange(self, attribute: str, callbacks: list[Callable]):
        if attribute not in self._get_classAttributes():
            error = f"`{attribute}` is not an acceptable attribute name for callbacks. Possible attributes for `{self.__class__.__name__}`:\n{'`' + '`, `'.join(self._get_classAttributes()) + '`'}."
            logger.critical(error)
            raise ValueError(error)

        onChanges = self._get_onChanges()
        if attribute not in onChanges.keys():
            logger.debug(f'Initializing `{attribute}` callback list to `_onChanges` for `{self.__class__.__name__}`.')
            onChanges[attribute] = []
        onChanges[attribute].extend(callbacks)
        logger.debug(f'Extended `{attribute}` callback list with `{callbacks}` for `{self.__class__.__name__}`.')

    def _changed(self, attribute: str):
        onChanges = self._get_onChanges()
        if attribute in onChanges.keys():
            logger.debug(f'Parsing callbacks for `{attribute}` in `{self.__class__.__name__}`.')
            for callback in onChanges[attribute]:
                try:
                    callback()
                except Exception as e:
                    logger.error(e)
                    raise e

    def _reset_computed_attributes(self, attributelist: list[str]):
        for attribute in attributelist:
            if hasattr(self, f'_{attribute}'): # prefix `_` to avoid calling getter method
                try:
                    delattr(self, f'{attribute}')  # No prefix `_` to ensure calling deleter method
                    logger.debug(f'Called for deletion of `{attribute}`. `_{attribute}` was deleted in `{self.__class__.__name__}`.')
                except AttributeError as e:
                    logger.debug(f'Called for deletion of `{attribute}` but exception ensued:')
                    logger.debug(e)
            else:
                logger.debug(f'Called for deletion of `{attribute}` but `_{attribute}` was not found in `{self.__class__.__name__}`.')

    def _get_onChanges(self) -> dict[str, list[Callable]]:
        if not hasattr(self, '_onChanges'):
            self._onChanges = dict()
            logger.debug(f'Initializing `_onChanges` for `{self.__class__.__name__}`.')
        return self._onChanges

    def __str__(self, shift=0) -> str:
        string = f'=====> {self.__class__.__name__.upper()} <=====\n'
        length = len(string)
        for attribute in self._get_classAttributes():
            value = getattr(self, attribute)
            string += f'{" " * shift}{attribute} = '
            if type(value) == type(array(0)):
                tmp = str(value.tolist()).split(', [')
                for i in range(1, len(tmp)):
                    tmp[i] = ' ' * (shift + 1 + len(attribute) + 3) + '[' + tmp[i]
                string += ',\n'.join(tmp)
            elif attribute in ['pulse', 'sequence', 'system', 'corrector', 'trajector', 'simulator']:
                string += value.__str__(shift + len(attribute) + 3)
            else:
                string += str(value)
            string += '\n'
        return string + ' ' * shift + '=' * length

    @classmethod
    def _get_classAttributes(cls) -> tuple[str, ...]:
        if not hasattr(cls, '_classAttributes'):
            return tuple()
        return cls._classAttributes


# Immutable class
class _BaseUnit(float):
    _unit = None

    def __new__(cls, value: int | float, label: None | str = None, *args, **kwargs) -> _BaseUnit:
        instance = super().__new__(cls, value)
        instance.__label = label
        return instance

    @classmethod
    def from_micro(cls, value: int | float, label: str | None = None):
        return cls(1e-6 * value, label)

    @classmethod
    def from_milli(cls, value: int | float, label: str | None = None):
        return cls(1e-3 * value, label)

    @classmethod
    def from_kilo(cls, value: int | float, label: str | None = None):
        return cls(1e3 * value, label)

    @classmethod
    def from_mega(cls, value: int | float, label: str | None = None):
        return cls(1e6 * value, label)

    def __str__(self):
        return f'{float(self)} {self._unit}'

    def __repr__(self):
        return f'{self.__class__.__name__}(value={float.__repr__(self)}, unit={self._unit}, label={repr(self.label)})'

    #####
    # BELOW: property getters
    #####
    @property
    def label(self) -> str:
        return self.__label


class Frequency(_BaseUnit):
    _unit = 'Hz'

    @staticmethod
    def from_hertz(value: int | float, label: str | None = None) -> Frequency:
        return Frequency(value, label)

    @property
    def angular(self) -> AngularFrequency:
        if not hasattr(self, '__angular'):
            self.__angular = AngularFrequency(_2pi * self, self.label)
        return self.__angular

    @property
    def period(self) -> Duration:
        if not hasattr(self, '__period'):
            self.__period = Duration(1. / self, self.label)
            self.__period.__rate = self
        return self.__period


class AngularFrequency(_BaseUnit):
    _unit = 'rad • Hz'

    @staticmethod
    def from_radHertz(value: int | float, label: str | None = None) -> AngularFrequency:
        return AngularFrequency(value, label)

    @property
    def frequency(self) -> Frequency:
        if not hasattr(self, '__frequency'):
            self.__frequency = Frequency(_inv_2pi * self, self.label)
            self.__frequency.__angular = self
        return self.__frequency

    @property
    def period(self) -> Duration:
        return self.frequency.period


class Duration(_BaseUnit):
    _unit = 's'

    @staticmethod
    def from_seconds(value: int | float, label: str | None = None) -> Duration:
        return Duration(value, label)

    @property
    def rate(self) -> Frequency:
        if not hasattr(self, '__rate'):
            self.__rate = Frequency(1. / self, self.label)
            self.__rate.__period = self
        return self.__rate

    @property
    def angular_rate(self) -> AngularFrequency:
        return self.rate.angular


class Angle(_BaseUnit):
    _unit = '°'

    @staticmethod
    def from_radians(value: int | float, label: str | None = None) -> Angle:
        return Angle(_rad2deg * value, label)

    @staticmethod
    def from_degrees(value: int | float, label: str | None = None) -> Angle:
        return Angle(value, label)

    @property
    def rad(self) -> float:
        if not hasattr(self, '__radians'):
            self.__radians = _deg2rad * self
        return self.__radians

    @property
    def deg(self) -> float:
        return float(self)

    @property
    def cos(self) -> float:
        if not hasattr(self, '__cos'):
            self.__cos = round(cos(self.rad), 15)
        return self.__cos

    @property
    def sin(self) -> float:
        if not hasattr(self, '__sin'):
            self.__sin = round(sin(self.rad), 15)
        return self.__sin

    @property
    def tan(self) -> float:
        if not hasattr(self, '__tan'):
            self.__tan = round(tan(self.rad), 15)
        return self.__tan

    @property
    def sec(self) -> float:
        if not hasattr(self, '__sec'):
            self.__sec = 1. / self.cos
        return self.__sec

    @property
    def csc(self) -> float:
        if not hasattr(self, '__csc'):
            self.__csc = 1. / self.sin
        return self.__csc

    @property
    def cot(self) -> float:
        if not hasattr(self, '__cot'):
            self.__cot = 1. / self.tan
        return self.__cot


type ScalarOrVector = number | ndarray[number]
type ScalarOrMatrix = number | ndarray[number]

from logging import getLogger, NullHandler
from operator import le, lt, gt, ge, eq, add, sub, mul, truediv 
from typing import Any
from collections.abc import Callable
from numpy import pi, cos, sin, tan, array, array_equal, errstate
from enum import Flag, auto

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


def check_value_is_valid(obj: Any, val_to_check: Any, type_to_check: type, operators: None | list[tuple[Callable, int | float]], attribute_name: str):
    error = None
    match type_to_check.__name__:
        case slice.__name__:
            if type(val_to_check) is not slice:
                error = f'`{attribute_name}` of `{obj}` must be of type {slice}. Received: `{repr(val_to_check)}` of type `{type(val_to_check)}`.'
        case _:
            if type_to_check(val_to_check) != val_to_check:
                error = f'`{attribute_name}` of `{obj}` must be safely castable to `{type_to_check}`. Received: `{repr(val_to_check)}`.'    

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

            if operator(val_to_check, bound):
                error = f'`{attribute_name}` of `{obj}` cannot be {boundStr}. Received: `{repr(val_to_check)}`.'
                logger.critical(error)
                raise ValueError(error)


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

    def __getitem__(self, subscript: Signal):
        if type(subscript) != Signal:
            raise TypeError(f"Accepting `{type(Signal)}` flags only. Received `{type(subscript)}`.")

        if subscript == Signal.ALL:
            with errstate(divide='ignore', invalid='ignore'):
                for subscript in Signal.values():
                    if subscript not in self.keys():
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

    #####
    # BELOW: property getters and setters
    #####
    @property
    def T(self) -> CompositeDictionary:
        return CompositeDictionary({key: val.T for key, val in self.items()})

    @property
    def _invMT0(self):
        if not hasattr(self, '__invMT0'):
            self.__invMT0 = 1. / self[Signal.MT0]
            self.__invMT0.setflags(write=False)
        return self.__invMT0


class _Event():
    _classAttributes: tuple[str]

    _onChanges: dict[str, list[Callable]]

    def onChange(self, attribute: str, callbacks: list[Callable]):
        if attribute not in self._get_classAttributes():
            error = f"`{attribute}` is not an acceptable attribute name for callbacks. Possible attributes for `{self}`:\n{'`' + '`, `'.join(self._get_classAttributes()) + '`'}."
            logger.critical(error)
            raise ValueError(error)

        onChanges = self._get_onChanges()
        if attribute not in onChanges.keys():
            logger.debug(f'Initializing `{attribute}` callback list to `_onChanges` for `{self}`.')
            onChanges[attribute] = []
        onChanges[attribute].extend(callbacks)
        logger.debug(f'Extended `{attribute}` callback list with `{callbacks}` for `{self}`.')

    def _changed(self, attribute: str):
        onChanges = self._get_onChanges()
        if attribute in onChanges.keys():
            logger.debug(f'Parsing callbacks for `{attribute}` in `{self}`.')
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
                    logger.debug(f'Called for deletion of `_{attribute}` in `{self}`.')
                except AttributeError as e:
                    logger.debug(f'Called for deletion of `{attribute}` but exception ensued:')
                    logger.debug(e)
            else:
                logger.debug(f'Called for deletion of `{attribute}` but `_{attribute}` was not found in `{self}`.')

    def _get_onChanges(self) -> dict[str, list[Callable]]:
        if not hasattr(self, '_onChanges'):
            self._onChanges = dict()
            logger.debug(f'Initializing `_onChanges` for `{self}`.')
        return self._onChanges

    @classmethod
    def _get_classAttributes(cls) -> tuple[str]:
        if not hasattr(cls, '_classAttributes'):
            return tuple()
        return cls._classAttributes


# Immutable class
class Angle():
    def __init__(self, label: str, value: int | float, is_radians: bool):
        check_value_is_valid(self, val_to_check=value, type_to_check=float, operators=None, attribute_name='Angle')

        self.__label = str(label)
        if is_radians:
            self.__radians = float(value)
            self.__degrees = _rad2deg * float(value)
        else:
            self.__degrees = float(value)
            self.__radians = _deg2rad * float(value)

    @staticmethod
    def from_radians(value: int | float, label: str | None = None) -> Angle:
        return Angle(label, value, is_radians=True)

    @staticmethod
    def from_degrees(value: int | float, label: str | None = None) -> Angle:
        return Angle(label, value, is_radians=False)

    def __eq__(self, other):
        return isinstance(other, Angle) and (self.degrees == other.degrees)

    def __str__(self):
        return f'{self.label if self.label is not None else "Angle"} = {self.degrees}°'

    def __repr__(self):
        return f'{self.__class__.__name__}({repr(self.label)}, {repr(self.degrees)}°)'

    #####
    # BELOW: property getters
    #####
    @property
    def label(self) -> str:
        return self.__label

    @property
    def degrees(self) -> float:
        return self.__degrees

    @property
    def radians(self) -> float:
        return self.__radians

    @property
    def cos(self):
        if not hasattr(self, '__cos'):
            self.__cos = cos(self.__radians)
        return self.__cos

    @property
    def sin(self):
        if not hasattr(self, '__sin'):
            self.__sin = sin(self.__radians)
        return self.__sin

    @property
    def tan(self):
        if not hasattr(self, '__tan'):
            self.__tan = tan(self.__radians)
        return self.__tan

    @property
    def sec(self):
        if not hasattr(self, '__sec'):
            self.__sec = 1. / self.cos
        return self.__sec

    @property
    def csc(self):
        if not hasattr(self, '__csc'):
            self.__csc = 1. / self.sin
        return self.__csc

    @property
    def cot(self):
        if not hasattr(self, '__cot'):
            self.__cot = 1. / self.tan
        return self.__cot


# Immutable class
class Frequency():
    def __init__(self, label: str, value: int | float, is_angular: bool):
        check_value_is_valid(self, val_to_check=value, type_to_check=float, operators=None, attribute_name='Frequency')

        self.__label = str(label)
        if is_angular:
            self.__angular = float(value)
            self.__linear = _inv_2pi * float(value)
        else:
            self.__linear = float(value)
            self.__angular = _2pi * float(value)

    @staticmethod
    def from_angular(value: int | float, label: str | None = None) -> Frequency:
        return Frequency(label, value, is_angular=True)

    @staticmethod
    def from_linear(value: int | float, label: str | None = None) -> Frequency:
        return Frequency(label, value, is_angular=False)

    def as_hertz(self):
        return self.linear

    def as_kilohertz(self):
        return 1e-3 * self.linear

    def as_megahertz(self):
        return 1e-6 * self.linear

    def as_angularHertz(self):
        return self.angular

    def as_angularKilohertz(self):
        return 1e-3 * self.angular

    def as_angularMegahertz(self):
        return 1e-6 * self.angular

    def __eq__(self, other):
        return isinstance(other, Frequency) and (self.linear == other.linear)

    def __str__(self):
        return f'{self.label if self.label is not None else "Frequency"} = {self.linear} Hz'

    def __repr__(self):
        return f'{self.__class__.__name__}({repr(self.label)}, {repr(self.linear)} Hz)'

    #####
    # BELOW: property getters
    #####
    @property
    def label(self) -> str:
        return self.__label

    @property
    def linear(self) -> float:
        return self.__linear

    @property
    def angular(self) -> float:
        return self.__angular

    @property
    def period(self) -> Duration:
        if not hasattr(self, '__period'):
            self.__period = Duration.from_seconds(1. / self.linear, self.label)
        return self.__period


# Immutable class
class Duration():
    def __init__(self, label: str, value: int | float):
        check_value_is_valid(self, val_to_check=value, type_to_check=float, operators=None, attribute_name='Duration')

        self.__label = str(label)
        self.__value = float(value)

    @staticmethod
    def from_microseconds(value: int | float, label: str | None = None) -> Duration:
        return Duration(label, 1e-6 * value)

    @staticmethod
    def from_miliseconds(value: int | float, label: str | None = None) -> Duration:
        return Duration(label, 1e-3 * value)

    @staticmethod
    def from_seconds(value: int | float, label: str | None = None) -> Duration:
        return Duration(label, value)

    def as_microseconds(self) -> float:
        return 1e6 * self.value

    def as_miliseconds(self) -> float:
        return 1e3 * self.value

    def as_seconds(self) -> float:
        return self.value

    def __eq__(self, other):
        return isinstance(other, Duration) and (self.value == other.value)

    def __str__(self):
        return f'{self.label if self.label is not None else "Duration"} = {self.value} s'

    def __repr__(self):
        return f'{self.__class__.__name__}({repr(self.label)}, {repr(self.value)} s)'

    #####
    # BELOW: property getters
    #####
    @property
    def label(self) -> str:
        return self.__label

    @property
    def value(self) -> float:
        return self.__value

    @property
    def rate(self) -> Frequency:
        if not hasattr(self, '__rate'):
            self.__rate = Frequency.from_linear(1. / self.linear, self.label)
        return self.__rate

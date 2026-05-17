from logging import getLogger, NullHandler
from operator import le, lt, gt, ge, eq
from typing import Any
from collections.abc import Callable

from numpy import pi, cos, sin, tan

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug('`meta` module loaded successfully')

_2pi = 2. * pi
_inv_2pi = 1. / _2pi
_rad2deg = 180. / pi
_deg2rad = pi / 180.


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
        return isinstance(self, Angle) and (self.degrees == other.degrees)

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

    def __eq__(self, other):
        return isinstance(self, Frequency) and (self.linear == other.linear)

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
    def period(self) -> float:
        if not hasattr(self, '__period'):
            self.__period = 1. / self.linear
        return self.__period

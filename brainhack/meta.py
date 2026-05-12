from logging import getLogger, NullHandler
from collections.abc import Callable

logger = getLogger(__name__)
logger.addHandler(NullHandler())
logger.debug('`meta` module loaded successfully')


class _Event():
    _classAttributes: tuple[str]

    _onChanges: dict[str, list[Callable]]

    def onChange(self, attribute: str, callbacks: list[Callable]):
        if attribute not in self._get_classAttributes():
            error = f"`{attribute}` is not an acceptable attribute name for callbacks. Possible attributes: {'`' + '`, `'.join(self._get_classAttributes()) + '`'}."
            logger.critical(error)
            raise ValueError(error)

        onChanges = self._get_onChanges()
        if attribute not in onChanges.keys():
            onChanges[attribute] = []
        onChanges[attribute].extend(callbacks)

    def _changed(self, attribute: str):
        onChanges = self._get_onChanges()
        if attribute in onChanges.keys():
            for callback in onChanges[attribute]:
                try:
                    callback()
                except Exception as e:
                    logger.error(e)

    def _resetComputedAttributes(self, attributelist: list[str]):
        for attribute in attributelist:
            if hasattr(self, f'_{attribute}'): # prefix `_` to avoid calling getter method
                delattr(self, f'{attribute}')  # No prefix `_` to ensure calling deleter method
                logger.debug(f'Called for deletion of `_{attribute}`.')
            else:
                logger.debug(f'Called for deletion of `_{attribute}` but attribute was missing.')

    #####
    # BELOW: property getters and setters
    #####
    def _get_onChanges(self) -> dict[str, list[Callable]]:
        if not hasattr(self, '_onChanges'):
            self._onChanges = dict()
        return self._onChanges

    @classmethod
    def _get_classAttributes(cls) -> tuple[str]:
        if not hasattr(cls, '_classAttributes'):
            return tuple()
        return cls._classAttributes

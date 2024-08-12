"""Basic function. It does nothing."""

import logging

import numpy as np

import lightberries.array_controller
from lightberries.array_transforms.base import ArrayTransform
from lightberries.exceptions import ControllerError, FunctionError, LightBerryError

LOGGER = logging.getLogger("lightBerries")


class ArrayFunctionNone(ArrayTransform):
    """Basic function. It does nothing."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        color_sequence: np.ndarray = None,
    ) -> None:
        """Do nothing.

        Args:
        ----
            controller: array controller instance
            color_sequence: optional; color sequence. Defaults to None.

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens

        """
        super().__init__(
            name=ArrayFunctionNone.__class__.__name__,
            controller=controller,
            color_sequence=color_sequence,
            state=state,
            kwargs=kwargs,
        )
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionNone.__name__)
        try:
            # create an object to put in the light data list so we don't just abort the run
            controller.privateLightFunctions.append(
                ArrayTransform(
                    self,
                    ArrayTransform.functionNone,
                    self.color_sequence,
                ),
            )
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerError from ex

    def _transform(self) -> None:
        """Do nothing.

        Args:
        ----
            nothing: tracking object

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens

        """
        try:  # pragma: no cover
            pass  # pragma: no cover
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except SystemExit:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise FunctionError from ex

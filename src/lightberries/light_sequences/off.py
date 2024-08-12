"""Creates array of RGB tuples that are all off."""

from __future__ import annotations

from typing import Any

from lightberries.array_patterns.base import ArrayPattern


class ArrayPatternOff(ArrayPattern):
    """Creates array of RGB tuples that are all off."""

    def __init__(self, led_count: int, name: str | None = None, **kwargs: dict[str, Any]) -> None:
        """Create array of RGB tuples that are all off.

        Args:
        ----
            name: the name of this pattern
            led_count: the number of pixels desired in the returned pixel array
            kwargs: args for patterns

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightPatternException: if something bad happens

        """
        if name is None:
            name = ArrayPatternOff.__name__
        super().__init__(name=name, led_count=led_count, kwargs=kwargs)
        try:
            if led_count > 0:
                self._sequence = np.array([PixelColors.OFF.array for i in range(int(led_count))])
            else:
                self._sequence = np.zeros((0, 3))
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise PatternError from ex

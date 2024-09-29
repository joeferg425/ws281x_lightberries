"""Color patterns and sequences."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from lightberries.pixel_sequence import PixelSequence

if TYPE_CHECKING:
    from lightberries.pixel import Pixel



class ArraySequence(PixelSequence):
    """A pattern of lights."""

    ALL_ARRAY_SEQUENCES: ClassVar[dict[str, type[ArraySequence]]] = {}

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        cls.ALL_ARRAY_SEQUENCES[cls.__name__.replace("Sequence", "")] = cls

    def __init__(
        self,
        led_count: int | None = None,
        pixel_array: list[Pixel] | None = None,
        name: str | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """Create a pattern of lights.

        Args:
        ----
            name: the name of this pattern
            led_count: the number of pixels desired in the returned pixel array
            kwargs: args for patterns

        """
        if name is None:
            name = ArraySequence.__name__
        super().__init__(
            led_count=led_count,
            pixel_array=pixel_array,
            name=name,
            **kwargs,
        )
